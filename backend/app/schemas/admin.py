"""
Admin user schemas.

Identity is owned by Clerk; the local Admin row only holds the
role/active flag and selected display fields. There is no longer a
local password, so create/update schemas don't accept one.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

from app.core.modules import ALL_MODULE_KEYS


class AdminBase(BaseModel):
    """Base admin schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    role: str = Field(default="viewer", pattern=r"^(admin|editor|viewer|kasserer)$")


class AdminCreate(AdminBase):
    """
    Schema for creating a new admin row directly (used by the seed
    script). Public-facing admin creation goes through ``AdminInvite``.
    """
    pass


class AdminUpdate(BaseModel):
    """Schema for updating an admin row. All fields optional."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[str] = Field(None, pattern=r"^(admin|editor|viewer|kasserer)$")
    # Per-user module allow-list. ``None`` = leave unchanged; ``[]`` = an
    # explicit empty allow-list; a list = the modules this user may reach.
    # Unknown keys are dropped so a stale UI can't grant phantom access.
    modules: Optional[List[str]] = None
    # Access-group assignment. Field absent = leave unchanged; ``null`` =
    # detach from any group; an int = assign to that group (copies its role,
    # clears per-user modules). Handled in the endpoint via model_fields_set.
    access_group_id: Optional[int] = None

    @field_validator("modules")
    @classmethod
    def _keep_known_modules(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        return sorted({m for m in v if m in ALL_MODULE_KEYS})


class AdminInvite(BaseModel):
    """
    Schema for inviting a new admin through Clerk.

    The backend creates a pending ``admins`` row plus a Clerk
    invitation; the user finishes onboarding by clicking the
    invite link and signing in.
    """
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field(default="viewer", pattern=r"^(admin|editor|viewer|kasserer)$")


class AdminResponse(AdminBase):
    """Schema for admin response (no secrets)."""
    id: int
    clerk_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Raw stored allow-list: ``None`` means "not customised" (falls back to
    # the assigned group, or role defaults); a list is an explicit override.
    modules: Optional[List[str]] = None
    # Assigned access group (id + name for display), if any.
    access_group_id: Optional[int] = None
    access_group_name: Optional[str] = None
    # Resolved set the user can actually reach. Requires a DB lookup to
    # compute, so endpoints populate it only where needed (e.g. /auth/me).
    effective_modules: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
