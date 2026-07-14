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


# ============================================================
# Upstream-compat shim: Spond.login endpoint moved
# ============================================================
# As of mid-2026, Spond's API moved login from /core/v1/login (404) to
# /core/v1/auth2/login, and the response shape changed — the bearer token
# now lives at `accessToken.token` instead of `loginToken`. The `spond`
# library (1.2.0) hasn't been patched yet (Olen/Spond#229). Until that
# ships, monkey-patch `_SpondBase.login` to hit the new URL and pull the
# token from the new location. The Bearer-header flow downstream is
# unchanged, so every other call (get_groups, get_events, …) keeps working.
def _install_spond_login_shim() -> None:
    from spond.base import _SpondBase
    from spond import AuthenticationError

    async def _patched_login(self) -> None:
        login_url = f"{self.api_url}auth2/login"
        data = {"email": self.username, "password": self.password}
        async with self.clientsession.post(login_url, json=data) as r:
            login_result = await r.json()
            access = login_result.get("accessToken")
            if isinstance(access, dict):
                self.token = access.get("token")
            if self.token is None:
                raise AuthenticationError(
                    f"Login failed. Response received: {login_result}"
                )

    _SpondBase.login = _patched_login
    logger.info("Spond login shim installed (auth2/login → accessToken.token)")


_install_spond_login_shim()


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

    @staticmethod
    def _is_token_expired(error: Exception) -> bool:
        """True if a Spond library error is a 401 token-expiry a re-login fixes."""
        msg = str(error)
        return "401" in msg and ("tokenExpired" in msg or "Not authenticated" in msg)

    async def _call_with_reauth(self, make_call):
        """Run a Spond library call, re-authenticating once on 401 tokenExpired.

        The Spond client is a long-lived singleton that only logs in when its
        token is unset, so an expired token surfaces as a 401 on every call
        until we force a fresh login. Mirrors the retry in create_event so the
        read paths (event/group/member sync) survive token expiry too.
        """
        client = await self._get_client()
        for attempt in range(2):
            try:
                return await make_call(client)
            except Exception as e:
                if attempt == 0 and self._is_token_expired(e):
                    logger.info(
                        "Spond returned 401 (token expired); "
                        "re-authenticating and retrying"
                    )
                    client.token = None
                    await client.login()
                    continue
                raise

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
        try:
            events_data = await self._call_with_reauth(
                lambda client: client.get_events(
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
        try:
            event_data = await self._call_with_reauth(
                lambda client: client.get_event(event_id)
            )
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

            # Direct field updates (these field names match the template).
            # `inviteTime` is Spond's "send later" field — when set, the
            # event sits in scheduled state on Spond until that timestamp.
            # When omitted, Spond sends invitations immediately.
            direct_fields = [
                "heading", "description", "spondType",
                "startTimestamp", "endTimestamp", "maxAccepted",
                "commentsDisabled", "autoAccept", "visibility",
                "inviteTime",
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
                    # Fetch all group members (default behavior). Guard the
                    # Spond library call: its _get_entity() iterates
                    # `self.groups` and does `entity["id"]`, which raises a
                    # cryptic "string indices must be integers, not 'str'"
                    # TypeError when the groups/ endpoint returns a non-list
                    # (e.g. an auth-error object). Never let that opaque error
                    # abort event creation — fall back to a group reference
                    # with no explicit member list.
                    member_ids = []
                    try:
                        group_data = await client.get_group(group_id)
                    except Exception as e:  # noqa: BLE001 — spond lib raises bare
                        logger.warning(
                            "client.get_group(%s) failed (%s); creating event "
                            "with the group reference only (no explicit member "
                            "list)", group_id, e,
                        )
                        group_data = None
                    if isinstance(group_data, dict) and isinstance(
                        group_data.get("members"), list
                    ):
                        for member in group_data["members"]:
                            if isinstance(member, dict) and "id" in member:
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

            # Log the payload for debugging — explicitly include inviteTime
            # and the number of invitees so we can verify send-later flows.
            recipients_block = event_payload.get("recipients") or {}
            group_members = (
                recipients_block.get("groupMembers")
                if isinstance(recipients_block, dict)
                else None
            ) or []
            logger.info(
                "Creating event with payload: heading=%r start=%s end=%s "
                "group=%s inviteTime=%s invitees=%d",
                event_payload.get("heading"),
                event_payload.get("startTimestamp"),
                event_payload.get("endTimestamp"),
                group_id,
                event_payload.get("inviteTime"),
                len(group_members),
            )

            # POST to create new event. Spond access tokens expire, but the
            # client is a long-lived singleton that only logs in when token
            # is unset — so a stale token yields a 401 tokenExpired. Re-login
            # once and retry with a fresh Bearer header before giving up.
            import json
            url = f"{client.api_url}sponds"
            for attempt in range(2):
                async with client.clientsession.post(
                    url, json=event_payload, headers=client.auth_headers
                ) as r:
                    response_text = await r.text()

                    if r.status == 401 and attempt == 0:
                        logger.info(
                            "Spond returned 401 (token expired); "
                            "re-authenticating and retrying event creation"
                        )
                        client.token = None
                        await client.login()
                        continue

                    if r.status >= 400:
                        logger.error(f"Spond API error {r.status}: {response_text}")
                        raise Exception(f"Spond API error {r.status}: {response_text}")

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
        try:
            groups_data = await self._call_with_reauth(
                lambda client: client.get_groups()
            )
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
        try:
            group_data = await self._call_with_reauth(
                lambda client: client.get_group(group_id)
            )
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
        try:
            person_data = await self._call_with_reauth(
                lambda client: client.get_person(user_identifier)
            )
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
        try:
            messages_data = await self._call_with_reauth(
                lambda client: client.get_messages(max_chats=max_chats)
            )
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
