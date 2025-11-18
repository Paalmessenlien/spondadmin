"""add_event_sync_and_location_fields

Revision ID: eddec35a6940
Revises: 20251117_145748
Create Date: 2025-11-18 12:25:37.793430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eddec35a6940'
down_revision: Union[str, None] = '20251117_145748'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add location fields
    op.add_column('events', sa.Column('location_address', sa.String(length=500), nullable=True))
    op.add_column('events', sa.Column('location_latitude', sa.Float(), nullable=True))
    op.add_column('events', sa.Column('location_longitude', sa.Float(), nullable=True))

    # Add max_accepted field
    op.add_column('events', sa.Column('max_accepted', sa.Integer(), nullable=False, server_default='0'))

    # Add sync status fields
    op.add_column('events', sa.Column('sync_status', sa.String(length=50), nullable=False, server_default='synced'))
    op.add_column('events', sa.Column('sync_error', sa.Text(), nullable=True))

    # Create index on sync_status
    op.create_index(op.f('ix_events_sync_status'), 'events', ['sync_status'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index(op.f('ix_events_sync_status'), table_name='events')

    # Drop sync status fields
    op.drop_column('events', 'sync_error')
    op.drop_column('events', 'sync_status')

    # Drop max_accepted field
    op.drop_column('events', 'max_accepted')

    # Drop location fields
    op.drop_column('events', 'location_longitude')
    op.drop_column('events', 'location_latitude')
    op.drop_column('events', 'location_address')
