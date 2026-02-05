"""
Pydantic schemas for event categories
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Pattern Rule schemas
class PatternRule(BaseModel):
    """Single pattern matching rule"""
    type: str = Field(..., description="Pattern type: contains, starts_with, ends_with, regex")
    value: str = Field(..., description="Pattern value to match")
    case_insensitive: bool = Field(True, description="Whether matching is case insensitive")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        allowed_types = ["contains", "starts_with", "ends_with", "regex"]
        if v not in allowed_types:
            raise ValueError(f"Pattern type must be one of: {', '.join(allowed_types)}")
        return v


class PatternRules(BaseModel):
    """Container for pattern rules"""
    patterns: List[PatternRule] = Field(default_factory=list)


# Category CRUD schemas
class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str = Field(..., min_length=1, max_length=100)
    pattern_rules: Dict[str, Any] = Field(default_factory=lambda: {"patterns": []})
    priority: int = Field(100, ge=0)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    is_default: bool = False


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, min_length=1, max_length=100)
    pattern_rules: Optional[Dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryWithStats(CategoryResponse):
    """Category with additional statistics"""
    event_count: int = 0
    percentage: float = 0.0


# Category statistics schemas
class CategoryDistribution(BaseModel):
    """Category distribution statistics"""
    category_id: int
    category_name: str
    color: str
    icon: str
    event_count: int
    percentage: float


class CategoryAttendanceStats(BaseModel):
    """Attendance statistics for a category"""
    category_id: int
    category_name: str
    color: str
    total_events: int
    avg_attendance_rate: float
    total_responses: int


# Bulk categorization schemas
class BulkCategorizeRequest(BaseModel):
    """Request for bulk categorization"""
    event_ids: Optional[List[int]] = None
    force_recategorize: bool = False


class BulkCategorizeResponse(BaseModel):
    """Response from bulk categorization"""
    total_processed: int
    categorized: int
    unchanged: int


# Pattern testing schema
class PatternTestRequest(BaseModel):
    """Request to test pattern matching"""
    heading: str
    pattern_rules: Dict[str, Any]


class PatternTestResponse(BaseModel):
    """Response from pattern testing"""
    matches: bool
    matched_pattern: Optional[PatternRule] = None
