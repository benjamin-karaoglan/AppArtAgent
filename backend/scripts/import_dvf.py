#!/usr/bin/env python3
"""
Import the geolocalized DVF dataset into dvf_sales + dvf_sale_lots.

Strategy: Polars processing + in-memory BytesIO buffer + COPY FROM STDIN.

Usage:
    uv run import-dvf                        # Uses data/dvf/dvf.csv
    uv run import-dvf --csv /path/to/dvf.csv # Custom path
"""

import argparse
import gzip
import io
import os
import shutil
import sys
import time
import urllib.request
from pathlib import Path

import polars as pl
import psycopg2

# Schema overrides for CSV columns that polars may mistype
DVF_SCHEMA_OVERRIDES = {
    "id_mutation": pl.Utf8,
    "code_postal": pl.Utf8,
    "code_commune": pl.Utf8,
    "code_departement": pl.Utf8,
    "id_parcelle": pl.Utf8,
    "numero_disposition": pl.Utf8,
    "adresse_numero": pl.Utf8,  # Read as string, cast to int later
    "adresse_code_voie": pl.Utf8,
    "ancien_code_commune": pl.Utf8,
    "ancien_id_parcelle": pl.Utf8,
    "lot1_numero": pl.Utf8,
    "lot2_numero": pl.Utf8,
    "lot3_numero": pl.Utf8,
    "lot4_numero": pl.Utf8,
    "lot5_numero": pl.Utf8,
    "lot1_surface_carrez": pl.Float64,
    "lot2_surface_carrez": pl.Float64,
    "lot3_surface_carrez": pl.Float64,
    "lot4_surface_carrez": pl.Float64,
    "lot5_surface_carrez": pl.Float64,
    "surface_reelle_bati": pl.Float64,
    "nombre_pieces_principales": pl.Float64,
    "surface_terrain": pl.Float64,
    "nombre_lots": pl.Float64,
    "valeur_fonciere": pl.Float64,
    "longitude": pl.Float64,
    "latitude": pl.Float64,
}

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "dvf" / "dvf.csv"

# Lot type classification
TYPE_LOCAL_MAP = {
    "1": "Maison",
    "2": "Appartement",
    "3": "Dépendance",
    "4": "Commercial",
}


