"""add documents_analyzed_count and dvf_stats table

Revision ID: e6f7g8h9i0j1
Revises: d5e6f7g8h9i0
Create Date: 2026-01-31

This migration adds:
- documents_analyzed_count column to users table
- dvf_stats table for tracking aggregate DVF metrics
"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e6f7g8h9i0j1"
down_revision: Union[str, None] = "d5e6f7g8h9i0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add documents_analyzed_count column to users table
    op.add_column(
        "users",
        sa.Column("documents_analyzed_count", sa.Integer(), nullable=True, server_default="0"),
    )

    # Create dvf_stats table
    op.create_table(
        "dvf_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_imports", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_import_date", sa.DateTime(), nullable=True),
        sa.Column("last_updated", sa.DateTime(), nullable=True, default=datetime.utcnow),
    )

    # Insert initial row for dvf_stats (single row table)
    connection = op.get_bind()

    # Count existing DVF records and set initial stats
    result = connection.execute(sa.text("SELECT COUNT(*) FROM dvf_records")).fetchone()
    dvf_count = result[0] if result else 0

    result = connection.execute(
        sa.text("SELECT COUNT(*) FROM dvf_imports WHERE status = 'completed'")
    ).fetchone()
    import_count = result[0] if result else 0

    connection.execute(
        sa.text("""
            INSERT INTO dvf_stats (id, total_records, total_imports, last_updated)
            VALUES (1, :total_records, :total_imports, :last_updated)
        """),
        {
            "total_records": dvf_count,
            "total_imports": import_count,
            "last_updated": datetime.utcnow(),
        },
    )

    # Initialize documents_analyzed_count for existing users based on their analyzed documents
    connection.execute(
        sa.text("""
            UPDATE users
            SET documents_analyzed_count = (
                SELECT COUNT(*)
                FROM documents
                WHERE documents.user_id = users.id AND documents.is_analyzed = true
            )
        """)
    )


def downgrade() -> None:
    # Drop dvf_stats table
    op.drop_table("dvf_stats")

    # Remove documents_analyzed_count column from users
    op.drop_column("users", "documents_analyzed_count")
