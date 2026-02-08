"""
Analytics API endpoints
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.admin import Admin
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    AttendanceTrendsResponse,
    ResponseRateData,
    EventTypeDistribution,
    MemberParticipationResponse,
    AnalyticsSummary,
    CategoryTrendsResponse,
    CategoryAttendanceComparison,
    CategoryResponseRateStats
)
from app.schemas.category import CategoryDistribution

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get overall analytics summary
    """
    service = AnalyticsService()
    return await service.get_analytics_summary(db, group_id=group_id)


@router.get("/attendance-trends", response_model=AttendanceTrendsResponse)
async def get_attendance_trends(
    period: str = Query("month", regex="^(week|month|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get attendance trends over time

    - **period**: Time period grouping (week, month, year)
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    - **group_id**: Optional group spond_id to filter by
    """
    service = AnalyticsService()
    return await service.get_attendance_trends(db, period, start_date, end_date, group_id=group_id)


@router.get("/response-rates", response_model=ResponseRateData)
async def get_response_rates(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get response rate statistics

    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    - **group_id**: Optional group spond_id to filter by
    """
    service = AnalyticsService()
    return await service.get_response_rates(db, start_date, end_date, group_id=group_id)


@router.get("/event-types", response_model=List[EventTypeDistribution])
async def get_event_type_distribution(
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get event type distribution

    - **group_id**: Optional group spond_id to filter by
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    return await service.get_event_type_distribution(db, group_id, start_date, end_date)


@router.get("/member-participation", response_model=MemberParticipationResponse)
async def get_member_participation(
    limit: int = Query(10, ge=1, le=100),
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get top members by participation

    - **limit**: Maximum number of members to return (1-100)
    - **group_id**: Optional group spond_id to filter by
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    return await service.get_member_participation(db, limit, group_id, start_date, end_date)


# Category Analytics Endpoints


@router.get("/categories/distribution", response_model=List[CategoryDistribution])
async def get_category_distribution(
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get event distribution by category

    - **group_id**: Optional group spond_id to filter by
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    results = await service.get_category_distribution(db, group_id, start_date, end_date)
    return [CategoryDistribution(**r) for r in results]


@router.get("/categories/attendance", response_model=List[CategoryAttendanceComparison])
async def get_category_attendance_comparison(
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Compare attendance rates across categories

    - **group_id**: Optional group spond_id to filter by
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    - **category_ids**: Comma-separated list of category IDs to compare
    """
    service = AnalyticsService()

    # Parse category IDs
    cat_ids = None
    if category_ids:
        cat_ids = [int(id.strip()) for id in category_ids.split(",")]

    return await service.get_category_attendance_comparison(
        db, group_id, start_date, end_date, cat_ids
    )


@router.get("/categories/trends", response_model=CategoryTrendsResponse)
async def get_category_trends(
    period: str = Query("month", regex="^(week|month|year)$"),
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    category_ids: Optional[str] = Query(None, description="Comma-separated category IDs"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get attendance trends broken down by category

    - **period**: Time period grouping (week, month, year)
    - **group_id**: Optional group spond_id to filter by
    - **category_ids**: Comma-separated list of category IDs to include
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()

    # Parse category IDs
    cat_ids = None
    if category_ids:
        cat_ids = [int(id.strip()) for id in category_ids.split(",")]

    return await service.get_category_trends(
        db, period, group_id, cat_ids, start_date, end_date
    )


@router.get("/categories/{category_id}/response-rates", response_model=CategoryResponseRateStats)
async def get_category_response_rates(
    category_id: int,
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get response rate statistics for a specific category

    - **category_id**: Category ID
    - **group_id**: Optional group spond_id to filter by
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    return await service.get_category_response_rates(
        db, category_id, group_id, start_date, end_date
    )


@router.get("/organizers")
async def get_organizer_statistics(
    limit: int = Query(10, ge=1, le=100),
    group_id: Optional[str] = Query(None, description="Filter by group spond_id"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get organizer statistics

    - **limit**: Maximum number of organizers to return (default: 10)
    - **group_id**: Optional group spond_id to filter by
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    return await service.get_organizer_statistics(db, limit, group_id, start_date, end_date)
