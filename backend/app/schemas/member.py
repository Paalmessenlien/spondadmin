"""
Member schemas for API requests and responses
"""
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr, model_validator


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

class MemberGroupAssociation(BaseModel):
    """One entry per group a member belongs to, with per-group role/subgroup data."""

    model_config = ConfigDict(from_attributes=True)

    group_id: int = Field(..., description="Surrogate groups.id")
    spond_id: str = Field(..., description="Spond group id (string)")
    name: str
    role_uids: List[str] = Field(default_factory=list)
    subgroup_uids: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _from_group_member(cls, value: Any) -> Any:
        """Flatten a GroupMember ORM row into the response shape."""
        if isinstance(value, dict):
            return value
        # Treat as GroupMember instance: pull group attributes through .group
        group = getattr(value, "group", None)
        if group is None:
            return value
        return {
            "group_id": getattr(value, "group_id", None),
            "spond_id": getattr(group, "spond_id", None),
            "name": getattr(group, "name", None),
            "role_uids": getattr(value, "role_uids", []) or [],
            "subgroup_uids": getattr(value, "subgroup_uids", []) or [],
        }


class MemberResponse(MemberBase):
    """Schema for member response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    groups: List[MemberGroupAssociation] = Field(default_factory=list)
    profile: Optional[Dict[str, Any]] = None
    member_created_time: Optional[datetime] = None
    fields: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None
    last_synced_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _alias_group_associations(cls, value: Any) -> Any:
        """Map ORM `group_associations` → response `groups`."""
        if isinstance(value, dict):
            return value
        # If the ORM object exposes group_associations (it does), surface it as groups.
        assocs = getattr(value, "group_associations", None)
        if assocs is None:
            return value
        # Construct a lightweight shim that exposes both the original attributes
        # and our renamed `groups` field, so Pydantic v2 from_attributes picks it up.
        return _MemberShim(value, assocs)


class _MemberShim:
    """Lightweight attribute proxy that aliases group_associations -> groups."""

    __slots__ = ("_obj", "groups")

    def __init__(self, obj: Any, assocs: Any) -> None:
        self._obj = obj
        self.groups = list(assocs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._obj, name)


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

SortBy = Literal["name", "email", "group_count", "subgroup_count", "last_synced_at"]
SortOrder = Literal["asc", "desc"]


class MemberFilters(BaseModel):
    """Schema for filtering members"""
    search: Optional[str] = Field(None, description="Search in name and email")
    group_id: Optional[str] = Field(None, description="Filter by group spond_id")
    subgroup_id: Optional[str] = Field(None, description="Filter by Spond subgroup uid")
    has_email: Optional[bool] = Field(None, description="Filter by presence of email")
    has_phone: Optional[bool] = Field(None, description="Filter by presence of phone")
    has_guardians: Optional[bool] = Field(None, description="Filter by presence of guardians")
    sort_by: SortBy = Field("name", description="Field to sort by")
    sort_order: SortOrder = Field("asc", description="Sort direction")
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
