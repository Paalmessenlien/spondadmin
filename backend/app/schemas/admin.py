"""
Admin user schemas.

Identity is owned by Clerk; the local Admin row only holds the
role/active flag and selected display fields. There is no longer a
local password, so create/update schemas don't accept one.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AdminBase(BaseModel):
    """Base admin schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    role: str = Field(default="viewer", pattern=r"^(admin|editor|viewer)$")


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
    role: Optional[str] = Field(None, pattern=r"^(admin|editor|viewer)$")


class AdminInvite(BaseModel):
    """
    Schema for inviting a new admin through Clerk.

    The backend creates a pending ``admins`` row plus a Clerk
    invitation; the user finishes onboarding by clicking the
    invite link and signing in.
    """
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    role: str = Field(default="viewer", pattern=r"^(admin|editor|viewer)$")


class AdminResponse(AdminBase):
    """Schema for admin response (no secrets)."""
    id: int
    clerk_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
