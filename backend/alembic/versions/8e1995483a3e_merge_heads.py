"""merge_heads

Revision ID: 8e1995483a3e
Revises: a1b2c3d4e5f6, c3d4e5f6g7h8
Create Date: 2026-03-15 12:00:34.116458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e1995483a3e'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'c3d4e5f6g7h8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
