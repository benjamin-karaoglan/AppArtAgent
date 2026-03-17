"""add price_analyses table

Revision ID: m4n5o6p7q8r9
Revises: l3m4n5o6p7q8
Create Date: 2026-03-06
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "m4n5o6p7q8r9"
down_revision = "l3m4n5o6p7q8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "price_analyses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "property_id",
            sa.Integer(),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        # Core metrics
        sa.Column("estimated_value", sa.Float(), nullable=True),
        sa.Column("price_per_sqm", sa.Float(), nullable=True),
        sa.Column("market_avg_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("market_median_price_per_sqm", sa.Float(), nullable=True),
        # Analysis results
        sa.Column("price_deviation_percent", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("market_trend_annual", sa.Float(), nullable=True),
        sa.Column("recommendation", sa.String(), nullable=True),
        sa.Column("comparables_count", sa.Integer(), nullable=True),
        # Trend projection summary
        sa.Column("estimated_value_2025", sa.Float(), nullable=True),
        sa.Column("projected_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("trend_used", sa.Float(), nullable=True),
        sa.Column("trend_source", sa.String(), nullable=True),
        sa.Column("trend_sample_size", sa.Integer(), nullable=True),
        # JSON blobs
        sa.Column("comparable_sales_json", postgresql.JSON(), nullable=True),
        sa.Column("trend_projection_json", postgresql.JSON(), nullable=True),
        sa.Column("market_trend_json", postgresql.JSON(), nullable=True),
        # User exclusions
        sa.Column("excluded_sale_ids", postgresql.JSON(), nullable=True, server_default="[]"),
        sa.Column(
            "excluded_neighboring_sale_ids", postgresql.JSON(), nullable=True, server_default="[]"
        ),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_price_analyses_property_id", "price_analyses", ["property_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_price_analyses_property_id", table_name="price_analyses")
    op.drop_table("price_analyses")
