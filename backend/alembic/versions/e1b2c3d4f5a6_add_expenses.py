"""add expenses + expense_attachments (utlegg)

Revision ID: e1b2c3d4f5a6
Revises: d9a4f2c61b85
Create Date: 2026-06-02 09:00:00.000000

Expense reimbursements (utlegg) submitted to the kasserer, with receipt
attachments stored on Bunny CDN. Standalone expenses, status lifecycle
utkast → sendt → godkjent/avvist → utbetalt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1b2c3d4f5a6'
down_revision: Union[str, None] = 'd9a4f2c61b85'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('submitter_admin_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), server_default='NOK', nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=True),
        sa.Column('payee_name', sa.String(length=255), nullable=True),
        sa.Column('bank_account', sa.String(length=40), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), server_default='utkast', nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by_admin_id', sa.Integer(), nullable=True),
        sa.Column('kasserer_note', sa.Text(), nullable=True),
        sa.Column('ai_extracted', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint(
            "status IN ('utkast','sendt','godkjent','avvist','utbetalt')",
            name='ck_expenses_status',
        ),
        sa.ForeignKeyConstraint(['submitter_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by_admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_expenses_id'), 'expenses', ['id'], unique=False)
    op.create_index('ix_expenses_status', 'expenses', ['status'], unique=False)
    op.create_index('ix_expenses_submitter_admin_id', 'expenses', ['submitter_admin_id'], unique=False)

    op.create_table(
        'expense_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('cdn_path', sa.String(length=500), nullable=False),
        sa.Column('cdn_url', sa.String(length=700), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('ai_suggestions', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['expense_id'], ['expenses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_expense_attachments_id'), 'expense_attachments', ['id'], unique=False)
    op.create_index('ix_expense_attachments_expense_id', 'expense_attachments', ['expense_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_expense_attachments_expense_id', table_name='expense_attachments')
    op.drop_index(op.f('ix_expense_attachments_id'), table_name='expense_attachments')
    op.drop_table('expense_attachments')
    op.drop_index('ix_expenses_submitter_admin_id', table_name='expenses')
    op.drop_index('ix_expenses_status', table_name='expenses')
    op.drop_index(op.f('ix_expenses_id'), table_name='expenses')
    op.drop_table('expenses')
