"""add linked_event_id + linked_competition_id to external_events

Revision ID: c8f3d1a25e74
Revises: b7e2a4c19d33
Create Date: 2026-05-31 08:30:00.000000

Lets an upcoming external competition (scraped from bueskyting.no) link to a
local Spond ``Event`` (the club's planned attendance) and/or a ``Competition``
(its results), so the UI can cross-navigate. Both nullable, ON DELETE SET NULL
— the link is advisory and must survive the target being re-synced/removed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c8f3d1a25e74'
down_revision: Union[str, None] = 'b7e2a4c19d33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'external_events',
        sa.Column('linked_event_id', sa.Integer(), nullable=True),
    )
    op.add_column(
        'external_events',
        sa.Column('linked_competition_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_external_events_linked_event_id',
        'external_events', 'events',
        ['linked_event_id'], ['id'], ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_external_events_linked_competition_id',
        'external_events', 'competitions',
        ['linked_competition_id'], ['id'], ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_external_events_linked_competition_id', 'external_events',
        type_='foreignkey',
    )
    op.drop_constraint(
        'fk_external_events_linked_event_id', 'external_events',
        type_='foreignkey',
    )
    op.drop_column('external_events', 'linked_competition_id')
    op.drop_column('external_events', 'linked_event_id')
