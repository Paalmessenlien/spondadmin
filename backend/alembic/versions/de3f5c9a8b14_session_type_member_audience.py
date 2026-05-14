"""add invited_member_ids on training_session_types

Revision ID: de3f5c9a8b14
Revises: cf8a2b1d4e7c
Create Date: 2026-05-14 15:00:00.000000

Lets a session type define "specific members" as its default audience
in addition to (or instead of) the existing `spond_subgroup_uids`.
Mirrors `training_shifts.invited_member_ids` and is the same wire shape
— a JSON list of internal `members.id` integers.

Precedence in the publish flow (see spond_event_create_service) after
this change:
  1. shift.invited_member_ids
  2. shift.invited_subgroup_uids
  3. session_type.invited_member_ids  <-- new
  4. session_type.spond_subgroup_uids
  5. whole group
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'de3f5c9a8b14'
down_revision: Union[str, None] = 'cf8a2b1d4e7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_session_types',
        sa.Column('invited_member_ids', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_session_types', 'invited_member_ids')
