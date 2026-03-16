"""
External Event Service - CRUD operations for external events
"""
from typing import Optional, List, Tuple
from datetime import date

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.external_event import ExternalEvent
from app.schemas.external_event import ExternalEventFilters


class ExternalEventService:
    @staticmethod
    async def get_events(
        db: AsyncSession, filters: ExternalEventFilters
    ) -> Tuple[List[ExternalEvent], int]:
        """Get external events with filtering and pagination."""
        conditions = []

        if filters.search:
            search = f"%{filters.search}%"
            conditions.append(or_(
                ExternalEvent.name.ilike(search),
                ExternalEvent.organizer.ilike(search),
                ExternalEvent.location.ilike(search),
            ))

        if filters.date_from:
            conditions.append(ExternalEvent.date_start >= filters.date_from)
        if filters.date_to:
            conditions.append(ExternalEvent.date_start <= filters.date_to)
        if filters.ai_event_category:
            conditions.append(ExternalEvent.ai_event_category == filters.ai_event_category)
        if filters.is_active is not None:
            conditions.append(ExternalEvent.is_active == filters.is_active)

        # Count
        count_query = select(func.count(ExternalEvent.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = (await db.execute(count_query)).scalar() or 0

        # Query
        query = select(ExternalEvent)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(ExternalEvent.date_start.asc().nullslast())
        query = query.offset(filters.skip).limit(filters.limit)

        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_event_by_id(db: AsyncSession, event_id: int) -> Optional[ExternalEvent]:
        """Get a single external event by ID."""
        result = await db.execute(
            select(ExternalEvent).where(ExternalEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_upcoming_events(db: AsyncSession, limit: int = 10) -> List[ExternalEvent]:
        """Get upcoming active events."""
        today = date.today()
        result = await db.execute(
            select(ExternalEvent)
            .where(and_(
                ExternalEvent.is_active == True,
                or_(
                    ExternalEvent.date_start >= today,
                    ExternalEvent.date_start.is_(None),
                ),
            ))
            .order_by(ExternalEvent.date_start.asc().nullslast())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_unanalyzed_events(db: AsyncSession) -> List[ExternalEvent]:
        """Get events that haven't been analyzed by AI yet."""
        result = await db.execute(
            select(ExternalEvent)
            .where(ExternalEvent.ai_analyzed_at.is_(None))
            .order_by(ExternalEvent.date_start.asc().nullslast())
        )
        return result.scalars().all()
