"""add access groups + editable role defaults

Revision ID: b8e4f0a2d6c1
Revises: a7d3e9f1c2b4
Create Date: 2026-07-14 13:00:00.000000

Adds:
  * ``access_groups`` — reusable {role + modules} bundles.
  * ``role_module_defaults`` — editable per-role default module sets, seeded
    from the code constants (editor/viewer/kasserer; admin always gets all).
  * ``admins.access_group_id`` — optional FK, SET NULL on group delete.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8e4f0a2d6c1'
down_revision: Union[str, None] = 'a7d3e9f1c2b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Seed values — kept in sync with app.core.modules.SEED_ROLE_DEFAULT_MODULES.
_ROLE_DEFAULT_SEED = {
    "viewer": ["competitions", "dashboard", "events", "members", "projects", "reports", "scores"],
    "editor": ["analytics", "competitions", "dashboard", "events", "expenses", "forms",
               "members", "projects", "reports", "scores", "training"],
    "kasserer": ["dashboard", "expenses", "members"],
}


def upgrade() -> None:
    op.create_table(
        'access_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='viewer', nullable=False),
        sa.Column('modules', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_access_groups_id', 'access_groups', ['id'])
    op.create_index('ix_access_groups_name', 'access_groups', ['name'], unique=True)

    op.create_table(
        'role_module_defaults',
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('modules', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('role'),
    )

    op.add_column(
        'admins',
        sa.Column('access_group_id', sa.Integer(), nullable=True),
    )
    op.create_index('ix_admins_access_group_id', 'admins', ['access_group_id'])
    op.create_foreign_key(
        'fk_admins_access_group_id', 'admins', 'access_groups',
        ['access_group_id'], ['id'], ondelete='SET NULL',
    )

    # Seed the editable role defaults.
    role_defaults = sa.table(
        'role_module_defaults',
        sa.column('role', sa.String),
        sa.column('modules', sa.JSON),
    )
    op.bulk_insert(
        role_defaults,
        [{"role": role, "modules": mods} for role, mods in _ROLE_DEFAULT_SEED.items()],
    )


def downgrade() -> None:
    op.drop_constraint('fk_admins_access_group_id', 'admins', type_='foreignkey')
    op.drop_index('ix_admins_access_group_id', table_name='admins')
    op.drop_column('admins', 'access_group_id')
    op.drop_table('role_module_defaults')
    op.drop_index('ix_access_groups_name', table_name='access_groups')
    op.drop_index('ix_access_groups_id', table_name='access_groups')
    op.drop_table('access_groups')
