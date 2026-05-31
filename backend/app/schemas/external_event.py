"""
Pydantic schemas for external events
"""
from typing import Optional, List
from datetime import date as DateType, datetime
from pydantic import BaseModel, ConfigDict


class ExternalEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bueskyting_event_id: str
    name: str
    event_type_raw: Optional[str] = None
    date_start: Optional[DateType] = None
    date_end: Optional[DateType] = None
    location: Optional[str] = None
    address: Optional[str] = None
    organizer: Optional[str] = None
    distance: Optional[str] = None
    format: Optional[str] = None
    description: Optional[str] = None
    registration_url: Optional[str] = None
    info_url: Optional[str] = None
    results_url: Optional[str] = None
    registration_deadline: Optional[str] = None
    registration_type_raw: Optional[str] = None
    fees: Optional[str] = None
    contact_email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: str
    ai_event_category: Optional[str] = None
    ai_competition_type: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_analyzed_at: Optional[datetime] = None
    is_active: bool
    # Cross-links to local entities (confirmed in the UI). The *_label fields
    # are resolved at query time for display; navigation uses the ids.
    linked_event_id: Optional[int] = None
    linked_event_heading: Optional[str] = None
    linked_competition_id: Optional[int] = None
    linked_competition_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class EventLinkSuggestion(BaseModel):
    """A candidate local Spond event for an external competition."""
    event_id: int
    heading: str
    start_time: Optional[datetime] = None
    score: float  # fuzzy name-match score 0-100


class CompetitionLinkSuggestion(BaseModel):
    """A candidate local competition (results) for an external competition."""
    competition_id: int
    name: str
    date: Optional[DateType] = None
    score: float


class ExternalEventLinkSuggestions(BaseModel):
    events: List[EventLinkSuggestion] = []
    competitions: List[CompetitionLinkSuggestion] = []


class ExternalEventLinkRequest(BaseModel):
    """Confirm/clear a link. Pass null to clear that side."""
    event_id: Optional[int] = None
    competition_id: Optional[int] = None


class ExternalEventListResponse(BaseModel):
    events: List[ExternalEventResponse]
    total: int
    skip: int
    limit: int


class ExternalEventFilters(BaseModel):
    search: Optional[str] = None
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None
    ai_event_category: Optional[str] = None
    ai_competition_type: Optional[str] = None
    is_active: Optional[bool] = None
    skip: int = 0
    limit: int = 50
