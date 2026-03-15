"""Add role column to admins table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = '7c46ddbe8345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column with server_default so existing rows get a value
    op.add_column('admins', sa.Column('role', sa.String(20), nullable=False, server_default='viewer'))

    # Migrate existing data: superusers become admin, others become editor
    op.execute("UPDATE admins SET role = 'admin' WHERE is_superuser = 1")
    op.execute("UPDATE admins SET role = 'editor' WHERE is_superuser = 0")


def downgrade() -> None:
    op.drop_column('admins', 'role')
