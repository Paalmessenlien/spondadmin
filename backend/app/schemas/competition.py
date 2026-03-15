"""
Competition schemas
"""
from typing import Optional, List
from datetime import date as DateType, datetime
from pydantic import BaseModel, ConfigDict


class CompetitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: Optional[DateType] = None
    location: Optional[str] = None
    event_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CompetitionListResponse(BaseModel):
    competitions: List[CompetitionResponse]
    total: int
    skip: int
    limit: int


class CompetitionFilters(BaseModel):
    search: Optional[str] = None
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None
    skip: int = 0
    limit: int = 50
