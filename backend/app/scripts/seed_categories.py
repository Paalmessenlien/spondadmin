"""
Seed script for creating default event categories

Usage:
    python -m app.scripts.seed_categories
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.event_category import EventCategory
from datetime import datetime


async def seed_categories():
    """Create default event categories"""

    # Create async engine and session
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    categories = [
        {
            "name": "Training",
            "description": "Training sessions and practice events",
            "color": "#3B82F6",  # Blue
            "icon": "i-heroicons-academic-cap",
            "pattern_rules": {
                "patterns": [
                    {"type": "contains", "value": "trening", "case_insensitive": True}
                ]
            },
            "priority": 10,
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Volunteer Work",
            "description": "Volunteer work and community service events",
            "color": "#10B981",  # Green
            "icon": "i-heroicons-hand-raised",
            "pattern_rules": {
                "patterns": [
                    {"type": "contains", "value": "dugnad", "case_insensitive": True}
                ]
            },
            "priority": 20,
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Match",
            "description": "Matches and competitive events",
            "color": "#EF4444",  # Red
            "icon": "i-heroicons-trophy",
            "pattern_rules": {
                "patterns": [
                    {"type": "contains", "value": "kamp", "case_insensitive": True},
                    {"type": "contains", "value": "match", "case_insensitive": True},
                ]
            },
            "priority": 5,
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Social",
            "description": "Social events and team building activities",
            "color": "#8B5CF6",  # Purple
            "icon": "i-heroicons-user-group",
            "pattern_rules": {
                "patterns": [
                    {"type": "contains", "value": "sosial", "case_insensitive": True},
                    {"type": "contains", "value": "fest", "case_insensitive": True},
                    {"type": "contains", "value": "party", "case_insensitive": True},
                ]
            },
            "priority": 15,
            "is_active": True,
            "is_default": False,
        },
        {
            "name": "Other",
            "description": "Uncategorized events",
            "color": "#6B7280",  # Gray
            "icon": "i-heroicons-ellipsis-horizontal",
            "pattern_rules": {"patterns": []},
            "priority": 999,
            "is_active": True,
            "is_default": True,
        },
    ]

    async with async_session() as session:
        # Check if categories already exist
        from sqlalchemy import select
        result = await session.execute(select(EventCategory))
        existing = result.scalars().all()

        if existing:
            print(f"Found {len(existing)} existing categories. Skipping seed.")
            return

        # Create categories
        print("Creating default categories...")
        now = datetime.utcnow()

        for cat_data in categories:
            category = EventCategory(
                **cat_data,
                created_at=now,
                updated_at=now
            )
            session.add(category)
            print(f"  - Created category: {cat_data['name']}")

        await session.commit()
        print(f"\nSuccessfully created {len(categories)} categories!")

    await engine.dispose()


def main():
    """Run the seed script"""
    print("=" * 60)
    print("Event Categories Seeding Script")
    print("=" * 60)
    print()

    try:
        asyncio.run(seed_categories())
        print("\nSeeding completed successfully!")
    except Exception as e:
        print(f"\nError during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
