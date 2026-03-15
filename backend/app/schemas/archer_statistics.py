"""
Archer Statistics schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ArcherStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: Optional[str] = None
    bueskyting_archer_id: Optional[str] = None
    archer_name: str
    year: int
    starts: int
    top3: int
    victories: int
    created_at: datetime
    updated_at: datetime


class ArcherStatisticsListResponse(BaseModel):
    statistics: List[ArcherStatisticsResponse]
    total: int
