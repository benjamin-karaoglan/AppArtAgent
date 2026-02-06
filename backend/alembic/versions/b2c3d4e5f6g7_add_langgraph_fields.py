"""Add LangGraph agent fields to DocumentSummary

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-29 12:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to document_summaries table
    op.add_column("document_summaries", sa.Column("overall_summary", sa.Text(), nullable=True))
    op.add_column("document_summaries", sa.Column("recommendations", sa.JSON(), nullable=True))
    op.add_column("document_summaries", sa.Column("total_annual_cost", sa.Float(), nullable=True))
    op.add_column("document_summaries", sa.Column("total_one_time_cost", sa.Float(), nullable=True))
    op.add_column(
        "document_summaries", sa.Column("risk_level", sa.String(length=50), nullable=True)
    )
    op.add_column("document_summaries", sa.Column("synthesis_data", sa.JSON(), nullable=True))
    op.add_column("document_summaries", sa.Column("last_updated", sa.DateTime(), nullable=True))

    # Make category nullable to support overall summaries
    op.alter_column("document_summaries", "category", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Remove columns
    op.drop_column("document_summaries", "last_updated")
    op.drop_column("document_summaries", "synthesis_data")
    op.drop_column("document_summaries", "risk_level")
    op.drop_column("document_summaries", "total_one_time_cost")
    op.drop_column("document_summaries", "total_annual_cost")
    op.drop_column("document_summaries", "recommendations")
    op.drop_column("document_summaries", "overall_summary")

    # Restore category to non-nullable
    op.alter_column("document_summaries", "category", existing_type=sa.String(), nullable=False)
