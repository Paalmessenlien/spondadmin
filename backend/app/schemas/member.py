"""
Member schemas for API requests and responses
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr


# ============================================================
# Base Schemas
# ============================================================

class MemberBase(BaseModel):
    """Base member schema"""
    spond_id: str
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


# ============================================================
# Request Schemas
# ============================================================

class MemberUpdate(BaseModel):
    """Schema for updating a member"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None


class MemberSyncRequest(BaseModel):
    """Schema for member sync request"""
    group_id: Optional[str] = Field(None, description="Sync members from specific group")
    force_refresh: bool = Field(default=False, description="Force refresh even if recently synced")


# ============================================================
# Response Schemas
# ============================================================

class MemberGroupResponse(BaseModel):
    """Schema for member's group association in response"""
    group_id: int
    group_name: str
    subgroup_id: Optional[str] = None
    subgroup_name: Optional[str] = None

    class Config:
        from_attributes = True


class MemberResponse(MemberBase):
    """Schema for member response"""
    id: int
    group_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    member_created_time: Optional[datetime] = None
    role_uids: Optional[List[str]] = None
    subgroup_uids: Optional[List[str]] = None
    fields: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemberListResponse(BaseModel):
    """Schema for paginated member list response"""
    members: List[MemberResponse]
    total: int
    skip: int
    limit: int


class MemberSyncResult(BaseModel):
    """Schema for member sync result"""
    total_fetched: int
    created: int
    updated: int
    errors: int
    sync_time: datetime


class MemberStats(BaseModel):
    """Schema for member statistics"""
    total_members: int
    members_with_email: int
    members_with_phone: int
    members_with_profile: int
    average_groups_per_member: float


# ============================================================
# Filter Schemas
# ============================================================

class MemberFilters(BaseModel):
    """Schema for filtering members"""
    search: Optional[str] = Field(None, description="Search in name and email")
    group_id: Optional[int] = Field(None, description="Filter by group ID")
    has_email: Optional[bool] = Field(None, description="Filter by presence of email")
    has_phone: Optional[bool] = Field(None, description="Filter by presence of phone")
    has_guardians: Optional[bool] = Field(None, description="Filter by presence of guardians")
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
