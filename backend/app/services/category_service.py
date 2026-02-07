"""
Event Category Service
Handles CRUD operations and pattern matching for event categorization
"""
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.event_category import EventCategory
from app.models.event import Event


class CategoryService:
    """Service for managing event categories"""

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        color: str,
        icon: str,
        pattern_rules: Dict[str, Any],
        priority: int = 100,
        description: Optional[str] = None,
        is_active: bool = True,
        is_default: bool = False,
    ) -> EventCategory:
        """Create a new event category"""
        now = datetime.utcnow()
        category = EventCategory(
            name=name,
            description=description,
            color=color,
            icon=icon,
            pattern_rules=pattern_rules,
            priority=priority,
            is_active=is_active,
            is_default=is_default,
            created_at=now,
            updated_at=now,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update(
        db: AsyncSession,
        category_id: int,
        **kwargs
    ) -> Optional[EventCategory]:
        """Update an existing category"""
        result = await db.execute(
            select(EventCategory).where(EventCategory.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(category, key) and value is not None:
                setattr(category, key, value)

        category.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category_id: int) -> bool:
        """
        Delete a category
        Events with this category will be set to None (uncategorized)
        """
        result = await db.execute(
            select(EventCategory).where(EventCategory.id == category_id)
        )
        category = result.scalar_one_or_none()

        if not category:
            return False

        # Don't allow deleting the default category
        if category.is_default:
            raise ValueError("Cannot delete the default category")

        # Set events' category_id to None
        await db.execute(
            Event.__table__.update()
            .where(Event.category_id == category_id)
            .values(category_id=None)
        )

        await db.delete(category)
        await db.commit()
        return True

    @staticmethod
    async def get_all(
        db: AsyncSession,
        active_only: bool = True
    ) -> List[EventCategory]:
        """Get all categories"""
        query = select(EventCategory).order_by(EventCategory.priority)

        if active_only:
            query = query.where(EventCategory.is_active == True)

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        category_id: int
    ) -> Optional[EventCategory]:
        """Get category by ID"""
        result = await db.execute(
            select(EventCategory).where(EventCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _match_pattern(heading: str, pattern: Dict[str, Any]) -> bool:
        """
        Test if a heading matches a single pattern rule

        Args:
            heading: Event heading to test
            pattern: Pattern dictionary with type, value, and case_insensitive

        Returns:
            True if pattern matches, False otherwise
        """
        pattern_type = pattern.get("type")
        value = pattern.get("value", "")
        case_insensitive = pattern.get("case_insensitive", True)

        test_heading = heading
        test_value = value

        if case_insensitive:
            test_heading = heading.lower()
            test_value = value.lower()

        try:
            if pattern_type == "contains":
                return test_value in test_heading
            elif pattern_type == "starts_with":
                return test_heading.startswith(test_value)
            elif pattern_type == "ends_with":
                return test_heading.endswith(test_value)
            elif pattern_type == "regex":
                flags = re.IGNORECASE if case_insensitive else 0
                return bool(re.search(value, heading, flags))
            else:
                return False
        except Exception:
            # If regex or any pattern fails, return False
            return False

    @staticmethod
    async def match_event_to_category(
        db: AsyncSession,
        event_heading: str
    ) -> Optional[int]:
        """
        Match an event heading to a category based on pattern rules

        Args:
            db: Database session
            event_heading: Event heading to categorize

        Returns:
            Category ID of the first matching category, or default category ID
        """
        # Get all active categories sorted by priority
        categories = await CategoryService.get_all(db, active_only=True)

        # Test each category's patterns
        for category in categories:
            # Skip testing the default category
            if category.is_default:
                continue

            pattern_rules = category.pattern_rules or {}
            patterns = pattern_rules.get("patterns", [])

            # Skip if no patterns
            if not patterns:
                continue

            # Evaluate first pattern
            result = CategoryService._match_pattern(event_heading, patterns[0])

            # Evaluate remaining patterns with AND/OR operators
            for i in range(1, len(patterns)):
                pattern = patterns[i]
                operator = pattern.get("operator", "OR")  # Default to OR
                pattern_matches = CategoryService._match_pattern(event_heading, pattern)

                if operator == "AND":
                    result = result and pattern_matches
                else:  # OR
                    result = result or pattern_matches

            # If the combined result matches, return this category
            if result:
                return category.id

        # No match found, return default category
        default_category = next(
            (cat for cat in categories if cat.is_default),
            None
        )
        return default_category.id if default_category else None

    @staticmethod
    async def categorize_events(
        db: AsyncSession,
        event_ids: Optional[List[int]] = None,
        force_recategorize: bool = False
    ) -> Dict[str, int]:
        """
        Bulk categorize events based on their headings

        Args:
            db: Database session
            event_ids: Specific event IDs to categorize (None = all events)
            force_recategorize: If True, recategorize even if category_override is set

        Returns:
            Dictionary with counts of categorized events
        """
        # Build query
        query = select(Event)

        if event_ids:
            query = query.where(Event.id.in_(event_ids))

        if not force_recategorize:
            # Skip events with manual category override
            query = query.where(Event.category_override == False)

        result = await db.execute(query)
        events = result.scalars().all()

        categorized_count = 0
        unchanged_count = 0

        for event in events:
            # Match event to category
            new_category_id = await CategoryService.match_event_to_category(
                db, event.heading
            )

            # Update if category changed
            if new_category_id and event.category_id != new_category_id:
                event.category_id = new_category_id
                event.updated_at = datetime.utcnow()
                categorized_count += 1
            else:
                unchanged_count += 1

        await db.commit()

        return {
            "total_processed": len(events),
            "categorized": categorized_count,
            "unchanged": unchanged_count,
        }

    @staticmethod
    async def get_category_stats(
        db: AsyncSession,
        group_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get event distribution statistics by category

        Args:
            db: Database session
            group_id: Filter by group (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)

        Returns:
            List of category statistics with counts and percentages
        """
        # Build base query
        query = select(
            EventCategory.id,
            EventCategory.name,
            EventCategory.color,
            EventCategory.icon,
            func.count(Event.id).label("event_count")
        ).outerjoin(
            Event, Event.category_id == EventCategory.id
        )

        # Apply filters to Event
        conditions = []
        if group_id:
            conditions.append(Event.group_id == group_id)
        if start_date:
            conditions.append(Event.start_time >= start_date)
        if end_date:
            conditions.append(Event.start_time <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        # Group by category
        query = query.group_by(
            EventCategory.id,
            EventCategory.name,
            EventCategory.color,
            EventCategory.icon
        ).order_by(func.count(Event.id).desc())

        result = await db.execute(query)
        rows = result.all()

        # Calculate total for percentage
        total_events = sum(row.event_count for row in rows)

        # Build response
        stats = []
        for row in rows:
            percentage = (row.event_count / total_events * 100) if total_events > 0 else 0
            stats.append({
                "category_id": row.id,
                "category_name": row.name,
                "color": row.color,
                "icon": row.icon,
                "event_count": row.event_count,
                "percentage": round(percentage, 2),
            })

        return stats
