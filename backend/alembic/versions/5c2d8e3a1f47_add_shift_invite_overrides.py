"""add per-shift invite overrides

Revision ID: 5c2d8e3a1f47
Revises: 4a1f7c2e9b0d
Create Date: 2026-05-13 13:00:00.000000

Adds two nullable columns on `training_shifts` so each shift can override the
session type's invite scope:

- `invited_subgroup_uid` — Spond subgroup uid to target (within the session
  type's Spond group). Wins over `session_types.spond_subgroup_uid`.
- `invited_member_ids` — JSON list of `members.id` values. When non-empty,
  invites exactly these members (takes precedence over both subgroup fields).

If both columns are NULL, the shift falls back to the session type's invite
scope, which itself falls back to inviting the whole Spond group.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5c2d8e3a1f47'
down_revision: Union[str, None] = '4a1f7c2e9b0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_shifts',
        sa.Column('invited_subgroup_uid', sa.String(length=255), nullable=True),
    )
    op.add_column(
        'training_shifts',
        sa.Column('invited_member_ids', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_shifts', 'invited_member_ids')
    op.drop_column('training_shifts', 'invited_subgroup_uid')
