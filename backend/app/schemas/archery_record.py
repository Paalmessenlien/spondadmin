"""
Archery Record schemas
"""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ArcheryRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: Optional[str] = None
    archer_name: Optional[str] = None
    division: str
    category: str
    distance: Optional[str] = None
    round_type: str
    score: int
    record_date: Optional[date] = None
    record_type: str
    team_members: Optional[dict] = None
    source_url: Optional[str] = None
    is_current: bool
    created_at: datetime
    updated_at: datetime


class ArcheryRecordListResponse(BaseModel):
    records: List[ArcheryRecordResponse]
    total: int
    skip: int
    limit: int


class ArcheryRecordFilters(BaseModel):
    division: Optional[str] = None
    category: Optional[str] = None
    record_type: Optional[str] = None
    skip: int = 0
    limit: int = 100
