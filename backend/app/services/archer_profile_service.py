"""
Archer Profile service - CRUD operations for archery-specific member data
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.archer_profile import ArcherProfile
from app.schemas.archer_profile import ArcherProfileCreate, ArcherProfileUpdate


class ArcherProfileService:
    @staticmethod
    async def get_by_spond_id(db: AsyncSession, spond_id: str) -> Optional[ArcherProfile]:
        result = await db.execute(
            select(ArcherProfile).where(ArcherProfile.spond_id == spond_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession, spond_id: str, data: ArcherProfileCreate
    ) -> ArcherProfile:
        now = datetime.now(timezone.utc)
        profile = ArcherProfile(
            spond_id=spond_id,
            created_at=now,
            updated_at=now,
            **data.model_dump(exclude_unset=True),
        )
        db.add(profile)
        return profile

    @staticmethod
    async def update(
        db: AsyncSession, profile: ArcherProfile, data: ArcherProfileUpdate
    ) -> ArcherProfile:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(profile, key, value)
        profile.updated_at = datetime.now(timezone.utc)
        return profile

    @staticmethod
    async def delete(db: AsyncSession, profile: ArcherProfile) -> None:
        await db.delete(profile)
