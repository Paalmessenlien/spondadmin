"""add_ai_provider_config

Revision ID: 216d0a384f05
Revises: 8e1995483a3e
Create Date: 2026-03-15 12:00:57.219189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '216d0a384f05'
down_revision: Union[str, None] = '8e1995483a3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ai_provider_config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('display_name', sa.String(length=100), nullable=False),
    sa.Column('api_key_encrypted', sa.Text(), nullable=True),
    sa.Column('base_url', sa.String(length=500), nullable=True),
    sa.Column('default_model', sa.String(length=100), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('last_tested_at', sa.DateTime(), nullable=True),
    sa.Column('test_status', sa.String(length=20), nullable=True),
    sa.Column('test_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('provider')
    )
    op.create_index(op.f('ix_ai_provider_config_id'), 'ai_provider_config', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_provider_config_id'), table_name='ai_provider_config')
    op.drop_table('ai_provider_config')
