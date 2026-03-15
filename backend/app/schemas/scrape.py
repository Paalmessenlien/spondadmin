"""
Scraping-related schemas
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ScrapeLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scrape_type: str
    status: str
    items_found: int
    items_created: int
    items_updated: int
    error_message: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime


class ScrapeLogListResponse(BaseModel):
    logs: List[ScrapeLogResponse]
    total: int


class ScrapingConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base_url: str
    records_url: str
    club_id: str
    last_results_scrape: Optional[datetime] = None
    last_records_scrape: Optional[datetime] = None
    auto_scrape_enabled: bool
    scrape_interval_hours: int
    created_at: datetime
    updated_at: datetime


class ScrapingConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    records_url: Optional[str] = None
    club_id: Optional[str] = None
    auto_scrape_enabled: Optional[bool] = None
    scrape_interval_hours: Optional[int] = Field(None, ge=1, le=168)


class UnmatchedArcherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bueskyting_id: str
    name: str
    is_active: bool
    dismissed: bool
    suggested_spond_id: Optional[str] = None
    match_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class ArcherMatchRequest(BaseModel):
    bueskyting_id: str
    spond_id: str


class ScrapeRunRequest(BaseModel):
    type: str = Field(..., pattern="^(full|records|single_archer|event_dates)$")
    archer_id: Optional[str] = None
    mode: str = Field("incremental", pattern="^(incremental|full)$")


class ScoresSummaryResponse(BaseModel):
    total_results: int = 0
    total_competitions: int = 0
    total_records: int = 0
    total_archers: int = 0
    unmatched_archers: int = 0
    latest_scrape: Optional[datetime] = None
