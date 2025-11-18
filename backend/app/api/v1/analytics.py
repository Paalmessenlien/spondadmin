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
    AnalyticsSummary
)

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get overall analytics summary
    """
    service = AnalyticsService()
    return await service.get_analytics_summary(db)


@router.get("/attendance-trends", response_model=AttendanceTrendsResponse)
async def get_attendance_trends(
    period: str = Query("month", regex="^(week|month|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get attendance trends over time

    - **period**: Time period grouping (week, month, year)
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    return await service.get_attendance_trends(db, period, start_date, end_date)


@router.get("/response-rates", response_model=ResponseRateData)
async def get_response_rates(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get response rate statistics

    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    service = AnalyticsService()
    return await service.get_response_rates(db, start_date, end_date)


@router.get("/event-types", response_model=List[EventTypeDistribution])
async def get_event_type_distribution(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get event type distribution
    """
    service = AnalyticsService()
    return await service.get_event_type_distribution(db)


@router.get("/member-participation", response_model=MemberParticipationResponse)
async def get_member_participation(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_user)
):
    """
    Get top members by participation

    - **limit**: Maximum number of members to return (1-100)
    """
    service = AnalyticsService()
    return await service.get_member_participation(db, limit)
