"""migrate dvf to geolocalized schema

Revision ID: l3m4n5o6p7q8
Revises: k2l3m4n5o6p7
Create Date: 2026-03-06 10:00:00.000000

Replaces dvf_records + dvf_grouped_transactions + dvf_imports + dvf_stats
with dvf_sales + dvf_sale_lots for the new geolocalized DVF dataset.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "l3m4n5o6p7q8"
down_revision: Union[str, None] = "k2l3m4n5o6p7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pg_trgm extension exists (needed for GIN trigram indexes)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- Create new tables ---

    op.create_table(
        "dvf_sales",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_mutation", sa.String(), nullable=False, unique=True),
        sa.Column("date_mutation", sa.Date(), nullable=False),
        sa.Column("nature_mutation", sa.String()),
        sa.Column("prix", sa.Numeric()),
        sa.Column("adresse_numero", sa.Integer()),
        sa.Column("adresse_nom_voie", sa.String()),
        sa.Column(
            "adresse_complete",
            sa.String(),
            sa.Computed("COALESCE(adresse_numero::text || ' ', '') || adresse_nom_voie"),
        ),
        sa.Column("code_postal", sa.String(5)),
        sa.Column("code_commune", sa.String(5)),
        sa.Column("nom_commune", sa.String()),
        sa.Column("code_departement", sa.String(3)),
        sa.Column("longitude", sa.Float()),
        sa.Column("latitude", sa.Float()),
        sa.Column("type_principal", sa.String()),
        sa.Column("surface_bati", sa.Integer()),
        sa.Column("nombre_pieces", sa.Integer()),
        sa.Column("surface_terrain", sa.Integer()),
        sa.Column("nombre_lots", sa.Integer()),
        sa.Column("n_appartements", sa.SmallInteger()),
        sa.Column("n_maisons", sa.SmallInteger()),
        sa.Column("n_dependances", sa.SmallInteger()),
        sa.Column("n_parcelles_terrain", sa.SmallInteger()),
        sa.Column("prix_m2", sa.Numeric()),
        sa.Column("annee", sa.SmallInteger()),
    )

    op.create_table(
        "dvf_sale_lots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "id_mutation",
            sa.String(),
            sa.ForeignKey("dvf_sales.id_mutation", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lot_type", sa.String()),
        sa.Column("nature_culture", sa.String()),
        sa.Column("surface_bati", sa.Integer()),
        sa.Column("nombre_pieces", sa.Integer()),
        sa.Column("surface_terrain", sa.Integer()),
        sa.Column("id_parcelle", sa.String()),
        sa.Column("longitude", sa.Float()),
        sa.Column("latitude", sa.Float()),
    )

    # --- Indexes on dvf_sales ---
    op.create_index("idx_dvf_sales_date_mutation", "dvf_sales", ["date_mutation"])
    op.create_index("idx_dvf_sales_code_postal", "dvf_sales", ["code_postal"])
    op.create_index("idx_dvf_sales_code_departement", "dvf_sales", ["code_departement"])
    op.create_index("idx_dvf_sales_annee", "dvf_sales", ["annee"])
    op.create_index("idx_dvf_sales_postal_type", "dvf_sales", ["code_postal", "type_principal"])
    op.create_index(
        "idx_dvf_sales_postal_type_date",
        "dvf_sales",
        ["code_postal", "type_principal", "date_mutation"],
    )
    op.execute(
        "CREATE INDEX idx_dvf_sales_adresse_gin ON dvf_sales "
        "USING gin(adresse_complete gin_trgm_ops)"
    )
    op.execute("CREATE INDEX idx_dvf_sales_prix_m2 ON dvf_sales(prix_m2) WHERE prix_m2 > 0")

    # --- Indexes on dvf_sale_lots ---
    op.create_index("idx_dvf_sale_lots_id_mutation", "dvf_sale_lots", ["id_mutation"])
    op.create_index("idx_dvf_sale_lots_lot_type", "dvf_sale_lots", ["lot_type"])

    # --- Drop old objects ---

    # Drop materialized view first (it depends on dvf_records)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS dvf_grouped_transactions CASCADE")
    op.execute("DROP FUNCTION IF EXISTS refresh_dvf_grouped_transactions()")

    op.drop_table("dvf_stats")
    op.drop_table("dvf_imports")
    op.drop_table("dvf_records")


def downgrade() -> None:
    # Recreate old tables (data loss accepted)
    op.drop_table("dvf_sale_lots")
    op.drop_table("dvf_sales")

    op.create_table(
        "dvf_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sale_date", sa.Date()),
        sa.Column("sale_price", sa.Float()),
        sa.Column("address", sa.String()),
        sa.Column("postal_code", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("department", sa.String()),
        sa.Column("property_type", sa.String()),
        sa.Column("surface_area", sa.Float()),
        sa.Column("rooms", sa.Integer()),
        sa.Column("land_surface", sa.Float()),
        sa.Column("price_per_sqm", sa.Float()),
        sa.Column("raw_data", sa.Text()),
        sa.Column("data_year", sa.Integer()),
        sa.Column("source_file", sa.String()),
        sa.Column("source_file_hash", sa.String(64)),
        sa.Column("import_batch_id", sa.String(36)),
        sa.Column("imported_at", sa.DateTime()),
        sa.Column("transaction_group_id", sa.String(32)),
        sa.Column("created_at", sa.DateTime()),
    )

    op.create_table(
        "dvf_imports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.String(36), unique=True, nullable=False),
        sa.Column("source_file", sa.String(), nullable=False),
        sa.Column("source_file_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("data_year", sa.Integer(), nullable=False),
        sa.Column("total_records", sa.Integer()),
        sa.Column("inserted_records", sa.Integer()),
        sa.Column("updated_records", sa.Integer()),
        sa.Column("skipped_records", sa.Integer()),
        sa.Column("error_records", sa.Integer()),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("error_message", sa.Text()),
    )

    op.create_table(
        "dvf_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("total_records", sa.Integer(), server_default="0"),
        sa.Column("total_imports", sa.Integer(), server_default="0"),
        sa.Column("last_import_date", sa.DateTime()),
        sa.Column("last_updated", sa.DateTime()),
    )
