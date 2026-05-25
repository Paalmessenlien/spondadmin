"""add clerk_user_id to admins; make hashed_password nullable

Revision ID: 00eef71933e9
Revises: de3f5c9a8b14
Create Date: 2026-05-22 09:00:00.000000

Adds a nullable, unique ``admins.clerk_user_id`` column that links a
local admin row to a Clerk user. Existing rows keep ``clerk_user_id``
NULL and are linked on the user's first Clerk sign-in by matching
the email address.

Also drops the NOT NULL constraint on ``admins.hashed_password`` so
that admins invited through Clerk (who have no local password) can
exist. The column itself is kept for one release to allow rollback;
a follow-up migration will drop it once the Clerk migration is
stable in production.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '00eef71933e9'
down_revision: Union[str, None] = 'de3f5c9a8b14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'admins',
        sa.Column('clerk_user_id', sa.String(length=255), nullable=True),
    )
    op.create_index(
        'ix_admins_clerk_user_id', 'admins', ['clerk_user_id'], unique=True
    )
    op.alter_column('admins', 'hashed_password', nullable=True)


def downgrade() -> None:
    op.alter_column('admins', 'hashed_password', nullable=False)
    op.drop_index('ix_admins_clerk_user_id', table_name='admins')
    op.drop_column('admins', 'clerk_user_id')
