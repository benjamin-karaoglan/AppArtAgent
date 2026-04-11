#!/usr/bin/env python3
"""
Import the geolocalized DVF dataset into dvf_sales + dvf_sale_lots.

Strategy: Polars processing + in-memory BytesIO buffer + COPY FROM STDIN.

Usage:
    uv run import-dvf                        # Uses data/dvf/dvf.csv
    uv run import-dvf --csv /path/to/dvf.csv # Custom path
"""

import argparse
import io
import os
import resource
import shutil
import sys
import time
import urllib.request
from pathlib import Path

import polars as pl
import psycopg2
import psycopg2.sql

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


def _download_from_gcs(gcs_uri: str, dest: Path) -> None:
    """Download a file from GCS using google-cloud-storage."""
    from google.cloud import storage  # already a backend dependency

    # Parse gs://bucket/path
    parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name, blob_name = parts[0], parts[1]
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.reload()  # Fetch metadata (size)
    size_mb = (blob.size or 0) / 1024 / 1024
    print(f"Downloading gs://{bucket_name}/{blob_name} ({size_mb:.0f} MB)")
    blob.download_to_filename(str(dest))
    print(f"Downloaded to {dest}")


def resolve_csv_path(cli_csv: str | None) -> Path:
    """Resolve CSV path from CLI arg, env var, or default."""
    if cli_csv:
        return Path(cli_csv)

    # Check for DVF_SOURCE_URL env var (Cloud Run Job)
    source_url = os.environ.get("DVF_SOURCE_URL")
    if source_url:
        # GCS path (fast, same region): gs://bucket/path/dvf.csv
        if source_url.startswith("gs://"):
            tmp_path = Path("/tmp/dvf.csv")
            if tmp_path.exists():
                print(f"Using cached {tmp_path}")
                return tmp_path
            _download_from_gcs(source_url, tmp_path)
            return tmp_path

        # HTTPS URL (data.gouv.fr): download compressed, polars reads .gz natively
        if not source_url.startswith("https://"):
            print("ERROR: DVF_SOURCE_URL must use https:// or gs://")
            sys.exit(1)

        # IMPORTANT: Cloud Run /tmp is RAM-backed (tmpfs), so keep compressed
        gz_path = Path("/tmp/dvf.csv.gz")
        if gz_path.exists():
            print(f"Using cached {gz_path}")
            return gz_path

        print(f"Downloading {source_url}")
        with (
            urllib.request.urlopen(source_url, timeout=120) as resp,  # noqa: S310
            open(gz_path, "wb") as out,
        ):
            shutil.copyfileobj(resp, out)
        size_mb = gz_path.stat().st_size / (1024 * 1024)
        print(f"Downloaded {size_mb:.1f} MB (kept compressed)")
        return gz_path

    return DEFAULT_CSV_PATH


def classify_lot_type(row_type_local: str | None, nature_culture: str | None) -> str:
    """Classify a row into a lot type."""
    if row_type_local and str(row_type_local) in TYPE_LOCAL_MAP:
        return TYPE_LOCAL_MAP[str(row_type_local)]
    if nature_culture:
        return "Terrain"
    return "Terrain"


