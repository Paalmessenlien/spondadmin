"""add last_reverse_synced_at to training_shifts

Revision ID: b7e2a4c19d33
Revises: 00eef71933e9
Create Date: 2026-05-31 08:00:00.000000

Adds a nullable ``training_shifts.last_reverse_synced_at`` timestamp. The
events reverse-sync stamps it whenever it writes a Spond-side change (time,
cancellation, leader, audience) back onto a shift, so the UI can show that a
shift was updated from Spond. NULL = never reverse-synced.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e2a4c19d33'
down_revision: Union[str, None] = '00eef71933e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_shifts',
        sa.Column('last_reverse_synced_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_shifts', 'last_reverse_synced_at')
