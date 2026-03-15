"""
Competition service - CRUD queries for competition results
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Competition
from app.models.competition_result import CompetitionResult
from app.schemas.competition import CompetitionFilters
from app.schemas.competition_result import CompetitionResultFilters


class CompetitionService:
    @staticmethod
    async def get_results(
        db: AsyncSession, filters: CompetitionResultFilters
    ) -> Tuple[List[CompetitionResult], int]:
        conditions = []
        if filters.search:
            search = f"%{filters.search}%"
            conditions.append(
                or_(
                    CompetitionResult.archer_name.ilike(search),
                    CompetitionResult.event_name.ilike(search),
                )
            )
        if filters.equipment_class:
            conditions.append(CompetitionResult.equipment_class == filters.equipment_class)
        if filters.distance:
            conditions.append(CompetitionResult.distance == filters.distance)
        if filters.date_from:
            conditions.append(CompetitionResult.date >= filters.date_from)
        if filters.date_to:
            conditions.append(CompetitionResult.date <= filters.date_to)
        if filters.spond_id:
            conditions.append(CompetitionResult.spond_id == filters.spond_id)
        if filters.bueskyting_archer_id:
            conditions.append(
                CompetitionResult.bueskyting_archer_id == filters.bueskyting_archer_id
            )

        count_query = select(func.count(CompetitionResult.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = (await db.execute(count_query)).scalar() or 0

        query = select(CompetitionResult)
        if conditions:
            query = query.where(and_(*conditions))

        # Server-side sorting
        sort_columns = {
            "date": CompetitionResult.date,
            "archer_name": CompetitionResult.archer_name,
            "score": CompetitionResult.score,
            "ranking": CompetitionResult.ranking,
            "event_name": CompetitionResult.event_name,
        }
        sort_col = sort_columns.get(filters.sort_by, CompetitionResult.date)
        if filters.sort_dir == "asc":
            query = query.order_by(sort_col.asc().nullslast())
        else:
            query = query.order_by(sort_col.desc().nullslast())

        query = query.offset(filters.skip).limit(filters.limit)

        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_result_by_id(db: AsyncSession, result_id: int) -> Optional[CompetitionResult]:
        result = await db.execute(
            select(CompetitionResult).where(CompetitionResult.id == result_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_competitions(
        db: AsyncSession, filters: CompetitionFilters
    ) -> Tuple[List[Competition], int]:
        conditions = []
        if filters.search:
            conditions.append(Competition.name.ilike(f"%{filters.search}%"))
        if filters.date_from:
            conditions.append(Competition.date >= filters.date_from)
        if filters.date_to:
            conditions.append(Competition.date <= filters.date_to)

        count_query = select(func.count(Competition.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total = (await db.execute(count_query)).scalar() or 0

        query = select(Competition)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(Competition.date.desc().nullslast())
        query = query.offset(filters.skip).limit(filters.limit)

        result = await db.execute(query)
        return result.scalars().all(), total

    @staticmethod
    async def get_competition_by_id(db: AsyncSession, comp_id: int) -> Optional[Competition]:
        result = await db.execute(
            select(Competition).where(Competition.id == comp_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_competition_results(
        db: AsyncSession, comp_id: int
    ) -> List[CompetitionResult]:
        result = await db.execute(
            select(CompetitionResult)
            .where(CompetitionResult.competition_id == comp_id)
            .order_by(CompetitionResult.ranking.asc().nullslast())
        )
        return result.scalars().all()

    @staticmethod
    async def get_member_results(
        db: AsyncSession, spond_id: str
    ) -> List[CompetitionResult]:
        result = await db.execute(
            select(CompetitionResult)
            .where(CompetitionResult.spond_id == spond_id)
            .order_by(CompetitionResult.date.desc().nullslast())
        )
        return result.scalars().all()

    @staticmethod
    async def get_member_statistics(
        db: AsyncSession, spond_id: str
    ) -> list:
        from app.models.archer_statistics import ArcherStatistics
        result = await db.execute(
            select(ArcherStatistics)
            .where(ArcherStatistics.spond_id == spond_id)
            .order_by(ArcherStatistics.year.desc())
        )
        return result.scalars().all()
