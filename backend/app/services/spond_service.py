"""
Spond API service wrapper
Handles all communication with the Spond API using the spond and spond-classes libraries
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from spond.spond import Spond
from spond_classes import Event as SpondEvent, Group as SpondGroup

from app.core.config import settings

logger = logging.getLogger(__name__)


class SpondService:
    """
    Service class for interacting with the Spond API
    """

    def __init__(self):
        """Initialize the Spond service"""
        self._client: Optional[Spond] = None
        self._username = settings.SPOND_USERNAME
        self._password = settings.SPOND_PASSWORD

    async def _get_client(self) -> Spond:
        """
        Get or create the Spond client instance

        Returns:
            Configured Spond client
        """
        if self._client is None:
            if not self._username or not self._password:
                raise ValueError(
                    "Spond credentials not configured. "
                    "Please set SPOND_USERNAME and SPOND_PASSWORD in .env"
                )

            self._client = Spond(
                username=self._username,
                password=self._password
            )
            logger.info("Spond client initialized")

        return self._client

    async def close(self):
        """Close the Spond client session"""
        if self._client and self._client.clientsession:
            await self._client.clientsession.close()
            self._client = None
            logger.info("Spond client session closed")

    # ============================================================
    # Events API
    # ============================================================

    async def get_events(
        self,
        group_id: Optional[str] = None,
        subgroup_id: Optional[str] = None,
        include_scheduled: bool = True,
        include_hidden: bool = False,
        max_end: Optional[datetime] = None,
        min_end: Optional[datetime] = None,
        max_start: Optional[datetime] = None,
        min_start: Optional[datetime] = None,
        max_events: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from Spond API

        Args:
            group_id: Filter by group ID
            subgroup_id: Filter by subgroup ID
            include_scheduled: Include scheduled events
            include_hidden: Include hidden events
            max_end: Maximum end timestamp
            min_end: Minimum end timestamp
            max_start: Maximum start timestamp
            min_start: Minimum start timestamp
            max_events: Maximum number of events to fetch

        Returns:
            List of event dictionaries from Spond API
        """
        client = await self._get_client()

        try:
            events_data = await client.get_events(
                group_id=group_id,
                subgroup_id=subgroup_id,
                include_scheduled=include_scheduled,
                include_hidden=include_hidden,
                max_end=max_end,
                min_end=min_end,
                max_start=max_start,
                min_start=min_start,
                max_events=max_events,
            )

            logger.info(f"Fetched {len(events_data)} events from Spond API")
            return events_data

        except Exception as e:
            logger.error(f"Error fetching events from Spond: {e}")
            raise

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single event by ID

        Args:
            event_id: Spond event ID

        Returns:
            Event dictionary or None if not found
        """
        client = await self._get_client()

        try:
            event_data = await client.get_event(event_id)
            logger.info(f"Fetched event {event_id}")
            return event_data

        except Exception as e:
            logger.error(f"Error fetching event {event_id}: {e}")
            raise

    async def create_event(
        self,
        event_data: Dict[str, Any],
        group_id: Optional[str] = None,
        invited_member_ids: Optional[List[str]] = None,
        owner_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new event in Spond

        Args:
            event_data: Dictionary with Spond field names:
                - heading: Event title
                - description: Event description
                - spondType: "EVENT", "RECURRING", or "AVAILABILITY"
                - startTimestamp: ISO 8601 timestamp (e.g., "2024-01-15T10:00:00Z")
                - endTimestamp: ISO 8601 timestamp
                - maxAccepted: Max participants (0 = unlimited)
                - location: Optional dict with address, latitude, longitude
            group_id: Optional group ID to associate event with
            invited_member_ids: Optional list of member IDs to invite (None = all group members)
            owner_ids: Optional list of profile IDs for responsible persons

        Returns:
            Created event dictionary with 'id' field

        Raises:
            Exception: If Spond API returns an error
        """
        client = await self._get_client()

        try:
            # Ensure the client is authenticated before making the POST request
            # The Spond library uses a decorator that auto-authenticates for its methods,
            # but since we're making a direct API call, we need to ensure authentication
            if not client.token:
                logger.info("Authenticating Spond client before event creation...")
                await client.login()
                logger.info("Spond client authenticated successfully")

            # Use the event template as base
            from spond.spond import Spond
            import copy
            event_payload = copy.deepcopy(Spond._EVENT_TEMPLATE)

            # Direct field updates (these field names match the template)
            direct_fields = [
                "heading", "description", "spondType",
                "startTimestamp", "endTimestamp", "maxAccepted",
                "commentsDisabled", "autoAccept", "visibility"
            ]
            for field in direct_fields:
                if field in event_data and event_data[field] is not None:
                    event_payload[field] = event_data[field]

            # Handle location separately (it's a nested object)
            if event_data.get("location"):
                loc = event_data["location"]
                event_payload["location"] = {
                    "id": None,
                    "feature": loc.get("feature") or loc.get("address"),
                    "address": loc.get("address"),
                    "latitude": loc.get("latitude"),
                    "longitude": loc.get("longitude"),
                }

            # Set recipients with group - required for the event to appear in a group
            if group_id:
                # Use provided member IDs or fetch all group members
                if invited_member_ids is not None:
                    # Use the specific members that were selected
                    member_ids = invited_member_ids
                    logger.info(f"Using {len(member_ids)} selected members for invitation")
                else:
                    # Fetch all group members (default behavior)
                    group_data = await client.get_group(group_id)
                    member_ids = []
                    if group_data and "members" in group_data:
                        for member in group_data["members"]:
                            if "id" in member:
                                member_ids.append(member["id"])
                    logger.info(f"Found {len(member_ids)} members in group {group_id} (inviting all)")

                event_payload["recipients"] = {
                    "group": {"id": group_id},
                    "groupMembers": member_ids  # Array of member IDs
                }

            # Set owners (responsible persons) if provided
            if owner_ids:
                event_payload["owners"] = [{"id": owner_id} for owner_id in owner_ids]
                logger.info(f"Setting {len(owner_ids)} responsible persons for event")
            else:
                # Remove owners if None - it's not required for event creation
                if "owners" in event_payload and event_payload["owners"] == [{"id": None}]:
                    del event_payload["owners"]

            # Remove optional fields that may cause validation errors if empty
            # The tasks field in the template has a "name": None which causes errors
            if "tasks" in event_payload:
                del event_payload["tasks"]

            # Remove id if None - it will be assigned by the API
            if "id" in event_payload and event_payload["id"] is None:
                del event_payload["id"]

            # Log the payload for debugging
            logger.info(f"Creating event with payload: heading={event_payload.get('heading')}, "
                       f"start={event_payload.get('startTimestamp')}, group={group_id}")

            # POST to create new event
            url = f"{client.api_url}sponds"
            async with client.clientsession.post(
                url, json=event_payload, headers=client.auth_headers
            ) as r:
                response_text = await r.text()

                if r.status >= 400:
                    logger.error(f"Spond API error {r.status}: {response_text}")
                    raise Exception(f"Spond API error {r.status}: {response_text}")

                import json
                result = json.loads(response_text)
                logger.info(f"Created event in Spond: {result.get('id')}")
                return result

        except Exception as e:
            logger.error(f"Error creating event: {e}")
            raise

    async def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an event

        Args:
            event_id: Spond event ID
            updates: Dictionary with fields to update

        Returns:
            Updated event dictionary
        """
        client = await self._get_client()

        try:
            result = await client.update_event(event_id, updates)
            logger.info(f"Updated event {event_id}")
            return result

        except Exception as e:
            logger.error(f"Error updating event {event_id}: {e}")
            raise

    async def change_event_response(
        self,
        event_id: str,
        user_id: str,
        response_type: str
    ) -> Dict[str, Any]:
        """
        Change a user's response to an event

        Args:
            event_id: Spond event ID
            user_id: User ID
            response_type: Response type (accepted, declined, etc.)

        Returns:
            Response data
        """
        client = await self._get_client()

        try:
            # Build response payload based on type
            payload = {"response": response_type}

            result = await client.change_response(event_id, user_id, payload)
            logger.info(f"Changed response for user {user_id} on event {event_id}")
            return result

        except Exception as e:
            logger.error(f"Error changing response: {e}")
            raise

    async def get_event_attendance_xlsx(self, event_id: str) -> bytes:
        """
        Get event attendance as Excel file

        Args:
            event_id: Spond event ID

        Returns:
            Excel file bytes
        """
        client = await self._get_client()

        try:
            xlsx_data = await client.get_event_attendance_xlsx(event_id)
            logger.info(f"Generated attendance XLSX for event {event_id}")
            return xlsx_data

        except Exception as e:
            logger.error(f"Error generating attendance XLSX: {e}")
            raise

    async def update_event_attendees(
        self,
        event_id: str,
        member_ids: List[str],
        group_id: str
    ) -> Dict[str, Any]:
        """
        Update which members are invited to an event

        Args:
            event_id: Spond event ID
            member_ids: List of member IDs to invite
            group_id: Group ID the event belongs to

        Returns:
            Updated event dictionary
        """
        client = await self._get_client()

        try:
            updates = {
                "recipients": {
                    "group": {"id": group_id},
                    "groupMembers": member_ids
                }
            }
            result = await client.update_event(event_id, updates)
            logger.info(f"Updated attendees for event {event_id}: {len(member_ids)} members")
            return result

        except Exception as e:
            logger.error(f"Error updating event attendees: {e}")
            raise

    async def update_event_owners(
        self,
        event_id: str,
        owner_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Update responsible persons (owners) for an event

        Args:
            event_id: Spond event ID
            owner_ids: List of profile IDs for responsible persons

        Returns:
            Updated event dictionary
        """
        client = await self._get_client()

        try:
            updates = {
                "owners": [{"id": owner_id} for owner_id in owner_ids]
            }
            result = await client.update_event(event_id, updates)
            logger.info(f"Updated owners for event {event_id}: {len(owner_ids)} persons")
            return result

        except Exception as e:
            logger.error(f"Error updating event owners: {e}")
            raise

    # ============================================================
    # Groups API
    # ============================================================

    async def get_groups(self) -> List[Dict[str, Any]]:
        """
        Fetch all groups from Spond API

        Returns:
            List of group dictionaries
        """
        client = await self._get_client()

        try:
            groups_data = await client.get_groups()
            logger.info(f"Fetched {len(groups_data)} groups from Spond API")
            return groups_data

        except Exception as e:
            logger.error(f"Error fetching groups from Spond: {e}")
            raise

    async def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single group by ID

        Args:
            group_id: Spond group ID

        Returns:
            Group dictionary or None if not found
        """
        client = await self._get_client()

        try:
            group_data = await client.get_group(group_id)
            logger.info(f"Fetched group {group_id}")
            return group_data

        except Exception as e:
            logger.error(f"Error fetching group {group_id}: {e}")
            raise

    # ============================================================
    # Members API
    # ============================================================

    async def get_person(self, user_identifier: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a person/member by ID, email, or name

        Args:
            user_identifier: User ID, email, full name, or profile ID

        Returns:
            Person dictionary or None if not found
        """
        client = await self._get_client()

        try:
            person_data = await client.get_person(user_identifier)
            logger.info(f"Fetched person: {user_identifier}")
            return person_data

        except Exception as e:
            logger.error(f"Error fetching person {user_identifier}: {e}")
            raise

    # ============================================================
    # Messaging API
    # ============================================================

    async def get_messages(self, max_chats: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch messages/chats

        Args:
            max_chats: Maximum number of chats to retrieve

        Returns:
            List of chat dictionaries
        """
        client = await self._get_client()

        try:
            messages_data = await client.get_messages(max_chats=max_chats)
            logger.info(f"Fetched messages")
            return messages_data

        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            raise

    async def send_message(
        self,
        text: str,
        user: Optional[str] = None,
        group_uid: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a user, group, or existing chat

        Args:
            text: Message text
            user: User ID to send to
            group_uid: Group ID to send to
            chat_id: Existing chat ID to reply to

        Returns:
            Response data
        """
        client = await self._get_client()

        try:
            result = await client.send_message(
                text=text,
                user=user,
                group_uid=group_uid,
                chat_id=chat_id
            )
            logger.info(f"Sent message")
            return result

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    # ============================================================
    # Helper Methods using spond-classes
    # ============================================================

    async def get_typed_events(
        self,
        **kwargs
    ) -> List[SpondEvent]:
        """
        Get events as typed SpondEvent objects

        Args:
            **kwargs: Arguments to pass to get_events()

        Returns:
            List of SpondEvent objects
        """
        events_data = await self.get_events(**kwargs)

        typed_events = []
        for event_dict in events_data:
            try:
                typed_event = SpondEvent.from_dict(event_dict)
                typed_events.append(typed_event)
            except Exception as e:
                logger.warning(f"Failed to parse event {event_dict.get('id')}: {e}")

        return typed_events

    async def get_typed_groups(self) -> List[SpondGroup]:
        """
        Get groups as typed SpondGroup objects

        Returns:
            List of SpondGroup objects
        """
        groups_data = await self.get_groups()

        typed_groups = []
        for group_dict in groups_data:
            try:
                typed_group = SpondGroup.from_dict(group_dict)
                typed_groups.append(typed_group)
            except Exception as e:
                logger.warning(f"Failed to parse group {group_dict.get('id')}: {e}")

        return typed_groups


# Singleton instance
_spond_service: Optional[SpondService] = None


async def get_spond_service() -> SpondService:
    """
    Get or create the global SpondService instance

    Usage in FastAPI endpoints:
        async def endpoint(spond: SpondService = Depends(get_spond_service)):
            ...
    """
    global _spond_service

    if _spond_service is None:
        _spond_service = SpondService()

    return _spond_service
