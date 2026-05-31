"""add ai_competition_type to external_events

Revision ID: d9a4f2c61b85
Revises: c8f3d1a25e74
Create Date: 2026-05-31 19:30:00.000000

Stores the AI-classified archery discipline for an upcoming external
competition (felt, bane, innendørs, 3D, ski, clout, annet, ukjent) so the
competitions list can show and filter by competition type. Nullable — existing
rows stay null until re-analyzed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd9a4f2c61b85'
down_revision: Union[str, None] = 'c8f3d1a25e74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'external_events',
        sa.Column('ai_competition_type', sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('external_events', 'ai_competition_type')