def resolve_csv_path(cli_csv: str | None) -> Path:
    """Resolve CSV path from CLI arg, env var, or default."""
    if cli_csv:
        return Path(cli_csv)

    # Check for DVF_SOURCE_URL env var (Cloud Run Job)
    source_url = os.environ.get("DVF_SOURCE_URL")
    if source_url:
        if not source_url.startswith("https://"):
            print("ERROR: DVF_SOURCE_URL must use HTTPS")
            sys.exit(1)
        tmp_path = Path("/tmp/dvf.csv")
        if tmp_path.exists():
            print(f"Using cached {tmp_path}")
            return tmp_path

        archive_path = Path("/tmp/dvf.csv.gz")
        print(f"Downloading {source_url}")
        with (
            urllib.request.urlopen(source_url, timeout=120) as resp,  # noqa: S310
            open(archive_path, "wb") as out,
        ):
            shutil.copyfileobj(resp, out)
        size_mb = archive_path.stat().st_size / (1024 * 1024)
        print(f"Downloaded {size_mb:.1f} MB")

        print("Extracting...")
        with gzip.open(archive_path, "rb") as f_in, open(tmp_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        archive_path.unlink()
        out_mb = tmp_path.stat().st_size / (1024 * 1024)
        print(f"Extracted {out_mb:.1f} MB")
        return tmp_path

    return DEFAULT_CSV_PATH


def classify_lot_type(row_type_local: str | None, nature_culture: str | None) -> str:
    """Classify a row into a lot type."""
    if row_type_local and str(row_type_local) in TYPE_LOCAL_MAP:
        return TYPE_LOCAL_MAP[str(row_type_local)]
    if nature_culture:
        return "Terrain"
    return "Terrain"


def dataframe_to_copy_buffer(df: pl.DataFrame, columns: list[str]) -> io.BytesIO:
    """Serialize a polars DataFrame to a tab-separated BytesIO buffer for COPY FROM STDIN."""
    buf = io.BytesIO()
    df.select(columns).write_csv(
        buf,
        separator="\t",
        null_value="\\N",
        include_header=False,
        quote_style="never",
    )
    buf.seek(0)
    return buf


def main() -> None:
    parser = argparse.ArgumentParser(description="Import geolocalized DVF data")
    parser.add_argument("--csv", type=str, help="Path to dvf.csv", default=None)
    args = parser.parse_args()

    csv_path = resolve_csv_path(args.csv)
    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}")
        print("Download it first: uv run download-dvf <url>")
        sys.exit(1)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Try loading from .env files
        try:
            from dotenv import load_dotenv

            project_root = Path(__file__).resolve().parent.parent.parent
            # backend/.env has DATABASE_URL for local dev
            load_dotenv(project_root / "backend" / ".env")
            # root .env may have other vars
            load_dotenv(project_root / ".env")
            database_url = os.environ.get("DATABASE_URL")
        except ImportError:
            pass

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    t0 = time.time()

    # --- Step 1: Read CSV ---
    print(f"Reading {csv_path}...")
    df = pl.read_csv(
        csv_path,
        schema_overrides=DVF_SCHEMA_OVERRIDES,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )
    print(f"  Raw rows: {len(df):,}")

    # --- Step 2: Filter to sales only ---
    df = df.filter(pl.col("nature_mutation").str.starts_with("Vente"))
    print(f"  After Vente filter: {len(df):,}")

    # --- Step 3: Semi-join to keep only mutations with at least 1 Appartement or Maison ---
    has_habitation = (
        df.filter(pl.col("type_local").is_in(["Maison", "Appartement"]))
        .select("id_mutation")
        .unique()
    )

    df = df.join(has_habitation, on="id_mutation", how="semi")
    print(f"  After habitation filter: {len(df):,}")

    # --- Step 4: Build dvf_sales via group_by ---
    print("Building dvf_sales...")

    sales = df.group_by("id_mutation").agg(
        pl.col("date_mutation").first(),
        pl.col("nature_mutation").first(),
        pl.col("valeur_fonciere").first().alias("prix"),
        # Address: take from first row
        pl.col("adresse_numero").first(),
        pl.col("adresse_nom_voie").first(),
        pl.col("code_postal").first(),
        pl.col("code_commune").first(),
        pl.col("nom_commune").first(),
        pl.col("code_departement").first(),
        # Geo: mean of non-null coordinates
        pl.col("longitude").mean(),
        pl.col("latitude").mean(),
        # Type counts
        (pl.col("type_local") == "Appartement").sum().cast(pl.Int16).alias("n_appartements"),
        (pl.col("type_local") == "Maison").sum().cast(pl.Int16).alias("n_maisons"),
        (pl.col("type_local") == "Dépendance").sum().cast(pl.Int16).alias("n_dependances"),
        # Terrain parcels: rows with nature_culture but no type_local
        (pl.col("type_local").is_null() & pl.col("nature_culture").is_not_null())
        .sum()
        .cast(pl.Int16)
        .alias("n_parcelles_terrain"),
        # Aggregated surface (only habitable: Appartement + Maison)
        pl.col("surface_reelle_bati")
        .filter(pl.col("type_local").is_in(["Appartement", "Maison"]))
        .sum()
        .alias("surface_bati"),
        pl.col("nombre_pieces_principales")
        .filter(pl.col("type_local").is_in(["Appartement", "Maison"]))
        .sum()
        .alias("nombre_pieces"),
        pl.col("surface_terrain").sum().alias("surface_terrain"),
        pl.col("nombre_lots").first().alias("nombre_lots"),
    )

    # Determine type_principal
    sales = sales.with_columns(
        pl.when(pl.col("n_appartements") > 0)
        .then(pl.lit("Appartement"))
        .when(pl.col("n_maisons") > 0)
        .then(pl.lit("Maison"))
        .otherwise(pl.lit(None))
        .alias("type_principal")
    )

    # Cast numeric columns
    sales = sales.with_columns(
        pl.col("adresse_numero").cast(pl.Int32, strict=False),
        pl.col("surface_bati").cast(pl.Int32, strict=False),
        pl.col("nombre_pieces").cast(pl.Int32, strict=False),
        pl.col("surface_terrain").cast(pl.Int32, strict=False),
        pl.col("nombre_lots").cast(pl.Int32, strict=False),
    )

    # Compute prix_m2 and annee
    sales = sales.with_columns(
        pl.when(pl.col("surface_bati") > 0)
        .then((pl.col("prix") / pl.col("surface_bati")).round(2))
        .otherwise(None)
        .alias("prix_m2"),
        pl.col("date_mutation").str.slice(0, 4).cast(pl.Int16, strict=False).alias("annee"),
    )

    print(f"  dvf_sales rows: {len(sales):,}")

    # --- Step 5: Build dvf_sale_lots ---
    print("Building dvf_sale_lots...")

    lots = df.select(
        "id_mutation",
        pl.when(pl.col("type_local") == "Maison")
        .then(pl.lit("Maison"))
        .when(pl.col("type_local") == "Appartement")
        .then(pl.lit("Appartement"))
        .when(pl.col("type_local") == "Dépendance")
        .then(pl.lit("Dépendance"))
        .when(pl.col("type_local").is_not_null())
        .then(pl.lit("Commercial"))
        .when(pl.col("nature_culture").is_not_null())
        .then(pl.lit("Terrain"))
        .otherwise(pl.lit("Terrain"))
        .alias("lot_type"),
        pl.col("nature_culture"),
        pl.col("surface_reelle_bati").cast(pl.Int32, strict=False).alias("surface_bati"),
        pl.col("nombre_pieces_principales").cast(pl.Int32, strict=False).alias("nombre_pieces"),
        pl.col("surface_terrain").cast(pl.Int32, strict=False).alias("surface_terrain"),
        pl.col("id_parcelle"),
        pl.col("longitude"),
        pl.col("latitude"),
    )

    print(f"  dvf_sale_lots rows: {len(lots):,}")

    # Free the raw DataFrame — no longer needed
    del df

    # --- Step 6: Columns for COPY ---
    sales_columns = [
        "id_mutation",
        "date_mutation",
        "nature_mutation",
        "prix",
        "adresse_numero",
        "adresse_nom_voie",
        "code_postal",
        "code_commune",
        "nom_commune",
        "code_departement",
        "longitude",
        "latitude",
        "type_principal",
        "surface_bati",
        "nombre_pieces",
        "surface_terrain",
        "nombre_lots",
        "n_appartements",
        "n_maisons",
        "n_dependances",
        "n_parcelles_terrain",
        "prix_m2",
        "annee",
    ]
    lots_columns = [
        "id_mutation",
        "lot_type",
        "nature_culture",
        "surface_bati",
        "nombre_pieces",
        "surface_terrain",
        "id_parcelle",
        "longitude",
        "latitude",
    ]

    t_process = time.time() - t0
    print(f"  Processing took {t_process:.1f}s")

    # --- Step 7: Load into PostgreSQL ---
    # Serialize and load each table one at a time to limit peak memory.
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Truncate
        print("Truncating tables...")
        cur.execute("TRUNCATE dvf_sales CASCADE")

        # Drop indexes for faster COPY
        print("Dropping indexes...")
        index_defs = []
        cur.execute("""
            SELECT indexname, indexdef FROM pg_indexes
            WHERE tablename IN ('dvf_sales', 'dvf_sale_lots')
            AND indexname NOT LIKE '%_pkey'
            AND indexname != 'dvf_sales_id_mutation_key'
        """)
        for row in cur.fetchall():
            index_defs.append((row[0], row[1]))
            cur.execute(
                psycopg2.sql.SQL("DROP INDEX IF EXISTS {}").format(psycopg2.sql.Identifier(row[0]))
            )

        # COPY dvf_sales (serialize → load → free)
        print("Serializing dvf_sales...")
        sales_buf = dataframe_to_copy_buffer(sales, sales_columns)
        del sales  # Free DataFrame before COPY
        print("COPY dvf_sales...")
        db_sales_columns = ", ".join(sales_columns)
        cur.copy_expert(
            f"COPY dvf_sales ({db_sales_columns}) FROM STDIN WITH (FORMAT text, NULL '\\N')",
            sales_buf,
        )
        del sales_buf  # Free buffer
        cur.execute("SELECT COUNT(*) FROM dvf_sales")
        sales_count = cur.fetchone()[0]
        print(f"  Loaded {sales_count:,} sales")

        # COPY dvf_sale_lots (serialize → load → free)
        print("Serializing dvf_sale_lots...")
        lots_buf = dataframe_to_copy_buffer(lots, lots_columns)
        del lots  # Free DataFrame before COPY
        print("COPY dvf_sale_lots...")
        db_lots_columns = ", ".join(lots_columns)
        cur.copy_expert(
            f"COPY dvf_sale_lots ({db_lots_columns}) FROM STDIN WITH (FORMAT text, NULL '\\N')",
            lots_buf,
        )
        del lots_buf  # Free buffer
        cur.execute("SELECT COUNT(*) FROM dvf_sale_lots")
        lots_count = cur.fetchone()[0]
        print(f"  Loaded {lots_count:,} lots")

        # Recreate indexes
        print("Recreating indexes...")
        for idx_name, idx_def in index_defs:
            print(f"  {idx_name}")
            cur.execute(idx_def)

        # Commit the data + indexes
        conn.commit()

        # ANALYZE needs autocommit
        print("Running ANALYZE...")
        conn.autocommit = True
        cur.execute("ANALYZE dvf_sales")
        cur.execute("ANALYZE dvf_sale_lots")

        t_total = time.time() - t0
        print()
        print("=" * 60)
        print("IMPORT COMPLETE")
        print(f"  dvf_sales:     {sales_count:>12,}")
        print(f"  dvf_sale_lots: {lots_count:>12,}")
        print(f"  Processing:    {t_process:>10.1f}s")
        print(f"  Total time:    {t_total:>10.1f}s")
        print("=" * 60)

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
