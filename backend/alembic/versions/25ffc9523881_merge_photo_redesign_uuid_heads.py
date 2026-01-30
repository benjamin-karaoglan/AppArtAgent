"""merge photo redesign uuid heads

Revision ID: 25ffc9523881
Revises: 19c3bf31bde4, c4d5e6f7g8h9
Create Date: 2026-01-10 19:55:33.172324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25ffc9523881'
down_revision: Union[str, None] = ('19c3bf31bde4', 'c4d5e6f7g8h9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
