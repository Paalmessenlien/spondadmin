"""
Event synchronization service
Handles syncing events from Spond API to local database
"""
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.sync_history import SyncHistory
from app.services.spond_service import SpondService

logger = logging.getLogger(__name__)


class EventSyncService:
    """
    Service for synchronizing events from Spond API to database
    """

    @staticmethod
    async def sync_events(
        db: AsyncSession,
        spond_service: SpondService,
        group_id: Optional[str] = None,
        max_events: int = 100,
    ) -> Dict[str, int]:
        """
        Sync events from Spond API to database

        Args:
            db: Database session
            spond_service: Spond service instance
            group_id: Optional group ID to filter events
            max_events: Maximum number of events to fetch

        Returns:
            Dictionary with sync statistics
        """
        # Create sync history record
        sync_record = SyncHistory(
            sync_type="events",
            status="running",
            started_at=datetime.utcnow(),
        )
        db.add(sync_record)
        await db.flush()

        stats = {
            "fetched": 0,
            "created": 0,
            "updated": 0,
            "errors": 0,
        }

        try:
            # Fetch events from Spond API
            logger.info(f"Fetching events from Spond API (group_id={group_id})")
            events_data = await spond_service.get_events(
                group_id=group_id,
                max_events=max_events,
            )

            stats["fetched"] = len(events_data)
            logger.info(f"Fetched {len(events_data)} events from Spond")

            # Process each event
            for event_dict in events_data:
                try:
                    await EventSyncService._sync_single_event(db, event_dict, stats)
                except Exception as e:
                    logger.error(f"Error syncing event {event_dict.get('id')}: {e}")
                    stats["errors"] += 1

            # Update sync record
            sync_record.status = "completed"
            sync_record.success = True
            sync_record.completed_at = datetime.utcnow()
            sync_record.items_fetched = stats["fetched"]
            sync_record.items_created = stats["created"]
            sync_record.items_updated = stats["updated"]

            await db.flush()

            logger.info(
                f"Event sync completed: {stats['created']} created, "
                f"{stats['updated']} updated, {stats['errors']} errors"
            )

            return stats

        except Exception as e:
            logger.error(f"Event sync failed: {e}")

            # Update sync record with error
            sync_record.status = "failed"
            sync_record.success = False
            sync_record.completed_at = datetime.utcnow()
            sync_record.error_message = str(e)
            await db.flush()

            raise

    @staticmethod
    async def _sync_single_event(
        db: AsyncSession,
        event_dict: Dict[str, Any],
        stats: Dict[str, int]
    ) -> None:
        """
        Sync a single event to the database

        Args:
            db: Database session
            event_dict: Event data from Spond API
            stats: Statistics dictionary to update
        """
        spond_id = event_dict.get("id")
        if not spond_id:
            logger.warning("Event missing ID, skipping")
            return

        # Check if event already exists
        result = await db.execute(
            select(Event).where(Event.spond_id == spond_id)
        )
        existing_event = result.scalar_one_or_none()

        # Extract event data
        heading = event_dict.get("heading", "Untitled Event")
        description = event_dict.get("description")
        event_type = event_dict.get("type", "EVENT")

        # Parse timestamps
        start_time = EventSyncService._parse_timestamp(event_dict.get("startTimestamp"))
        end_time = EventSyncService._parse_timestamp(event_dict.get("endTimestamp"))
        created_time = EventSyncService._parse_timestamp(event_dict.get("createdTime"))
        invite_time = EventSyncService._parse_timestamp(event_dict.get("inviteTime"))

        # Extract status flags
        cancelled = event_dict.get("cancelled", False)
        hidden = event_dict.get("hidden", False)

        # Extract location
        location = event_dict.get("location", {})
        location_address = location.get("address") if location else None
        location_latitude = location.get("latitude") if location else None
        location_longitude = location.get("longitude") if location else None

        # Extract max participants
        max_accepted = event_dict.get("maxAccepted", 0)

        # Extract responses
        responses = EventSyncService._extract_responses(event_dict.get("responses"))

        if existing_event:
            # Update existing event
            now = datetime.utcnow()
            existing_event.heading = heading
            existing_event.description = description
            existing_event.event_type = event_type
            existing_event.start_time = start_time
            existing_event.end_time = end_time
            existing_event.created_time = created_time
            existing_event.invite_time = invite_time
            existing_event.cancelled = cancelled
            existing_event.hidden = hidden
            existing_event.location_address = location_address
            existing_event.location_latitude = location_latitude
            existing_event.location_longitude = location_longitude
            existing_event.max_accepted = max_accepted
            existing_event.responses = responses
            existing_event.raw_data = event_dict
            existing_event.last_synced_at = now
            existing_event.updated_at = now
            # Only update sync_status to 'synced' if it's not local_only
            if existing_event.sync_status != "local_only":
                existing_event.sync_status = "synced"
                existing_event.sync_error = None

            stats["updated"] += 1
            logger.debug(f"Updated event {spond_id}: {heading}")

        else:
            # Create new event
            now = datetime.utcnow()
            new_event = Event(
                spond_id=spond_id,
                heading=heading,
                description=description,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                created_time=created_time,
                invite_time=invite_time,
                cancelled=cancelled,
                hidden=hidden,
                location_address=location_address,
                location_latitude=location_latitude,
                location_longitude=location_longitude,
                max_accepted=max_accepted,
                responses=responses,
                raw_data=event_dict,
                sync_status="synced",  # Events from Spond are synced by definition
                sync_error=None,
                last_synced_at=now,
                created_at=now,
                updated_at=now,
            )

            db.add(new_event)
            stats["created"] += 1
            logger.debug(f"Created event {spond_id}: {heading}")

        await db.flush()

    @staticmethod
    def _parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
        """
        Parse timestamp string to datetime

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Datetime object or None
        """
        if not timestamp_str:
            return None

        try:
            # Handle ISO format with timezone
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'

            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None

    @staticmethod
    def _extract_responses(responses_dict: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Preserve complete Spond API response structure

        The Spond API returns both ID arrays AND a detailed responses array.
        We preserve everything to support analytics.

        Args:
            responses_dict: Responses dictionary from Spond API

        Returns:
            Complete responses dictionary from Spond API
        """
        if not responses_dict:
            return None

        # Return the complete response object from Spond
        # This includes both 'responses' array and ID arrays (acceptedIds, declinedIds, etc.)
        return responses_dict
