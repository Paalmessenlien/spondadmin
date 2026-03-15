"""
Competition Result schemas
"""
from typing import Optional, List
from datetime import date as DateType, datetime
from pydantic import BaseModel, ConfigDict


class CompetitionResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: Optional[str] = None
    archer_name: str
    bueskyting_archer_id: Optional[str] = None
    competition_id: Optional[int] = None
    event_name: Optional[str] = None
    distance: Optional[str] = None
    equipment_class: Optional[str] = None
    round_type: Optional[str] = None
    score: Optional[int] = None
    ranking: Optional[int] = None
    date: Optional[DateType] = None
    event_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CompetitionResultListResponse(BaseModel):
    results: List[CompetitionResultResponse]
    total: int
    skip: int
    limit: int


class CompetitionResultFilters(BaseModel):
    search: Optional[str] = None
    equipment_class: Optional[str] = None
    distance: Optional[str] = None
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None
    spond_id: Optional[str] = None
    bueskyting_archer_id: Optional[str] = None
    sort_by: str = "date"
    sort_dir: str = "desc"
    skip: int = 0
    limit: int = 50
