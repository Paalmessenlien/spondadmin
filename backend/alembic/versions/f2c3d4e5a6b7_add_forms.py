"""add feedback forms (skjema): forms, form_fields, form_responses, form_answers

Revision ID: f2c3d4e5a6b7
Revises: e1b2c3d4f5a6
Create Date: 2026-06-15 10:00:00.000000

Tally-inspired questionnaire system. Forms own ordered field blocks; responses
hold per-field answers. Forms support logged-in (identity captured) and/or
anonymous public-link submissions. Status: utkast → publisert → lukket.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2c3d4e5a6b7'
down_revision: Union[str, None] = 'e1b2c3d4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'forms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=16), server_default='utkast', nullable=False),
        sa.Column('access_mode', sa.String(length=16), server_default='begge', nullable=False),
        sa.Column('one_response_per_user', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint("status IN ('utkast','publisert','lukket')", name='ck_forms_status'),
        sa.CheckConstraint("access_mode IN ('offentlig','innlogget','begge')", name='ck_forms_access_mode'),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_forms_id'), 'forms', ['id'], unique=False)
    op.create_index('ix_forms_status', 'forms', ['status'], unique=False)
    op.create_index('ix_forms_slug', 'forms', ['slug'], unique=True)

    op.create_table(
        'form_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('field_type', sa.String(length=32), nullable=False),
        sa.Column('label', sa.Text(), nullable=False),
        sa.Column('help_text', sa.Text(), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('options', sa.JSON(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['form_id'], ['forms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_form_fields_id'), 'form_fields', ['id'], unique=False)
    op.create_index('ix_form_fields_form_id', 'form_fields', ['form_id'], unique=False)

    op.create_table(
        'form_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('form_id', sa.Integer(), nullable=False),
        sa.Column('respondent_admin_id', sa.Integer(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('respondent_label', sa.String(length=255), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['form_id'], ['forms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['respondent_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_form_responses_id'), 'form_responses', ['id'], unique=False)
    op.create_index('ix_form_responses_form_id', 'form_responses', ['form_id'], unique=False)

    op.create_table(
        'form_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('response_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('value_text', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['response_id'], ['form_responses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['field_id'], ['form_fields.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_form_answers_id'), 'form_answers', ['id'], unique=False)
    op.create_index('ix_form_answers_response_id', 'form_answers', ['response_id'], unique=False)
    op.create_index('ix_form_answers_field_id', 'form_answers', ['field_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_form_answers_field_id', table_name='form_answers')
    op.drop_index('ix_form_answers_response_id', table_name='form_answers')
    op.drop_index(op.f('ix_form_answers_id'), table_name='form_answers')
    op.drop_table('form_answers')
    op.drop_index('ix_form_responses_form_id', table_name='form_responses')
    op.drop_index(op.f('ix_form_responses_id'), table_name='form_responses')
    op.drop_table('form_responses')
    op.drop_index('ix_form_fields_form_id', table_name='form_fields')
    op.drop_index(op.f('ix_form_fields_id'), table_name='form_fields')
    op.drop_table('form_fields')
    op.drop_index('ix_forms_slug', table_name='forms')
    op.drop_index('ix_forms_status', table_name='forms')
    op.drop_index(op.f('ix_forms_id'), table_name='forms')
    op.drop_table('forms')
