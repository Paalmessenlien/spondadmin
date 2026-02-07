"""add_pattern_operators

Revision ID: 8cf7cfe58fe5
Revises: 97f6a876630a
Create Date: 2026-02-07 16:24:18.452074

"""
from typing import Sequence, Union
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cf7cfe58fe5'
down_revision: Union[str, None] = '97f6a876630a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add default 'OR' operators to existing multi-pattern categories"""
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, pattern_rules FROM event_categories"))

    for row in result:
        category_id = row[0]
        pattern_rules = json.loads(row[1]) if row[1] else {"patterns": []}
        patterns = pattern_rules.get("patterns", [])

        # Add "OR" operator to patterns after the first
        if len(patterns) > 1:
            modified = False
            for i in range(1, len(patterns)):
                if "operator" not in patterns[i]:
                    patterns[i]["operator"] = "OR"
                    modified = True

            if modified:
                pattern_rules["patterns"] = patterns
                conn.execute(
                    sa.text("UPDATE event_categories SET pattern_rules = :rules WHERE id = :id"),
                    {"rules": json.dumps(pattern_rules), "id": category_id}
                )


def downgrade() -> None:
    """Remove operator fields from pattern rules"""
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, pattern_rules FROM event_categories"))

    for row in result:
        category_id = row[0]
        pattern_rules = json.loads(row[1]) if row[1] else {"patterns": []}
        patterns = pattern_rules.get("patterns", [])

        # Remove "operator" field from all patterns
        if patterns:
            modified = False
            for pattern in patterns:
                if "operator" in pattern:
                    del pattern["operator"]
                    modified = True

            if modified:
                pattern_rules["patterns"] = patterns
                conn.execute(
                    sa.text("UPDATE event_categories SET pattern_rules = :rules WHERE id = :id"),
                    {"rules": json.dumps(pattern_rules), "id": category_id}
                )
