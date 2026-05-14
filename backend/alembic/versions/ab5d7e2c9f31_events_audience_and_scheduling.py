"""events audience + scheduling fields

Revision ID: ab5d7e2c9f31
Revises: 9a6c4d1e8f23
Create Date: 2026-05-14 12:00:00.000000

Brings the `events` table to feature-parity with `training_shifts` so the
Events UI can target Spond invites by subgroup and schedule the
invitation send-time:

- `events.invited_subgroup_uids JSON NULL` — list of Spond subgroup uids
  to narrow the invite to. NULL or empty list → invite the whole group.
- `events.invite_lead_days INTEGER NULL` — days before the event's
  start_time at which the Spond invitation should be sent.
- `events.invite_send_time TIME NULL` — local Europe/Oslo time-of-day to
  send.

If either of the two scheduling columns is NULL the event sends
immediately on publish (matches the training-side semantics). The
existing `events.invite_time` (datetime) keeps holding the resolved
absolute timestamp that gets written to Spond's `inviteTime` field.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ab5d7e2c9f31'
down_revision: Union[str, None] = '9a6c4d1e8f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'events',
        sa.Column('invited_subgroup_uids', sa.JSON(), nullable=True),
    )
    op.add_column(
        'events',
        sa.Column('invite_lead_days', sa.Integer(), nullable=True),
    )
    op.add_column(
        'events',
        sa.Column('invite_send_time', sa.Time(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('events', 'invite_send_time')
    op.drop_column('events', 'invite_lead_days')
    op.drop_column('events', 'invited_subgroup_uids')
