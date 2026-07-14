"""
Schemas for access groups and editable role defaults.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.core.modules import ALL_MODULE_KEYS

_ROLE_PATTERN = r"^(admin|editor|viewer|kasserer)$"


def _clean(v: Optional[List[str]]) -> Optional[List[str]]:
    if v is None:
        return None
    return sorted({m for m in v if m in ALL_MODULE_KEYS})


class AccessGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    role: str = Field(..., pattern=_ROLE_PATTERN)
    modules: List[str] = Field(default_factory=list)

    @field_validator("modules")
    @classmethod
    def _v(cls, v):
        return _clean(v) or []


class AccessGroupCreate(AccessGroupBase):
    pass


class AccessGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    role: Optional[str] = Field(None, pattern=_ROLE_PATTERN)
    modules: Optional[List[str]] = None

    @field_validator("modules")
    @classmethod
    def _v(cls, v):
        return _clean(v)


class AccessGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    role: str
    modules: List[str]
    member_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleDefaultResponse(BaseModel):
    role: str
    modules: List[str]


class RoleDefaultUpdate(BaseModel):
    modules: List[str] = Field(default_factory=list)

    @field_validator("modules")
    @classmethod
    def _v(cls, v):
        return _clean(v) or []
