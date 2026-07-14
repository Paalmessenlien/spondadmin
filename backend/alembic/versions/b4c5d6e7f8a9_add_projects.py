"""add Prosjekter: projects, states, labels, cycles, modules, work items + children

Revision ID: b4c5d6e7f8a9
Revises: f2c3d4e5a6b7
Create Date: 2026-07-12 10:00:00.000000

Plane-like project management (Prosjekter). Projects own board states,
labels, cycles and modules; work items carry priority, dates, a
self-referential parent, assignees/subscribers (free-text names with
optional fuzzy-matched member/admin refs), comments, links and relations.
State-group and priority vocabularies are kept Plane-compatible (English
tokens) so Plane exports import losslessly; the unique
(project_id, sequence_id) key makes re-imports idempotent.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, None] = 'f2c3d4e5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('identifier', sa.String(length=12), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('last_sequence_id', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_archived', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index('ix_projects_identifier', 'projects', ['identifier'], unique=True)

    op.create_table(
        'project_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('state_group', sa.String(length=16), server_default='unstarted', nullable=False),
        sa.Column('color', sa.String(length=7), server_default='#9CA3AF', nullable=False),
        sa.Column('position', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='0', nullable=False),
        sa.CheckConstraint(
            "state_group IN ('backlog','unstarted','started','completed','cancelled')",
            name='ck_project_states_group',
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_project_states_project_name'),
    )
    op.create_index(op.f('ix_project_states_id'), 'project_states', ['id'], unique=False)
    op.create_index('ix_project_states_project_id', 'project_states', ['project_id'], unique=False)

    op.create_table(
        'project_labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), server_default='#6B7280', nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_project_labels_project_name'),
    )
    op.create_index(op.f('ix_project_labels_id'), 'project_labels', ['id'], unique=False)
    op.create_index('ix_project_labels_project_id', 'project_labels', ['project_id'], unique=False)

    op.create_table(
        'project_cycles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_project_cycles_project_name'),
    )
    op.create_index(op.f('ix_project_cycles_id'), 'project_cycles', ['id'], unique=False)
    op.create_index('ix_project_cycles_project_id', 'project_cycles', ['project_id'], unique=False)

    op.create_table(
        'project_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'name', name='uq_project_modules_project_name'),
    )
    op.create_index(op.f('ix_project_modules_id'), 'project_modules', ['id'], unique=False)
    op.create_index('ix_project_modules_project_id', 'project_modules', ['project_id'], unique=False)

    op.create_table(
        'work_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('sequence_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('state_id', sa.Integer(), nullable=True),
        sa.Column('priority', sa.String(length=8), server_default='none', nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('estimate', sa.String(length=32), nullable=True),
        sa.Column('is_draft', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('sort_order', sa.Float(), server_default='0', nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.CheckConstraint(
            "priority IN ('none','low','medium','high','urgent')",
            name='ck_work_items_priority',
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['state_id'], ['project_states.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parent_id'], ['work_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'sequence_id', name='uq_work_items_project_seq'),
    )
    op.create_index(op.f('ix_work_items_id'), 'work_items', ['id'], unique=False)
    op.create_index('ix_work_items_project_id', 'work_items', ['project_id'], unique=False)
    op.create_index('ix_work_items_state_id', 'work_items', ['state_id'], unique=False)
    op.create_index('ix_work_items_parent_id', 'work_items', ['parent_id'], unique=False)

    op.create_table(
        'work_item_labels',
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('label_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['label_id'], ['project_labels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('work_item_id', 'label_id'),
    )

    op.create_table(
        'work_item_cycles',
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cycle_id'], ['project_cycles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('work_item_id', 'cycle_id'),
    )

    op.create_table(
        'work_item_modules',
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['project_modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('work_item_id', 'module_id'),
    )

    op.create_table(
        'work_item_people',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=12), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('match_confidence', sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "kind IN ('assignee','subscriber')", name='ck_work_item_people_kind',
        ),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'work_item_id', 'kind', 'display_name',
            name='uq_work_item_people_item_kind_name',
        ),
    )
    op.create_index(op.f('ix_work_item_people_id'), 'work_item_people', ['id'], unique=False)
    op.create_index('ix_work_item_people_work_item_id', 'work_item_people', ['work_item_id'], unique=False)

    op.create_table(
        'work_item_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_by_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['admins.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_work_item_comments_id'), 'work_item_comments', ['id'], unique=False)
    op.create_index('ix_work_item_comments_work_item_id', 'work_item_comments', ['work_item_id'], unique=False)

    op.create_table(
        'work_item_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_work_item_links_id'), 'work_item_links', ['id'], unique=False)
    op.create_index('ix_work_item_links_work_item_id', 'work_item_links', ['work_item_id'], unique=False)

    op.create_table(
        'work_item_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('work_item_id', sa.Integer(), nullable=False),
        sa.Column('relation_type', sa.String(length=16), server_default='relates_to', nullable=False),
        sa.Column('direction', sa.String(length=8), server_default='outgoing', nullable=False),
        sa.Column('related_identifier', sa.String(length=32), nullable=False),
        sa.Column('related_work_item_id', sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "relation_type IN ('relates_to','blocks','blocked_by','duplicate')",
            name='ck_work_item_relations_type',
        ),
        sa.CheckConstraint(
            "direction IN ('outgoing','incoming')",
            name='ck_work_item_relations_direction',
        ),
        sa.ForeignKeyConstraint(['work_item_id'], ['work_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_work_item_id'], ['work_items.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'work_item_id', 'relation_type', 'direction', 'related_identifier',
            name='uq_work_item_relations_key',
        ),
    )
    op.create_index(op.f('ix_work_item_relations_id'), 'work_item_relations', ['id'], unique=False)
    op.create_index('ix_work_item_relations_work_item_id', 'work_item_relations', ['work_item_id'], unique=False)
    op.create_index('ix_work_item_relations_related_id', 'work_item_relations', ['related_work_item_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_work_item_relations_related_id', table_name='work_item_relations')
    op.drop_index('ix_work_item_relations_work_item_id', table_name='work_item_relations')
    op.drop_index(op.f('ix_work_item_relations_id'), table_name='work_item_relations')
    op.drop_table('work_item_relations')
    op.drop_index('ix_work_item_links_work_item_id', table_name='work_item_links')
    op.drop_index(op.f('ix_work_item_links_id'), table_name='work_item_links')
    op.drop_table('work_item_links')
    op.drop_index('ix_work_item_comments_work_item_id', table_name='work_item_comments')
    op.drop_index(op.f('ix_work_item_comments_id'), table_name='work_item_comments')
    op.drop_table('work_item_comments')
    op.drop_index('ix_work_item_people_work_item_id', table_name='work_item_people')
    op.drop_index(op.f('ix_work_item_people_id'), table_name='work_item_people')
    op.drop_table('work_item_people')
    op.drop_table('work_item_modules')
    op.drop_table('work_item_cycles')
    op.drop_table('work_item_labels')
    op.drop_index('ix_work_items_parent_id', table_name='work_items')
    op.drop_index('ix_work_items_state_id', table_name='work_items')
    op.drop_index('ix_work_items_project_id', table_name='work_items')
    op.drop_index(op.f('ix_work_items_id'), table_name='work_items')
    op.drop_table('work_items')
    op.drop_index('ix_project_modules_project_id', table_name='project_modules')
    op.drop_index(op.f('ix_project_modules_id'), table_name='project_modules')
    op.drop_table('project_modules')
    op.drop_index('ix_project_cycles_project_id', table_name='project_cycles')
    op.drop_index(op.f('ix_project_cycles_id'), table_name='project_cycles')
    op.drop_table('project_cycles')
    op.drop_index('ix_project_labels_project_id', table_name='project_labels')
    op.drop_index(op.f('ix_project_labels_id'), table_name='project_labels')
    op.drop_table('project_labels')
    op.drop_index('ix_project_states_project_id', table_name='project_states')
    op.drop_index(op.f('ix_project_states_id'), table_name='project_states')
    op.drop_table('project_states')
    op.drop_index('ix_projects_identifier', table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
