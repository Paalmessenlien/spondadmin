"""
Event schemas for request/response validation
"""
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EventResponses(BaseModel):
    """
    Event responses schema
    """
    accepted_uids: List[str] = Field(default_factory=list)
    declined_uids: List[str] = Field(default_factory=list)
    unanswered_uids: List[str] = Field(default_factory=list)
    waiting_list_uids: List[str] = Field(default_factory=list)
    unconfirmed_uids: List[str] = Field(default_factory=list)


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


class EventResponse(EventBase):
    """
    Event response schema (from database)
    """
    id: int
    responses: Optional[EventResponses] = None
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    """
    Paginated list of events
    """
    events: List[EventResponse]
    total: int
    skip: int
    limit: int


class EventUpdate(BaseModel):
    """
    Schema for updating an event
    """
    heading: Optional[str] = None
    description: Optional[str] = None
    cancelled: Optional[bool] = None
    hidden: Optional[bool] = None


class EventFilters(BaseModel):
    """
    Filters for listing events
    """
    group_id: Optional[str] = None
    subgroup_id: Optional[str] = None
    event_type: Optional[Literal["AVAILABILITY", "EVENT", "RECURRING"]] = None
    include_cancelled: bool = False
    include_hidden: bool = False
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = None  # Search in heading/description


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
