"""
Archer Profile schemas for API requests and responses
"""
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class ArcherProfileBase(BaseModel):
    """Base archer profile schema"""
    bow_type: Optional[str] = Field(None, max_length=50)
    division: Optional[str] = Field(None, max_length=50)
    skill_level: Optional[str] = Field(None, max_length=50)
    club_join_date: Optional[date] = None
    archery_gb_number: Optional[str] = Field(None, max_length=50)
    current_classification: Optional[str] = Field(None, max_length=50)
    current_handicap: Optional[int] = Field(None, ge=0, le=150)
    notes: Optional[str] = None
    bueskyting_id: Optional[str] = Field(None, max_length=50)


class ArcherProfileCreate(ArcherProfileBase):
    """Schema for creating an archer profile"""
    pass


class ArcherProfileUpdate(ArcherProfileBase):
    """Schema for updating an archer profile"""
    pass


class ArcherProfileResponse(ArcherProfileBase):
    """Schema for archer profile response"""
    id: int
    spond_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
