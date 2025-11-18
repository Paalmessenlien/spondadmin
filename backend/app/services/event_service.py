"""
Event service for CRUD operations
"""
from typing import Optional, List, Tuple
from datetime import datetime, timezone
import logging

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.schemas.event import EventUpdate, EventFilters
from app.services.spond_service import SpondService

logger = logging.getLogger(__name__)


class EventService:
    """
    Service for event CRUD operations
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, event_id: int) -> Optional[Event]:
        """
        Get event by database ID

        Args:
            db: Database session
            event_id: Event ID

        Returns:
            Event or None
        """
        result = await db.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_spond_id(db: AsyncSession, spond_id: str) -> Optional[Event]:
        """
        Get event by Spond ID

        Args:
            db: Database session
            spond_id: Spond event ID

        Returns:
            Event or None
        """
        result = await db.execute(
            select(Event).where(Event.spond_id == spond_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        filters: Optional[EventFilters] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "start_time",
        order_desc: bool = True,
    ) -> Tuple[List[Event], int]:
        """
        Get all events with filtering and pagination

        Args:
            db: Database session
            filters: Optional filters
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by
            order_desc: Order descending if True

        Returns:
            Tuple of (list of events, total count)
        """
        # Build query
        query = select(Event)
        count_query = select(func.count(Event.id))

        # Apply filters
        if filters:
            conditions = EventService._build_filter_conditions(filters)
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply ordering
        order_column = getattr(Event, order_by, Event.start_time)
        if order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute query
        result = await db.execute(query)
        events = list(result.scalars().all())

        return events, total

    @staticmethod
    def _build_filter_conditions(filters: EventFilters) -> List:
        """
        Build filter conditions from EventFilters

        Args:
            filters: Event filters

        Returns:
            List of SQLAlchemy filter conditions
        """
        conditions = []

        # Filter by event type
        if filters.event_type:
            conditions.append(Event.event_type == filters.event_type)

        # Include/exclude cancelled
        if not filters.include_cancelled:
            conditions.append(Event.cancelled.is_(False))

        # Include/exclude hidden
        if not filters.include_hidden:
            conditions.append(Event.hidden.is_(False))

        # Filter by date range
        if filters.start_date:
            conditions.append(Event.start_time >= filters.start_date)

        if filters.end_date:
            conditions.append(Event.start_time <= filters.end_date)

        # Search in heading or description
        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(
                    Event.heading.ilike(search_term),
                    Event.description.ilike(search_term)
                )
            )

        return conditions

    @staticmethod
    async def update(
        db: AsyncSession,
        event_id: int,
        update_data: EventUpdate,
        spond_service: Optional[SpondService] = None,
    ) -> Optional[Event]:
        """
        Update an event

        Args:
            db: Database session
            event_id: Event ID
            update_data: Update data
            spond_service: Optional Spond service for API updates

        Returns:
            Updated event or None if not found
        """
        event = await EventService.get_by_id(db, event_id)
        if not event:
            return None

        # Update local fields
        if update_data.heading is not None:
            event.heading = update_data.heading

        if update_data.description is not None:
            event.description = update_data.description

        if update_data.cancelled is not None:
            event.cancelled = update_data.cancelled

        if update_data.hidden is not None:
            event.hidden = update_data.hidden

        # Update in Spond API if service provided
        if spond_service:
            try:
                updates = {}
                if update_data.heading is not None:
                    updates["heading"] = update_data.heading
                if update_data.description is not None:
                    updates["description"] = update_data.description

                if updates:
                    await spond_service.update_event(event.spond_id, updates)
                    logger.info(f"Updated event {event.spond_id} in Spond API")

            except Exception as e:
                logger.error(f"Failed to update event in Spond API: {e}")
                # Continue with local update even if Spond update fails

        await db.flush()
        await db.refresh(event)

        return event

    @staticmethod
    async def delete(db: AsyncSession, event_id: int) -> bool:
        """
        Delete an event from database (local only, not from Spond)

        Args:
            db: Database session
            event_id: Event ID

        Returns:
            True if deleted, False if not found
        """
        event = await EventService.get_by_id(db, event_id)
        if not event:
            return False

        await db.delete(event)
        await db.flush()

        return True

    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        filters: Optional[EventFilters] = None
    ) -> dict:
        """
        Get event statistics

        Args:
            db: Database session
            filters: Optional filters

        Returns:
            Dictionary with statistics
        """
        now = datetime.now(timezone.utc)

        # Base query conditions
        conditions = []
        if filters:
            conditions = EventService._build_filter_conditions(filters)

        # Total events
        total_query = select(func.count(Event.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await db.execute(total_query)
        total_events = total_result.scalar()

        # Upcoming events
        upcoming_query = select(func.count(Event.id)).where(Event.start_time >= now)
        if conditions:
            upcoming_query = upcoming_query.where(and_(*conditions))
        upcoming_result = await db.execute(upcoming_query)
        upcoming_events = upcoming_result.scalar()

        # Past events
        past_events = total_events - upcoming_events

        # Cancelled events
        cancelled_query = select(func.count(Event.id)).where(Event.cancelled.is_(True))
        if conditions:
            cancelled_query = cancelled_query.where(and_(*conditions))
        cancelled_result = await db.execute(cancelled_query)
        cancelled_events = cancelled_result.scalar()

        # Events by type
        type_query = select(Event.event_type, func.count(Event.id)).group_by(Event.event_type)
        if conditions:
            type_query = type_query.where(and_(*conditions))
        type_result = await db.execute(type_query)
        events_by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "total_events": total_events,
            "upcoming_events": upcoming_events,
            "past_events": past_events,
            "cancelled_events": cancelled_events,
            "events_by_type": events_by_type,
        }

    @staticmethod
    async def get_attendance_export(
        db: AsyncSession,
        event_id: int,
        spond_service: SpondService
    ) -> bytes:
        """
        Get attendance export for an event as Excel file

        Args:
            db: Database session
            event_id: Event ID
            spond_service: Spond service instance

        Returns:
            Excel file bytes

        Raises:
            ValueError: If event not found
        """
        event = await EventService.get_by_id(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        # Get attendance from Spond API
        xlsx_data = await spond_service.get_event_attendance_xlsx(event.spond_id)

        return xlsx_data

    @staticmethod
    async def update_response(
        db: AsyncSession,
        event_id: int,
        user_id: str,
        response_type: str,
        spond_service: SpondService
    ) -> Optional[Event]:
        """
        Update a user's response to an event

        Args:
            db: Database session
            event_id: Event ID
            user_id: User ID
            response_type: Response type (accepted, declined, etc.)
            spond_service: Spond service instance

        Returns:
            Updated event or None if not found
        """
        event = await EventService.get_by_id(db, event_id)
        if not event:
            return None

        # Update response in Spond API
        try:
            await spond_service.change_event_response(
                event.spond_id,
                user_id,
                response_type
            )

            logger.info(
                f"Updated response for user {user_id} on event {event.spond_id} "
                f"to {response_type}"
            )

            # Note: The response in the database will be updated on next sync
            # For immediate update, we could fetch the event again from Spond

        except Exception as e:
            logger.error(f"Failed to update response in Spond API: {e}")
            raise

        return event
