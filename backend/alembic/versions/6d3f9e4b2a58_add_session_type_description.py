"""add description to training_session_types

Revision ID: 6d3f9e4b2a58
Revises: 5c2d8e3a1f47
Create Date: 2026-05-13 14:00:00.000000

Adds a nullable Text `description` column on `training_session_types`. The
publish service composes the Spond event description from
`{leader hint} + {session_type.description} + {location} + {shift.notes}`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6d3f9e4b2a58'
down_revision: Union[str, None] = '5c2d8e3a1f47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'training_session_types',
        sa.Column('description', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('training_session_types', 'description')
