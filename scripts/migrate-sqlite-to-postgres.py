#!/usr/bin/env python3
"""
One-time migration script: SQLite → PostgreSQL

Usage:
    1. docker compose up db -d
    2. docker compose run --rm backend alembic upgrade head
    3. python3 scripts/migrate-sqlite-to-postgres.py

The script reads from the local SQLite file and writes to the PostgreSQL
database defined by DATABASE_URL in the environment.
"""
import json
import os
import sqlite3
import sys
from datetime import datetime

import asyncio
import asyncpg


SQLITE_PATH = os.environ.get("SQLITE_PATH", "backend/spond_admin.db")
PG_DSN = os.environ.get(
    "PG_DSN",
    "postgresql://postgres:postgres@localhost:5432/spond_admin",
)

# Tables to migrate (order matters for foreign keys)
TABLES = [
    "admins",
    "groups",
    "members",
    "events",
    "event_categories",
    "archer_profiles",
    "reports",
    "sync_history",
    "audit_logs",
    "competitions",
    "competition_results",
    "archer_statistics",
    "archery_records",
    "bueskyting_scrape_logs",
    "unmatched_archers",
    "scraping_configs",
]


def read_sqlite(db_path: str) -> dict:
    """Read all tables from SQLite."""
    if not os.path.exists(db_path):
        print(f"SQLite file not found: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    data = {}

    for table in TABLES:
        try:
            cursor = conn.execute(f"SELECT * FROM {table}")
            rows = [dict(row) for row in cursor.fetchall()]
            data[table] = rows
            print(f"  Read {len(rows)} rows from {table}")
        except sqlite3.OperationalError as e:
            print(f"  Skipping {table}: {e}")
            data[table] = []

    conn.close()
    return data


def convert_value(value, col_name: str):
    """Convert SQLite values to PostgreSQL-compatible types."""
    if value is None:
        return None

    # Booleans stored as 0/1
    if col_name in ("is_active", "is_superuser", "is_favorite", "active"):
        return bool(value)

    # JSON fields
    if col_name in (
        "raw_data", "responses", "config", "pattern_rules",
        "report_config", "report_data", "backup_metadata",
        "metadata", "results_data", "statistics_data",
    ):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    # Datetime strings
    if col_name in ("created_at", "updated_at", "start_time", "end_time",
                     "last_synced_at", "generated_at", "last_scraped_at",
                     "scraped_at", "matched_at", "dismissed_at",
                     "competition_date"):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                return value

    return value


async def write_postgres(pg_dsn: str, data: dict):
    """Write data to PostgreSQL."""
    conn = await asyncpg.connect(pg_dsn)

    for table in TABLES:
        rows = data.get(table, [])
        if not rows:
            continue

        # Check if table already has data
        count = await conn.fetchval(f"SELECT count(*) FROM {table}")
        if count > 0:
            print(f"  Skipping {table}: already has {count} rows")
            continue

        columns = list(rows[0].keys())
        # Filter out 'alembic_version' if present
        if table == "alembic_version":
            continue

        placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
        col_names = ", ".join(f'"{c}"' for c in columns)
        insert_sql = f'INSERT INTO {table} ({col_names}) VALUES ({placeholders})'

        inserted = 0
        for row in rows:
            values = [convert_value(row[col], col) for col in columns]
            try:
                await conn.execute(insert_sql, *values)
                inserted += 1
            except Exception as e:
                print(f"  Error inserting into {table}: {e}")
                print(f"    Row: {row}")
                continue

        # Reset sequence if table has an id column
        if "id" in columns:
            try:
                max_id = await conn.fetchval(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
                await conn.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), $1, true)",
                    max_id,
                )
            except Exception:
                pass

        print(f"  Inserted {inserted}/{len(rows)} rows into {table}")

    await conn.close()


async def main():
    print(f"SQLite source: {SQLITE_PATH}")
    print(f"PostgreSQL target: {PG_DSN}")
    print()

    print("Reading from SQLite...")
    data = read_sqlite(SQLITE_PATH)

    print()
    print("Writing to PostgreSQL...")
    await write_postgres(PG_DSN, data)

    print()
    print("Migration complete!")


if __name__ == "__main__":
    asyncio.run(main())
