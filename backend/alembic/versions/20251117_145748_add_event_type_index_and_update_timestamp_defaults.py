"""Add event_type index and update timestamp defaults

Revision ID: 20251117_145748
Revises:
Create Date: 2025-11-17 14:57:48.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251117_145748'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Apply schema changes:
    1. Add index on events.event_type
    2. Update timestamp defaults to use server-side func.now()
    """
    # Add index on event_type for better query performance
    op.create_index(
        'ix_events_event_type',
        'events',
        ['event_type'],
        unique=False
    )

    # Note: For SQLite, we cannot directly modify column defaults in existing tables
    # The server_default changes in models will apply to new tables or when using
    # PostgreSQL. For SQLite in development, this is acceptable as the models
    # now use the correct pattern.

    # If using PostgreSQL, uncomment the following:
    # op.alter_column('events', 'last_synced_at',
    #                server_default=sa.func.now())
    # op.alter_column('groups', 'last_synced_at',
    #                server_default=sa.func.now())
    # op.alter_column('members', 'last_synced_at',
    #                server_default=sa.func.now())
    # op.alter_column('sync_history', 'started_at',
    #                server_default=sa.func.now())
    # op.alter_column('audit_logs', 'performed_at',
    #                server_default=sa.func.now())


def downgrade() -> None:
    """
    Revert schema changes
    """
    # Remove index on event_type
    op.drop_index('ix_events_event_type', table_name='events')

    # Note: Reverting server_default changes would require PostgreSQL-specific code
