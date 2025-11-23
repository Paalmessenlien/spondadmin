"""
Data migration script to populate event group columns from raw_data.

This script extracts group IDs from the raw_data['recipients'] field and populates:
- primary_group_id: The first group ID (for fast filtering)
- group_ids: Array of all group IDs this event belongs to

Run this script AFTER running the Alembic migration that adds the columns.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.event import Event


async def migrate_event_groups():
    """
    Migrate existing events to populate group columns from raw_data
    """
    async with AsyncSessionLocal() as db:
        # Get all events
        result = await db.execute(select(Event))
        events = result.scalars().all()

        total = len(events)
        updated = 0
        skipped = 0
        errors = 0

        print(f"Found {total} events to process")

        for event in events:
            try:
                # Skip if already populated
                if event.primary_group_id is not None:
                    skipped += 1
                    continue

                # Extract group IDs from raw_data
                group_ids = extract_group_ids(event.raw_data)

                if group_ids:
                    # Set primary_group_id to first group
                    event.primary_group_id = group_ids[0]
                    # Set group_ids to all groups
                    event.group_ids = group_ids
                    updated += 1

                    if updated % 10 == 0:
                        print(f"Processed {updated}/{total} events...")
                else:
                    # No group data found
                    skipped += 1

            except Exception as e:
                print(f"Error processing event {event.spond_id}: {e}")
                errors += 1

        # Commit all changes
        await db.commit()

        print(f"\nMigration complete!")
        print(f"  Total events: {total}")
        print(f"  Updated: {updated}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors: {errors}")


def extract_group_ids(raw_data: dict) -> list:
    """
    Extract group IDs from raw_data dictionary.

    Spond API structure:
    {
        "recipients": {
            "group": {
                "id": "GROUP_ID_HERE",
                ...
            },
            ...
        }
    }

    Args:
        raw_data: The raw_data JSON from Spond API

    Returns:
        List of unique group IDs
    """
    if not raw_data:
        return []

    group_ids = []

    # Try to get recipients from raw_data
    recipients = raw_data.get("recipients")
    if not recipients or not isinstance(recipients, dict):
        return []

    # Extract group ID from recipients dict
    group = recipients.get("group")
    if group and isinstance(group, dict):
        group_id = group.get("id")
        if group_id:
            group_ids.append(group_id)

    return group_ids


if __name__ == "__main__":
    print("=" * 60)
    print("Event Group Data Migration")
    print("=" * 60)
    print()
    print("This script will populate primary_group_id and group_ids")
    print("columns for all events based on their raw_data.")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)

    print()
    asyncio.run(migrate_event_groups())
