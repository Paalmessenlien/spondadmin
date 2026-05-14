"""add leader groups

Revision ID: 7e4a8b6c1d92
Revises: 6d3f9e4b2a58
Create Date: 2026-05-13 15:00:00.000000

Adds:
- `leader_groups`: named pool of members eligible to lead training shifts.
- `leader_group_members`: M2M between leader_groups and members
  (composite PK).
- `training_session_types.leader_group_id`: optional FK; when set, the shift
  editor narrows the leader picker to members of this group.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7e4a8b6c1d92'
down_revision: Union[str, None] = '6d3f9e4b2a58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'leader_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_leader_groups_name'),
    )
    op.create_index(
        op.f('ix_leader_groups_id'),
        'leader_groups',
        ['id'],
        unique=False,
    )

    op.create_table(
        'leader_group_members',
        sa.Column('leader_group_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['leader_group_id'],
            ['leader_groups.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['member_id'],
            ['members.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('leader_group_id', 'member_id'),
    )
    op.create_index(
        'ix_leader_group_members_leader_group_id',
        'leader_group_members',
        ['leader_group_id'],
    )
    op.create_index(
        'ix_leader_group_members_member_id',
        'leader_group_members',
        ['member_id'],
    )

    op.add_column(
        'training_session_types',
        sa.Column('leader_group_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_training_session_types_leader_group_id',
        source_table='training_session_types',
        referent_table='leader_groups',
        local_cols=['leader_group_id'],
        remote_cols=['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_training_session_types_leader_group_id',
        'training_session_types',
        ['leader_group_id'],
    )


def downgrade() -> None:
    op.drop_index(
        'ix_training_session_types_leader_group_id',
        table_name='training_session_types',
    )
    op.drop_constraint(
        'fk_training_session_types_leader_group_id',
        'training_session_types',
        type_='foreignkey',
    )
    op.drop_column('training_session_types', 'leader_group_id')

    op.drop_index(
        'ix_leader_group_members_member_id',
        table_name='leader_group_members',
    )
    op.drop_index(
        'ix_leader_group_members_leader_group_id',
        table_name='leader_group_members',
    )
    op.drop_table('leader_group_members')

    op.drop_index(op.f('ix_leader_groups_id'), table_name='leader_groups')
    op.drop_table('leader_groups')
