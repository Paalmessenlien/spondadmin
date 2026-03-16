"""add_external_events

Revision ID: db150f900da8
Revises: 216d0a384f05
Create Date: 2026-03-15 12:57:07.084729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db150f900da8'
down_revision: Union[str, None] = '216d0a384f05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('external_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bueskyting_event_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=500), nullable=False),
    sa.Column('event_type_raw', sa.String(length=100), nullable=True),
    sa.Column('date_start', sa.Date(), nullable=True),
    sa.Column('date_end', sa.Date(), nullable=True),
    sa.Column('location', sa.String(length=500), nullable=True),
    sa.Column('address', sa.String(length=500), nullable=True),
    sa.Column('organizer', sa.String(length=255), nullable=True),
    sa.Column('distance', sa.String(length=100), nullable=True),
    sa.Column('format', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('registration_url', sa.String(length=1000), nullable=True),
    sa.Column('info_url', sa.String(length=1000), nullable=True),
    sa.Column('results_url', sa.String(length=1000), nullable=True),
    sa.Column('registration_deadline', sa.String(length=255), nullable=True),
    sa.Column('registration_type_raw', sa.String(length=255), nullable=True),
    sa.Column('fees', sa.String(length=500), nullable=True),
    sa.Column('contact_email', sa.String(length=255), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('source_url', sa.String(length=1000), nullable=False),
    sa.Column('ai_event_category', sa.String(length=50), nullable=True),
    sa.Column('ai_summary', sa.Text(), nullable=True),
    sa.Column('ai_analyzed_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('bueskyting_event_id')
    )
    op.create_index(op.f('ix_external_events_id'), 'external_events', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_external_events_id'), table_name='external_events')
    op.drop_table('external_events')