def log_mem(label: str) -> None:
    """Log current memory usage (RSS) in MiB."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS returns bytes, Linux returns KiB
    if sys.platform == "darwin":
        mib = rss / (1024 * 1024)
    else:
        mib = rss / 1024
    print(f"  [MEM] {label}: {mib:,.0f} MiB peak RSS")


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


CHUNK_SIZE = 500_000  # rows per COPY batch


def chunked_copy(
    cur: "psycopg2.extensions.cursor",
    df: pl.DataFrame,
    table: str,
    columns: list[str],
) -> int:
    """COPY a DataFrame into PostgreSQL in chunks with progress logging."""
    total = len(df)
    col_list = ", ".join(columns)
    copy_sql = f"COPY {table} ({col_list}) FROM STDIN WITH (FORMAT text, NULL '\\N')"

    loaded = 0
    chunk_idx = 0
    while loaded < total:
        chunk = df.slice(loaded, CHUNK_SIZE)
        buf = dataframe_to_copy_buffer(chunk, columns)
        cur.copy_expert(copy_sql, buf)
        del buf
        loaded += len(chunk)
        del chunk
        chunk_idx += 1
        pct = loaded / total * 100
        print(f"  chunk {chunk_idx}: {loaded:,}/{total:,} rows ({pct:.0f}%)")
        log_mem(f"after chunk {chunk_idx}")

    return loaded


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
    log_mem("start")
    print(f"Reading {csv_path}...")
    df = pl.read_csv(
        csv_path,
        schema_overrides=DVF_SCHEMA_OVERRIDES,
        ignore_errors=True,
        truncate_ragged_lines=True,
    )
    print(f"  Raw rows: {len(df):,}")
    log_mem("after read_csv")

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
    log_mem("after sales groupby")

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
    log_mem("after lots select (before del df)")

    # Free the raw DataFrame — no longer needed
    del df
    log_mem("after del df")

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

        # Drop indexes for faster COPY (hardcoded list — survives interrupted runs)
        print("Dropping indexes...")
        for idx_name in [
            "idx_dvf_sales_date_mutation",
            "idx_dvf_sales_code_postal",
            "idx_dvf_sales_code_departement",
            "idx_dvf_sales_annee",
            "idx_dvf_sales_postal_type",
            "idx_dvf_sales_postal_type_date",
            "idx_dvf_sales_adresse_gin",
            "idx_dvf_sales_prix_m2",
            "idx_dvf_sale_lots_id_mutation",
            "idx_dvf_sale_lots_lot_type",
        ]:
            cur.execute(
                psycopg2.sql.SQL("DROP INDEX IF EXISTS {}").format(
                    psycopg2.sql.Identifier(idx_name)
                )
            )

        # COPY dvf_sales in chunks
        print(f"COPY dvf_sales ({len(sales):,} rows, {CHUNK_SIZE:,}/chunk)...")
        sales_count = chunked_copy(cur, sales, "dvf_sales", sales_columns)
        del sales
        print(f"  Loaded {sales_count:,} sales")
        log_mem("after sales COPY")

        # Commit sales before starting lots (reduces transaction size)
        print("Committing dvf_sales...")
        conn.commit()

        # COPY dvf_sale_lots in chunks
        print(f"COPY dvf_sale_lots ({len(lots):,} rows, {CHUNK_SIZE:,}/chunk)...")
        lots_count = chunked_copy(cur, lots, "dvf_sale_lots", lots_columns)
        del lots
        print(f"  Loaded {lots_count:,} lots")
        log_mem("after lots COPY")

        # Recreate indexes (hardcoded — matches alembic migration)
        print("Recreating indexes...")
        index_defs = [
            (
                "idx_dvf_sales_date_mutation",
                "CREATE INDEX idx_dvf_sales_date_mutation ON dvf_sales (date_mutation)",
            ),
            (
                "idx_dvf_sales_code_postal",
                "CREATE INDEX idx_dvf_sales_code_postal ON dvf_sales (code_postal)",
            ),
            (
                "idx_dvf_sales_code_departement",
                "CREATE INDEX idx_dvf_sales_code_departement ON dvf_sales (code_departement)",
            ),
            ("idx_dvf_sales_annee", "CREATE INDEX idx_dvf_sales_annee ON dvf_sales (annee)"),
            (
                "idx_dvf_sales_postal_type",
                "CREATE INDEX idx_dvf_sales_postal_type ON dvf_sales (code_postal, type_principal)",
            ),
            (
                "idx_dvf_sales_postal_type_date",
                "CREATE INDEX idx_dvf_sales_postal_type_date ON dvf_sales (code_postal, type_principal, date_mutation)",
            ),
            (
                "idx_dvf_sales_adresse_gin",
                "CREATE INDEX idx_dvf_sales_adresse_gin ON dvf_sales USING gin(adresse_complete gin_trgm_ops)",
            ),
            (
                "idx_dvf_sales_prix_m2",
                "CREATE INDEX idx_dvf_sales_prix_m2 ON dvf_sales (prix_m2) WHERE prix_m2 > 0",
            ),
            (
                "idx_dvf_sale_lots_id_mutation",
                "CREATE INDEX idx_dvf_sale_lots_id_mutation ON dvf_sale_lots (id_mutation)",
            ),
            (
                "idx_dvf_sale_lots_lot_type",
                "CREATE INDEX idx_dvf_sale_lots_lot_type ON dvf_sale_lots (lot_type)",
            ),
        ]
        for idx_name, idx_sql in index_defs:
            print(f"  {idx_name}...", end=" ", flush=True)
            t_idx = time.time()
            cur.execute(idx_sql)
            print(f"done ({time.time() - t_idx:.1f}s)")

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
