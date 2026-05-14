"""subgroup uid columns become JSON arrays

Revision ID: 9a6c4d1e8f23
Revises: 8f5b3c9d2e10
Create Date: 2026-05-14 10:00:00.000000

Promotes the single-uid columns to JSON arrays so a session type / shift can
target multiple Spond subgroups at once:

- `training_session_types.spond_subgroup_uid` (String) → `spond_subgroup_uids` (JSON)
- `training_shifts.invited_subgroup_uid` (String)    → `invited_subgroup_uids` (JSON)

Existing single values are wrapped as a one-element list; NULLs stay NULL.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9a6c4d1e8f23'
down_revision: Union[str, None] = '8f5b3c9d2e10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Session types
    op.add_column(
        'training_session_types',
        sa.Column('spond_subgroup_uids', sa.JSON(), nullable=True),
    )
    op.execute(
        """
        UPDATE training_session_types
           SET spond_subgroup_uids = jsonb_build_array(spond_subgroup_uid)::json
         WHERE spond_subgroup_uid IS NOT NULL
        """
    )
    op.drop_column('training_session_types', 'spond_subgroup_uid')

    # Shifts
    op.add_column(
        'training_shifts',
        sa.Column('invited_subgroup_uids', sa.JSON(), nullable=True),
    )
    op.execute(
        """
        UPDATE training_shifts
           SET invited_subgroup_uids = jsonb_build_array(invited_subgroup_uid)::json
         WHERE invited_subgroup_uid IS NOT NULL
        """
    )
    op.drop_column('training_shifts', 'invited_subgroup_uid')


def downgrade() -> None:
    # Restore single-uid columns. If a row has 2+ uids in the array, only the
    # first survives the downgrade — there's no lossless mapping back.
    op.add_column(
        'training_shifts',
        sa.Column('invited_subgroup_uid', sa.String(length=255), nullable=True),
    )
    op.execute(
        """
        UPDATE training_shifts
           SET invited_subgroup_uid = (invited_subgroup_uids::jsonb->>0)
         WHERE invited_subgroup_uids IS NOT NULL
           AND jsonb_array_length(invited_subgroup_uids::jsonb) > 0
        """
    )
    op.drop_column('training_shifts', 'invited_subgroup_uids')

    op.add_column(
        'training_session_types',
        sa.Column('spond_subgroup_uid', sa.String(length=255), nullable=True),
    )
    op.execute(
        """
        UPDATE training_session_types
           SET spond_subgroup_uid = (spond_subgroup_uids::jsonb->>0)
         WHERE spond_subgroup_uids IS NOT NULL
           AND jsonb_array_length(spond_subgroup_uids::jsonb) > 0
        """
    )
    op.drop_column('training_session_types', 'spond_subgroup_uids')
