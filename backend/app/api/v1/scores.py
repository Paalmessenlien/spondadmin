"""
Scores & Records API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.admin import Admin
from app.models.competition import Competition
from app.models.competition_result import CompetitionResult
from app.models.archery_record import ArcheryRecord
from app.models.archer_statistics import ArcherStatistics
from app.models.unmatched_archer import UnmatchedArcher
from app.models.bueskyting_scrape_log import BueskytingScrapeLog
from app.services.competition_service import CompetitionService
from app.services.archery_record_service import ArcheryRecordService
from app.schemas.competition import (
    CompetitionResponse,
    CompetitionListResponse,
    CompetitionFilters,
)
from app.schemas.competition_result import (
    CompetitionResultResponse,
    CompetitionResultListResponse,
    CompetitionResultFilters,
)
from app.schemas.archery_record import (
    ArcheryRecordResponse,
    ArcheryRecordListResponse,
    ArcheryRecordFilters,
)
from app.schemas.archer_statistics import (
    ArcherStatisticsResponse,
    ArcherStatisticsListResponse,
)
from app.schemas.scrape import ScoresSummaryResponse

router = APIRouter()


# ──────────────────────────────────────────────
# Results
# ──────────────────────────────────────────────
@router.get("/results", response_model=CompetitionResultListResponse)
async def list_results(
    search: str | None = Query(None),
    equipment_class: str | None = Query(None),
    distance: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    spond_id: str | None = Query(None),
    bueskyting_archer_id: str | None = Query(None),
    sort_by: str = Query("date"),
    sort_dir: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List competition results with filtering and sorting."""
    from datetime import date as date_type

    filters = CompetitionResultFilters(
        search=search,
        equipment_class=equipment_class,
        distance=distance,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        spond_id=spond_id,
        bueskyting_archer_id=bueskyting_archer_id,
        sort_by=sort_by,
        sort_dir=sort_dir,
        skip=skip,
        limit=limit,
    )
    results, total = await CompetitionService.get_results(db, filters)
    return CompetitionResultListResponse(
        results=[CompetitionResultResponse.model_validate(r) for r in results],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/results/{result_id}", response_model=CompetitionResultResponse)
async def get_result(
    result_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single competition result."""
    result = await CompetitionService.get_result_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return CompetitionResultResponse.model_validate(result)


# ──────────────────────────────────────────────
# Competitions
# ──────────────────────────────────────────────
@router.get("/competitions", response_model=CompetitionListResponse)
async def list_competitions(
    search: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List competitions."""
    from datetime import date as date_type

    filters = CompetitionFilters(
        search=search,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        skip=skip,
        limit=limit,
    )
    competitions, total = await CompetitionService.get_competitions(db, filters)
    return CompetitionListResponse(
        competitions=[CompetitionResponse.model_validate(c) for c in competitions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/competitions/{comp_id}")
async def get_competition(
    comp_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get competition details with its results."""
    comp = await CompetitionService.get_competition_by_id(db, comp_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    results = await CompetitionService.get_competition_results(db, comp_id)
    return {
        "competition": CompetitionResponse.model_validate(comp),
        "results": [CompetitionResultResponse.model_validate(r) for r in results],
    }


# ──────────────────────────────────────────────
# Records
# ──────────────────────────────────────────────
@router.get("/records", response_model=ArcheryRecordListResponse)
async def list_records(
    division: str | None = Query(None),
    category: str | None = Query(None),
    record_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List archery records."""
    filters = ArcheryRecordFilters(
        division=division,
        category=category,
        record_type=record_type,
        skip=skip,
        limit=limit,
    )
    records, total = await ArcheryRecordService.get_records(db, filters)
    return ArcheryRecordListResponse(
        records=[ArcheryRecordResponse.model_validate(r) for r in records],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/records/filters")
async def get_record_filters(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get available filter values for records."""
    return await ArcheryRecordService.get_filter_values(db)


# ──────────────────────────────────────────────
# Statistics
# ──────────────────────────────────────────────
@router.get("/statistics", response_model=ArcherStatisticsListResponse)
async def list_statistics(
    year: int | None = Query(None),
    spond_id: str | None = Query(None),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List archer statistics."""
    conditions = []
    if year:
        conditions.append(ArcherStatistics.year == year)
    if spond_id:
        conditions.append(ArcherStatistics.spond_id == spond_id)

    query = select(ArcherStatistics)
    if conditions:
        from sqlalchemy import and_
        query = query.where(and_(*conditions))
    query = query.order_by(ArcherStatistics.year.desc(), ArcherStatistics.starts.desc())

    result = await db.execute(query)
    stats = result.scalars().all()

    return ArcherStatisticsListResponse(
        statistics=[ArcherStatisticsResponse.model_validate(s) for s in stats],
        total=len(stats),
    )


# ──────────────────────────────────────────────
# Member-specific
# ──────────────────────────────────────────────
@router.get("/members/{spond_id}/results")
async def get_member_results(
    spond_id: str,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get competition results for a member."""
    results = await CompetitionService.get_member_results(db, spond_id)
    return {
        "results": [CompetitionResultResponse.model_validate(r) for r in results],
        "total": len(results),
    }


@router.get("/members/{spond_id}/statistics")
async def get_member_statistics(
    spond_id: str,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get yearly statistics for a member."""
    stats = await CompetitionService.get_member_statistics(db, spond_id)
    return {
        "statistics": [ArcherStatisticsResponse.model_validate(s) for s in stats],
        "total": len(stats),
    }


@router.get("/members/{spond_id}/records")
async def get_member_records(
    spond_id: str,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get records held by a member."""
    records = await ArcheryRecordService.get_member_records(db, spond_id)
    return {
        "records": [ArcheryRecordResponse.model_validate(r) for r in records],
        "total": len(records),
    }


# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────
@router.get("/summary", response_model=ScoresSummaryResponse)
async def get_scores_summary(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary counts for the scores dashboard."""
    total_results = (
        await db.execute(select(func.count(CompetitionResult.id)))
    ).scalar() or 0

    total_competitions = (
        await db.execute(select(func.count(Competition.id)))
    ).scalar() or 0

    total_records = (
        await db.execute(
            select(func.count(ArcheryRecord.id)).where(ArcheryRecord.is_current == True)
        )
    ).scalar() or 0

    total_archers = (
        await db.execute(
            select(func.count(func.distinct(CompetitionResult.bueskyting_archer_id)))
        )
    ).scalar() or 0

    unmatched_count = (
        await db.execute(
            select(func.count(UnmatchedArcher.id)).where(
                UnmatchedArcher.dismissed == False
            )
        )
    ).scalar() or 0

    latest_log = await db.execute(
        select(BueskytingScrapeLog.created_at)
        .where(BueskytingScrapeLog.status == "completed")
        .order_by(BueskytingScrapeLog.created_at.desc())
        .limit(1)
    )
    latest_row = latest_log.first()

    return ScoresSummaryResponse(
        total_results=total_results,
        total_competitions=total_competitions,
        total_records=total_records,
        total_archers=total_archers,
        unmatched_archers=unmatched_count,
        latest_scrape=latest_row[0] if latest_row else None,
    )
