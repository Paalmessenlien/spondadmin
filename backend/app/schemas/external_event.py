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
    ai_summary: Optional[str] = None
    ai_analyzed_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


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
    is_active: Optional[bool] = None
    skip: int = 0
    limit: int = 50
