"""
Archery Record service - CRUD queries for archery records
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.archery_record import ArcheryRecord
from app.schemas.archery_record import ArcheryRecordFilters


class ArcheryRecordService:
    @staticmethod
    async def get_records(
        db: AsyncSession, filters: ArcheryRecordFilters
    ) -> Tuple[List[ArcheryRecord], int]:
        conditions = [ArcheryRecord.is_current == True]
        if filters.division:
            conditions.append(ArcheryRecord.division == filters.division)
        if filters.category:
            conditions.append(ArcheryRecord.category == filters.category)
        if filters.record_type:
            conditions.append(ArcheryRecord.record_type == filters.record_type)

        count_query = select(func.count(ArcheryRecord.id)).where(and_(*conditions))
        total = (await db.execute(count_query)).scalar() or 0

        query = (
            select(ArcheryRecord)
            .where(and_(*conditions))
            .order_by(ArcheryRecord.division, ArcheryRecord.category, ArcheryRecord.round_type)
            .offset(filters.skip)
            .limit(filters.limit)
        )
        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_member_records(
        db: AsyncSession, spond_id: str
    ) -> List[ArcheryRecord]:
        result = await db.execute(
            select(ArcheryRecord)
            .where(
                ArcheryRecord.spond_id == spond_id,
                ArcheryRecord.is_current == True,
            )
            .order_by(ArcheryRecord.division, ArcheryRecord.round_type)
        )
        return result.scalars().all()

    @staticmethod
    async def get_filter_values(db: AsyncSession) -> dict:
        """Get available filter values for records."""
        divisions = await db.execute(
            select(distinct(ArcheryRecord.division))
            .where(ArcheryRecord.is_current == True)
            .order_by(ArcheryRecord.division)
        )
        categories = await db.execute(
            select(distinct(ArcheryRecord.category))
            .where(ArcheryRecord.is_current == True)
            .order_by(ArcheryRecord.category)
        )
        return {
            "divisions": [r[0] for r in divisions.all() if r[0]],
            "categories": [r[0] for r in categories.all() if r[0]],
            "record_types": ["individual", "team"],
        }
