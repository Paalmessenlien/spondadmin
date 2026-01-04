"""
Event service for CRUD operations
"""
from typing import Optional, List, Tuple
from datetime import datetime, timezone
import logging

from sqlalchemy import select, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.member import Member
from app.schemas.event import EventCreate, EventUpdate, EventFilters
from app.services.spond_service import SpondService
import uuid

logger = logging.getLogger(__name__)


class EventService:
    """
    Service for event CRUD operations
    """

    @staticmethod
    async def get_by_id(db: AsyncSession, event_id: int, enrich_responses: bool = False) -> Optional[Event]:
        """
        Get event by database ID

        Args:
            db: Database session
            event_id: Event ID
            enrich_responses: If True, enrich responses with member profile data

        Returns:
            Event or None
        """
        result = await db.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()

        if event and enrich_responses:
            event = await EventService._enrich_event_responses(db, event)

        return event

    @staticmethod
    async def _enrich_event_responses(db: AsyncSession, event: Event) -> Event:
        """
        Enrich event responses with member profile data from the members table.

        Args:
            db: Database session
            event: Event to enrich

        Returns:
            Event with enriched responses
        """
        if not event.responses:
            return event

        # Collect all member IDs from responses
        member_ids = set()
        responses_array = event.responses.get("responses", [])

        for response in responses_array:
            profile = response.get("profile", {})
            if profile and profile.get("id"):
                member_ids.add(profile["id"])

        if not member_ids:
            return event

        # Fetch member data from database
        result = await db.execute(
            select(Member).where(Member.spond_id.in_(member_ids))
        )
        members = {m.spond_id: m for m in result.scalars().all()}

        # Enrich responses with member data
        enriched_responses = []
        for response in responses_array:
            profile = response.get("profile", {})
            member_id = profile.get("id") if profile else None

            if member_id and member_id in members:
                member = members[member_id]
                enriched_profile = {
                    "id": member_id,
                    "firstName": member.first_name,
                    "lastName": member.last_name,
                    "email": member.email,
                }
            else:
                enriched_profile = profile

            enriched_responses.append({
                "answer": response.get("answer"),
                "profile": enriched_profile,
            })

        # Create enriched responses dict
        enriched = dict(event.responses)
        enriched["responses"] = enriched_responses
        event.responses = enriched

        return event

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

        # Include/exclude archived (events where end_time has passed)
        if not filters.include_archived:
            conditions.append(Event.end_time >= datetime.utcnow())

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

        # Filter by group_id (stored in raw_data JSON as recipients.group.id)
        if filters.group_id:
            conditions.append(
                text("json_extract(raw_data, '$.recipients.group.id') = :group_id").bindparams(group_id=filters.group_id)
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

        # Track if any changes were made
        has_changes = False

        # Update local fields
        if update_data.heading is not None:
            event.heading = update_data.heading
            has_changes = True

        if update_data.description is not None:
            event.description = update_data.description
            has_changes = True

        if update_data.start_time is not None:
            event.start_time = update_data.start_time
            has_changes = True

        if update_data.end_time is not None:
            event.end_time = update_data.end_time
            has_changes = True

        if update_data.location_address is not None:
            event.location_address = update_data.location_address
            has_changes = True

        if update_data.location_latitude is not None:
            event.location_latitude = update_data.location_latitude
            has_changes = True

        if update_data.location_longitude is not None:
            event.location_longitude = update_data.location_longitude
            has_changes = True

        if update_data.max_accepted is not None:
            event.max_accepted = update_data.max_accepted
            has_changes = True

        if update_data.cancelled is not None:
            event.cancelled = update_data.cancelled
            has_changes = True

        if update_data.hidden is not None:
            event.hidden = update_data.hidden
            has_changes = True

        # Update sync status
        if has_changes:
            if update_data.sync_to_spond and spond_service and event.sync_status != "local_only":
                # Sync immediately to Spond
                try:
                    await EventService.push_to_spond(db, event_id, spond_service)
                except Exception as e:
                    logger.error(f"Failed to sync event to Spond: {e}")
                    event.sync_status = "error"
                    event.sync_error = str(e)
            elif event.sync_status == "synced":
                # Mark as pending if not syncing immediately
                event.sync_status = "pending"

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
    async def create(
        db: AsyncSession,
        create_data: EventCreate,
        spond_service: Optional[SpondService] = None,
    ) -> Event:
        """
        Create a new event

        Args:
            db: Database session
            create_data: Event creation data
            spond_service: Optional Spond service for API sync

        Returns:
            Created event
        """
        now = datetime.utcnow()

        # Generate a temporary spond_id for local-only events
        temp_spond_id = f"local_{uuid.uuid4().hex[:12]}"

        # Determine initial sync status
        sync_status = "local_only"
        spond_id = temp_spond_id

        # Create event in Spond if requested
        if create_data.sync_to_spond and spond_service:
            try:
                # Prepare event data for Spond API
                spond_data = {
                    "heading": create_data.heading,
                    "description": create_data.description or "",
                    "spondType": create_data.event_type,
                    "startTimestamp": create_data.start_time.isoformat(),
                    "endTimestamp": create_data.end_time.isoformat(),
                }

                # Add location if provided
                if create_data.location_address:
                    spond_data["location"] = {
                        "address": create_data.location_address,
                        "latitude": create_data.location_latitude,
                        "longitude": create_data.location_longitude,
                    }

                # Add max participants if set
                if create_data.max_accepted > 0:
                    spond_data["maxAccepted"] = create_data.max_accepted

                # Create in Spond
                result = await spond_service.create_event(spond_data)
                spond_id = result.get("id", temp_spond_id)
                sync_status = "synced"
                logger.info(f"Created event in Spond: {spond_id}")

            except Exception as e:
                logger.error(f"Failed to create event in Spond: {e}")
                sync_status = "error"
                # Continue with local creation

        # Build raw_data with group info if provided
        raw_data = None
        if create_data.group_id:
            raw_data = {
                "recipients": {
                    "group": {
                        "id": create_data.group_id
                    }
                }
            }

        # Create local event record
        event = Event(
            spond_id=spond_id,
            heading=create_data.heading,
            description=create_data.description,
            event_type=create_data.event_type,
            start_time=create_data.start_time,
            end_time=create_data.end_time,
            created_time=now,
            invite_time=None,
            location_address=create_data.location_address,
            location_latitude=create_data.location_latitude,
            location_longitude=create_data.location_longitude,
            max_accepted=create_data.max_accepted,
            cancelled=create_data.cancelled,
            hidden=create_data.hidden,
            sync_status=sync_status,
            sync_error=None,
            last_synced_at=now,
            created_at=now,
            updated_at=now,
            raw_data=raw_data,
        )

        db.add(event)
        await db.flush()
        await db.refresh(event)

        logger.info(f"Created event locally: {event.id} (spond_id: {event.spond_id})")
        return event

    @staticmethod
    async def push_to_spond(
        db: AsyncSession,
        event_id: int,
        spond_service: SpondService,
    ) -> Event:
        """
        Push a local or pending event to Spond

        Args:
            db: Database session
            event_id: Event ID
            spond_service: Spond service instance

        Returns:
            Updated event

        Raises:
            ValueError: If event not found
            Exception: If sync fails
        """
        event = await EventService.get_by_id(db, event_id)
        if not event:
            raise ValueError(f"Event {event_id} not found")

        try:
            # Prepare event data for Spond API with correct field names
            # Timestamps must be ISO 8601 format with Z suffix for UTC
            start_ts = event.start_time.isoformat()
            if not start_ts.endswith("Z"):
                start_ts += "Z"
            end_ts = event.end_time.isoformat()
            if not end_ts.endswith("Z"):
                end_ts += "Z"

            spond_data = {
                "heading": event.heading,
                "description": event.description or "",
                "spondType": event.event_type,
                "startTimestamp": start_ts,
                "endTimestamp": end_ts,
                "maxAccepted": event.max_accepted,
            }

            # Add location if provided
            if event.location_address:
                spond_data["location"] = {
                    "address": event.location_address,
                    "latitude": event.location_latitude,
                    "longitude": event.location_longitude,
                }

            # Extract group_id from raw_data if available
            group_id = None
            if event.raw_data and isinstance(event.raw_data, dict):
                recipients = event.raw_data.get("recipients", {})
                if isinstance(recipients, dict):
                    group = recipients.get("group", {})
                    if isinstance(group, dict):
                        group_id = group.get("id")

            # Create or update in Spond
            is_local = event.sync_status == "local_only" or (
                event.spond_id and event.spond_id.startswith("local_")
            )
            if is_local:
                # Create new event in Spond
                if not group_id:
                    raise ValueError(
                        "Cannot push event to Spond without a group. "
                        "Please select a group when creating the event."
                    )
                result = await spond_service.create_event(spond_data, group_id=group_id)
                new_spond_id = result.get("id") if result else None
                if not new_spond_id:
                    raise ValueError("Spond API did not return an event ID")
                event.spond_id = new_spond_id
                logger.info(f"Created event in Spond: {event.spond_id}")
            else:
                # Update existing event in Spond
                await spond_service.update_event(event.spond_id, spond_data)
                logger.info(f"Updated event in Spond: {event.spond_id}")

            # Update sync status
            event.sync_status = "synced"
            event.sync_error = None
            event.last_synced_at = datetime.utcnow()

            await db.flush()
            await db.refresh(event)

            return event

        except Exception as e:
            logger.error(f"Failed to push event to Spond: {e}")
            event.sync_status = "error"
            event.sync_error = str(e)
            await db.flush()
            await db.refresh(event)
            raise

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
