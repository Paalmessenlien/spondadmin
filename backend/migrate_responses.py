#!/usr/bin/env python3
"""
One-time migration: Convert old response format to new format

This script updates all existing events in the database to use
the analytics-compatible response format by adding a "responses"
array constructed from the UID arrays.
"""
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import attributes
from app.db.session import AsyncSessionLocal
from app.models.event import Event


async def migrate():
    """Migrate all existing events to new response format"""

    async with AsyncSessionLocal() as db:
        print("Starting response format migration...")
        print("=" * 60)

        # Fetch all events with responses
        result = await db.execute(
            select(Event).where(Event.responses.isnot(None))
        )
        events = result.scalars().all()

        print(f"Found {len(events)} events with responses to migrate")
        print()

        migrated = 0
        skipped = 0

        for event in events:
            # Skip if already in new format
            if event.responses and "responses" in event.responses:
                skipped += 1
                continue

            # Check if in old format
            if not event.responses:
                skipped += 1
                continue

            old_format = event.responses

            # Build responses array from UID arrays
            responses_array = []

            # Add accepted responses
            for uid in old_format.get("accepted_uids", []):
                responses_array.append({
                    "answer": "accepted",
                    "profile": {"id": uid}
                })

            # Add declined responses
            for uid in old_format.get("declined_uids", []):
                responses_array.append({
                    "answer": "declined",
                    "profile": {"id": uid}
                })

            # Add unanswered responses
            for uid in old_format.get("unanswered_uids", []):
                responses_array.append({
                    "answer": "unanswered",
                    "profile": {"id": uid}
                })

            # Add waiting list responses
            for uid in old_format.get("waiting_list_uids", []):
                responses_array.append({
                    "answer": "waitinglistavailable",
                    "profile": {"id": uid}
                })

            # Add unconfirmed responses
            for uid in old_format.get("unconfirmed_uids", []):
                responses_array.append({
                    "answer": "unconfirmed",
                    "profile": {"id": uid}
                })

            # Update event with new format while keeping old format
            # Must create new dict to trigger SQLAlchemy dirty flag
            new_responses = dict(event.responses)
            new_responses["responses"] = responses_array
            event.responses = new_responses

            # Mark the attribute as modified
            attributes.flag_modified(event, "responses")

            migrated += 1

            # Commit in batches
            if migrated % 100 == 0:
                print(f"Migrated {migrated} events...")
                await db.commit()

        # Final commit
        await db.commit()

        print()
        print("=" * 60)
        print("Migration complete!")
        print("=" * 60)
        print(f"  Migrated:  {migrated:>5} events")
        print(f"  Skipped:   {skipped:>5} events (already in new format)")
        print(f"  Total:     {len(events):>5} events")
        print("=" * 60)

        if migrated > 0:
            print()
            print("✅ Analytics should now show data correctly!")
            print("   You can verify by visiting:")
            print("   http://localhost:3001/dashboard/analytics")


if __name__ == "__main__":
    asyncio.run(migrate())
