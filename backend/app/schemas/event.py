"""
Event schemas for request/response validation
"""
from typing import Optional, List, Literal
from datetime import datetime, time, timezone
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EventResponseProfile(BaseModel):
    """Profile data within a response"""
    id: Optional[str] = None
    # Local members.id (resolved from the Spond uid) so the UI can link to the
    # member detail page. None when the attendee isn't a synced local member.
    member_id: Optional[int] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None


class EventResponseItem(BaseModel):
    """Single response item with answer and profile"""
    answer: str
    profile: Optional[EventResponseProfile] = None


class EventResponses(BaseModel):
    """
    Event responses schema - supports both UID arrays and detailed responses
    """
    accepted_uids: List[str] = Field(default_factory=list)
    declined_uids: List[str] = Field(default_factory=list)
    unanswered_uids: List[str] = Field(default_factory=list)
    waiting_list_uids: List[str] = Field(default_factory=list)
    unconfirmed_uids: List[str] = Field(default_factory=list)
    responses: List[EventResponseItem] = Field(default_factory=list)

    model_config = ConfigDict(extra='allow')


class EventLocation(BaseModel):
    """Location schema"""
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EventBase(BaseModel):
    """
    Base event schema with common fields
    """
    spond_id: str
    heading: str
    description: Optional[str] = None
    event_type: Literal["AVAILABILITY", "EVENT", "RECURRING"]
    start_time: datetime
    end_time: datetime
    created_time: datetime
    invite_time: Optional[datetime] = None
    cancelled: bool = False
    hidden: bool = False
    location_address: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    max_accepted: int = 0
    # Audience override + scheduling intent — see model docstring.
    invited_subgroup_uids: Optional[List[str]] = None
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None


class EventResponse(EventBase):
    """
    Event response schema (from database)
    """
    id: int
    group_id: Optional[str] = None  # Group spond_id this event belongs to
    responses: Optional[EventResponses] = None
    raw_data: Optional[dict] = None  # Raw data from Spond API
    sync_status: str  # synced, pending, local_only, error
    sync_error: Optional[str] = None
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime
    # ID of the training_shift that published this Spond event, if any.
    # Computed at query time via LEFT JOIN on training_shifts.spond_event_id
    # — never stored on the events row. None for events that weren't
    # produced from a training shift.
    linked_shift_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    """
    Paginated list of events
    """
    events: List[EventResponse]
    total: int
    skip: int
    limit: int


class EventCreate(BaseModel):
    """
    Schema for creating a new event
    """
    heading: str
    description: Optional[str] = None
    event_type: Literal["AVAILABILITY", "EVENT", "RECURRING"] = "EVENT"
    start_time: datetime
    end_time: datetime
    location_address: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    max_accepted: int = 0
    cancelled: bool = False
    hidden: bool = False
    sync_to_spond: bool = False  # Whether to immediately sync to Spond
    group_id: Optional[str] = None  # Group spond_id to associate event with
    # Attendee and owner management
    invited_member_ids: Optional[List[str]] = None  # Spond member IDs to invite (None = all group members)
    invited_subgroup_uids: Optional[List[str]] = None  # Subgroup uids — invite members in any
    owner_ids: Optional[List[str]] = None  # Profile IDs for responsible persons
    # Invite scheduling — see model docstring. Both NULL → send immediately.
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None


class EventUpdate(BaseModel):
    """
    Schema for updating an event
    """
    heading: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location_address: Optional[str] = None
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None
    max_accepted: Optional[int] = None
    cancelled: Optional[bool] = None
    hidden: Optional[bool] = None
    sync_to_spond: bool = False  # Whether to immediately sync changes to Spond
    # Attendee and owner management
    invited_member_ids: Optional[List[str]] = None  # Spond member IDs to invite
    invited_subgroup_uids: Optional[List[str]] = None
    owner_ids: Optional[List[str]] = None  # Profile IDs for responsible persons
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None


class EventFilters(BaseModel):
    """
    Filters for listing events
    """
    group_id: Optional[str] = None
    subgroup_id: Optional[str] = None
    event_type: Optional[Literal["AVAILABILITY", "EVENT", "RECURRING"]] = None
    include_cancelled: bool = False
    include_hidden: bool = False
    include_archived: bool = False  # Include events where end_time has passed
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None  # Search in heading/description

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _strip_tzinfo(cls, value):
        """Normalize incoming datetimes to tz-naive UTC.

        The frontend sends ISO strings with `Z`, which Pydantic parses into
        tz-aware values. PostgreSQL `TIMESTAMP WITHOUT TIME ZONE` columns
        (events.start_time / end_time) refuse those, so we shift to UTC and
        drop the tzinfo. Matches the convention in our sync services.
        """
        if value is None:
            return value
        if isinstance(value, datetime) and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value


class EventStats(BaseModel):
    """
    Event statistics
    """
    total_events: int
    upcoming_events: int
    past_events: int
    cancelled_events: int
    events_by_type: dict


class EventResponseUpdate(BaseModel):
    """
    Update a user's response to an event
    """
    user_id: str
    response_type: Literal["accepted", "declined", "unanswered", "waiting_list", "unconfirmed"]


class EventSyncResult(BaseModel):
    """
    Result of event synchronization
    """
    total_fetched: int
    created: int
    updated: int
    errors: int
    sync_time: datetime
