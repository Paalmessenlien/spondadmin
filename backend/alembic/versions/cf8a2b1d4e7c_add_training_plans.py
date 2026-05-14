"""add training plans

Revision ID: cf8a2b1d4e7c
Revises: ab5d7e2c9f31
Create Date: 2026-05-14 14:00:00.000000

Introduces TrainingPlan: a named period that owns a set of
TrainingSessionTypes. Each plan has its own session-type list so admins
can plan future quarters alongside the current one without name clashes.

Existing data is preserved by auto-creating a single plan named
"Vaktliste 2026" with period bounds derived from `min(date)` /
`max(date)` of existing training_shifts (falling back to today and
today+3 months when there are no shifts), and pointing every existing
training_session_types.plan_id at that plan.

The name-unique constraint on training_session_types.name is dropped
and replaced with a composite unique on (plan_id, name). This is the
change that unlocks importing the same vaktliste shape into multiple
plans (e.g. two consecutive quarters with the same session-type names).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cf8a2b1d4e7c'
down_revision: Union[str, None] = 'ab5d7e2c9f31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) New table.
    op.create_table(
        'training_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'is_active',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
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
        sa.UniqueConstraint('name', name='uq_training_plans_name'),
    )
    op.create_index(
        op.f('ix_training_plans_id'), 'training_plans', ['id'], unique=False
    )

    # 2) Add plan_id to training_session_types (nullable for now so we
    #    can backfill before flipping NOT NULL).
    op.add_column(
        'training_session_types',
        sa.Column('plan_id', sa.Integer(), nullable=True),
    )

    # 3) Backfill: if any session types exist, auto-create a default
    #    "Vaktliste 2026" plan and point every row at it. Period bounds
    #    come from existing shifts when available.
    op.execute(
        """
        INSERT INTO training_plans (name, period_start, period_end, description)
        SELECT 'Vaktliste 2026',
               COALESCE(
                 (SELECT min(date) FROM training_shifts),
                 CURRENT_DATE
               ),
               COALESCE(
                 (SELECT max(date) FROM training_shifts),
                 CURRENT_DATE + INTERVAL '3 months'
               ),
               'Auto-created from pre-multi-plan data.'
        WHERE EXISTS (SELECT 1 FROM training_session_types)
        """
    )
    op.execute(
        """
        UPDATE training_session_types
           SET plan_id = (SELECT id FROM training_plans WHERE name = 'Vaktliste 2026')
         WHERE plan_id IS NULL
        """
    )

    # 4) Lock plan_id NOT NULL + FK + index.
    op.alter_column('training_session_types', 'plan_id', nullable=False)
    op.create_foreign_key(
        'fk_training_session_types_plan_id_training_plans',
        source_table='training_session_types',
        referent_table='training_plans',
        local_cols=['plan_id'],
        remote_cols=['id'],
        ondelete='RESTRICT',
    )
    op.create_index(
        'ix_training_session_types_plan_id',
        'training_session_types',
        ['plan_id'],
    )

    # 5) Swap the name-unique constraint for the composite one.
    # The original constraint name comes from the table definition
    # (UniqueConstraint('name', name='uq_training_session_types_name')).
    op.drop_constraint(
        'uq_training_session_types_name',
        'training_session_types',
        type_='unique',
    )
    op.create_unique_constraint(
        'uq_training_session_types_plan_id_name',
        'training_session_types',
        ['plan_id', 'name'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_training_session_types_plan_id_name',
        'training_session_types',
        type_='unique',
    )
    op.create_unique_constraint(
        'uq_training_session_types_name',
        'training_session_types',
        ['name'],
    )

    op.drop_index(
        'ix_training_session_types_plan_id',
        table_name='training_session_types',
    )
    op.drop_constraint(
        'fk_training_session_types_plan_id_training_plans',
        'training_session_types',
        type_='foreignkey',
    )
    op.drop_column('training_session_types', 'plan_id')

    op.drop_index(op.f('ix_training_plans_id'), table_name='training_plans')
    op.drop_table('training_plans')
