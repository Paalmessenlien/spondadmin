"""
Pydantic schemas for reports
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


# Report configuration schemas
class DateRangeConfig(BaseModel):
    """Date range configuration"""
    start: date
    end: date


class ReportConfiguration(BaseModel):
    """Report configuration structure"""
    date_range: Optional[DateRangeConfig] = None
    group_ids: Optional[List[str]] = Field(default_factory=list)
    category_ids: Optional[List[int]] = Field(default_factory=list)
    metrics: List[str] = Field(
        default_factory=lambda: ["attendance_rate", "response_distribution"]
    )
    chart_types: List[str] = Field(default_factory=lambda: ["line", "doughnut"])
    comparison_period: Optional[str] = None


# Report CRUD schemas
class ReportBase(BaseModel):
    """Base report schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: str = Field(..., min_length=1, max_length=50)
    configuration: Dict[str, Any]
    is_public: bool = False
    is_favorite: bool = False


class ReportCreate(ReportBase):
    """Schema for creating a new report"""
    pass


class ReportUpdate(BaseModel):
    """Schema for updating a report"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    report_type: Optional[str] = Field(None, min_length=1, max_length=50)
    configuration: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None


class ReportResponse(ReportBase):
    """Schema for report response"""
    id: int
    created_by: int
    last_generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for report list item"""
    id: int
    name: str
    description: Optional[str]
    report_type: str
    is_public: bool
    is_favorite: bool
    created_by: int
    last_generated_at: Optional[datetime]
    created_at: datetime


# Report generation schemas
class ReportDataResponse(BaseModel):
    """Response containing generated report data"""
    report_id: int
    report_name: str
    generated_at: datetime
    data: Dict[str, Any]


# Report filtering
class ReportFilterParams(BaseModel):
    """Parameters for filtering reports"""
    show_public: bool = True
    show_favorites: bool = False
    report_type: Optional[str] = None


# CSV Export
class ReportExportFormat(BaseModel):
    """Export format specification"""
    format: str = Field("csv", pattern=r"^(csv|pdf)$")
