"""add training plan tables

Revision ID: 3c13b72e135d
Revises: e7a91b3c2d10
Create Date: 2026-05-13 10:00:00.000000

Wave 1 of the training-plan feature. Introduces three tables:

- training_session_types: reusable templates (name, default times, location,
  optional Spond subgroup uid).
- training_shifts: per-date occurrences referencing a session type, with an
  optional resolved leader (members.id) or unresolved raw_initials, time
  overrides, status, and Spond publish bookkeeping.
- member_aliases: maps initials -> members.id, used by the importer to resolve
  trainer initials from the vaktliste spreadsheet.

Excel parsing, Spond publishing, and shift CRUD endpoints land in wave 2.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c13b72e135d'
down_revision: Union[str, None] = 'e7a91b3c2d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. training_session_types
    op.create_table(
        'training_session_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('default_start_time', sa.Time(), nullable=False),
        sa.Column('default_end_time', sa.Time(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('spond_subgroup_uid', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_training_session_types_name'),
    )
    op.create_index(
        op.f('ix_training_session_types_id'),
        'training_session_types',
        ['id'],
        unique=False,
    )

    # 2. training_shifts
    op.create_table(
        'training_shifts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_type_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('leader_member_id', sa.Integer(), nullable=True),
        sa.Column('raw_initials', sa.String(length=64), nullable=True),
        sa.Column('start_time_override', sa.Time(), nullable=True),
        sa.Column('end_time_override', sa.Time(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'draft'"),
        ),
        sa.Column('spond_event_id', sa.String(length=255), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['session_type_id'],
            ['training_session_types.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['leader_member_id'],
            ['members.id'],
            ondelete='SET NULL',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'session_type_id',
            'date',
            name='uq_training_shifts_session_type_id_date',
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'cancelled')",
            name='ck_training_shifts_status',
        ),
    )
    op.create_index(
        op.f('ix_training_shifts_id'),
        'training_shifts',
        ['id'],
        unique=False,
    )
    op.create_index(
        'ix_training_shifts_session_type_id',
        'training_shifts',
        ['session_type_id'],
    )
    op.create_index('ix_training_shifts_date', 'training_shifts', ['date'])
    op.create_index(
        'ix_training_shifts_leader_member_id',
        'training_shifts',
        ['leader_member_id'],
    )

    # 3. member_aliases
    op.create_table(
        'member_aliases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('initials', sa.String(length=16), nullable=False),
        sa.Column(
            'source',
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'manual'"),
        ),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ['member_id'],
            ['members.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('initials', name='uq_member_aliases_initials'),
    )
    op.create_index(op.f('ix_member_aliases_id'), 'member_aliases', ['id'], unique=False)
    op.create_index('ix_member_aliases_member_id', 'member_aliases', ['member_id'])
    op.create_index('ix_member_aliases_initials', 'member_aliases', ['initials'])


def downgrade() -> None:
    op.drop_index('ix_member_aliases_initials', table_name='member_aliases')
    op.drop_index('ix_member_aliases_member_id', table_name='member_aliases')
    op.drop_index(op.f('ix_member_aliases_id'), table_name='member_aliases')
    op.drop_table('member_aliases')

    op.drop_index('ix_training_shifts_leader_member_id', table_name='training_shifts')
    op.drop_index('ix_training_shifts_date', table_name='training_shifts')
    op.drop_index('ix_training_shifts_session_type_id', table_name='training_shifts')
    op.drop_index(op.f('ix_training_shifts_id'), table_name='training_shifts')
    op.drop_table('training_shifts')

    op.drop_index(op.f('ix_training_session_types_id'), table_name='training_session_types')
    op.drop_table('training_session_types')
