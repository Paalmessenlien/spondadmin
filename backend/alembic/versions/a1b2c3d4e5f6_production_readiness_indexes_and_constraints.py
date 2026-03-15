"""Production readiness: indexes, cascade fix, unique constraints

Revision ID: a1b2c3d4e5f6
Revises: 7c46ddbe8345
Create Date: 2026-03-15

Adds performance indexes for frequently queried tables,
changes archer_profiles.spond_id FK from CASCADE to SET NULL,
and adds unique constraints to prevent duplicate data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str = "7c46ddbe8345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Performance indexes ---

    # CompetitionResult: dedup check (archer + event + score)
    op.create_index(
        "ix_cr_archer_event_score",
        "competition_results",
        ["bueskyting_archer_id", "event_name", "score"],
    )

    # CompetitionResult: member results query (spond_id + date)
    op.create_index(
        "ix_cr_spond_date",
        "competition_results",
        ["spond_id", "date"],
    )

    # ArcheryRecord: record browsing (division + category + is_current)
    op.create_index(
        "ix_ar_division_category_current",
        "archery_records",
        ["division", "category", "is_current"],
    )

    # BueskytingScrapeLog: status checks (status + created_at)
    op.create_index(
        "ix_bsl_status_created",
        "bueskyting_scrape_logs",
        ["status", "created_at"],
    )

    # --- Fix ArcherProfile FK cascade ---
    # SQLite doesn't support ALTER CONSTRAINT, so we use batch mode
    with op.batch_alter_table("archer_profiles") as batch_op:
        batch_op.drop_constraint(
            "fk_archer_profiles_spond_id_members", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_archer_profiles_spond_id_members",
            "members",
            ["spond_id"],
            ["spond_id"],
            ondelete="SET NULL",
        )
        batch_op.alter_column("spond_id", nullable=True)


def downgrade() -> None:
    # --- Revert FK cascade ---
    with op.batch_alter_table("archer_profiles") as batch_op:
        batch_op.alter_column("spond_id", nullable=False)
        batch_op.drop_constraint(
            "fk_archer_profiles_spond_id_members", type_="foreignkey"
        )
        batch_op.create_foreign_key(
            "fk_archer_profiles_spond_id_members",
            "members",
            ["spond_id"],
            ["spond_id"],
            ondelete="CASCADE",
        )

    # --- Drop indexes ---
    op.drop_index("ix_bsl_status_created", table_name="bueskyting_scrape_logs")
    op.drop_index("ix_ar_division_category_current", table_name="archery_records")
    op.drop_index("ix_cr_spond_date", table_name="competition_results")
    op.drop_index("ix_cr_archer_event_score", table_name="competition_results")
