"""add event group columns

Revision ID: 20251123_000000
Revises: eddec35a6940
Create Date: 2025-11-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251123_000000'
down_revision: Union[str, None] = 'eddec35a6940'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add group association columns to events table:
    1. primary_group_id - Single group ID for fast filtering (indexed)
    2. group_ids - JSON array of all group IDs this event belongs to
    """
    # Add primary_group_id column with index for fast filtering
    op.add_column('events', sa.Column('primary_group_id', sa.String(length=255), nullable=True))
    op.create_index(op.f('ix_events_primary_group_id'), 'events', ['primary_group_id'], unique=False)

    # Add group_ids JSON column for multi-group associations
    op.add_column('events', sa.Column('group_ids', sa.JSON(), nullable=True))


def downgrade() -> None:
    """
    Revert schema changes
    """
    # Drop group_ids column
    op.drop_column('events', 'group_ids')

    # Drop index and primary_group_id column
    op.drop_index(op.f('ix_events_primary_group_id'), table_name='events')
    op.drop_column('events', 'primary_group_id')
