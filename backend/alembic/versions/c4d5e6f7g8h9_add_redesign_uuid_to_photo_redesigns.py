"""Add redesign_uuid to photo_redesigns.

Revision ID: c4d5e6f7g8h9
Revises: b2c3d4e5f6g7
Create Date: 2026-01-10 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = "c4d5e6f7g8h9"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "photo_redesigns",
        sa.Column("redesign_uuid", sa.String(), nullable=True)
    )
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM photo_redesigns"))
    for row in result:
        connection.execute(
            sa.text(
                "UPDATE photo_redesigns SET redesign_uuid = :uuid WHERE id = :id"
            ),
            {"uuid": str(uuid.uuid4()), "id": row[0]}
        )
    op.alter_column("photo_redesigns", "redesign_uuid", nullable=False)
    op.create_unique_constraint(
        "uq_photo_redesigns_redesign_uuid",
        "photo_redesigns",
        ["redesign_uuid"]
    )
    op.create_index(
        "ix_photo_redesigns_redesign_uuid",
        "photo_redesigns",
        ["redesign_uuid"],
        unique=False
    )


def downgrade():
    op.drop_index("ix_photo_redesigns_redesign_uuid", table_name="photo_redesigns")
    op.drop_constraint(
        "uq_photo_redesigns_redesign_uuid",
        "photo_redesigns",
        type_="unique"
    )
    op.drop_column("photo_redesigns", "redesign_uuid")
