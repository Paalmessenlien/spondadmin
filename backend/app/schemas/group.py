"""
Group schemas for API requests and responses
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================
# Base Schemas
# ============================================================

class GroupBase(BaseModel):
    """Base group schema"""
    spond_id: str
    name: str
    description: Optional[str] = None


# ============================================================
# Request Schemas
# ============================================================

class GroupUpdate(BaseModel):
    """Schema for updating a group"""
    name: Optional[str] = None
    description: Optional[str] = None


class GroupSyncRequest(BaseModel):
    """Schema for group sync request"""
    force_refresh: bool = Field(default=False, description="Force refresh even if recently synced")


# ============================================================
# Response Schemas
# ============================================================

class SubgroupResponse(BaseModel):
    """Schema for subgroup in response"""
    id: str
    name: str

    class Config:
        from_attributes = True


class GroupResponse(GroupBase):
    """Schema for group response"""
    id: int
    roles: Optional[List[Dict[str, Any]]] = None
    subgroups: Optional[List[Dict[str, Any]]] = None
    member_count: int = 0
    raw_data: Optional[Dict[str, Any]] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GroupListResponse(BaseModel):
    """Schema for paginated group list response"""
    groups: List[GroupResponse]
    total: int
    skip: int
    limit: int


class GroupSyncResult(BaseModel):
    """Schema for group sync result"""
    total_fetched: int
    created: int
    updated: int
    errors: int
    sync_time: datetime


class GroupStats(BaseModel):
    """Schema for group statistics"""
    total_groups: int
    groups_with_subgroups: int
    total_subgroups: int
    average_members_per_group: float


# ============================================================
# Filter Schemas
# ============================================================

class GroupFilters(BaseModel):
    """Schema for filtering groups"""
    search: Optional[str] = Field(None, description="Search in name and description")
    has_subgroups: Optional[bool] = Field(None, description="Filter by presence of subgroups")
    min_members: Optional[int] = Field(None, description="Minimum number of members")
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
