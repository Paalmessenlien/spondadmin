"""add invite scheduling fields

Revision ID: 8f5b3c9d2e10
Revises: 7e4a8b6c1d92
Create Date: 2026-05-14 09:00:00.000000

Adds an "invite send-at" pair on both `training_session_types` (as the
default) and `training_shifts` (as the per-shift override):

- `invite_lead_days INT NULL` — number of days before the shift's date
  on which the Spond invitation should be sent. NULL means "send
  immediately on publish".
- `invite_send_time TIME NULL` — local Oslo time of day to send.
  NULL means "send immediately on publish".

The publish service computes the absolute send-at from
`shift.date - lead_days @ send_time`, falling back to the session type's
values when the shift's are NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8f5b3c9d2e10'
down_revision: Union[str, None] = '7e4a8b6c1d92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_session_types',
        sa.Column('invite_lead_days', sa.Integer(), nullable=True),
    )
    op.add_column(
        'training_session_types',
        sa.Column('invite_send_time', sa.Time(), nullable=True),
    )
    op.add_column(
        'training_shifts',
        sa.Column('invite_lead_days', sa.Integer(), nullable=True),
    )
    op.add_column(
        'training_shifts',
        sa.Column('invite_send_time', sa.Time(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_shifts', 'invite_send_time')
    op.drop_column('training_shifts', 'invite_lead_days')
    op.drop_column('training_session_types', 'invite_send_time')
    op.drop_column('training_session_types', 'invite_lead_days')
