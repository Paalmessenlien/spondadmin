"""add per-user module allow-list (admins.modules)

Revision ID: a7d3e9f1c2b4
Revises: b4c5d6e7f8a9
Create Date: 2026-07-14 12:00:00.000000

Adds a nullable JSON ``modules`` column to ``admins``. NULL means the
user's module access is not customised and falls back to the role's
default set (see app/core/modules.py), so all pre-existing users keep
working exactly as before. A non-null list is an explicit allow-list of
sidebar modules the user may reach.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7d3e9f1c2b4'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('admins', sa.Column('modules', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('admins', 'modules')
