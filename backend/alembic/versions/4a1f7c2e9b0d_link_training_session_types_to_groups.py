"""link training session types to groups

Revision ID: 4a1f7c2e9b0d
Revises: 3c13b72e135d
Create Date: 2026-05-13 12:00:00.000000

Adds a nullable `group_id` FK on `training_session_types` pointing at
`groups.id` (ON DELETE SET NULL). Existing rows are backfilled with the id of
the largest group (by member count) — that matches the implicit behavior the
publish service had before this change. Rows where no group can be found
(empty database) remain NULL and the publish service keeps its fallback.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a1f7c2e9b0d'
down_revision: Union[str, None] = '3c13b72e135d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_session_types',
        sa.Column('group_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_training_session_types_group_id_groups',
        source_table='training_session_types',
        referent_table='groups',
        local_cols=['group_id'],
        remote_cols=['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_training_session_types_group_id',
        'training_session_types',
        ['group_id'],
    )

    # Backfill: assign every existing training session type to the group with
    # the most members. Mirrors the implicit default in
    # SpondEventCreateService._resolve_group.
    op.execute(
        """
        WITH largest AS (
            SELECT g.id
              FROM groups g
              LEFT JOIN group_members gm ON gm.group_id = g.id
             GROUP BY g.id
             ORDER BY COUNT(gm.member_id) DESC, g.id ASC
             LIMIT 1
        )
        UPDATE training_session_types
           SET group_id = (SELECT id FROM largest)
         WHERE group_id IS NULL
           AND EXISTS (SELECT 1 FROM largest)
        """
    )


def downgrade() -> None:
    op.drop_index(
        'ix_training_session_types_group_id',
        table_name='training_session_types',
    )
    op.drop_constraint(
        'fk_training_session_types_group_id_groups',
        'training_session_types',
        type_='foreignkey',
    )
    op.drop_column('training_session_types', 'group_id')
