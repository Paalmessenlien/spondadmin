"""
Analytics Pydantic schemas
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AttendanceTrendPoint(BaseModel):
    """Single point in attendance trend"""
    date: str  # ISO format date
    total_events: int
    accepted: int
    declined: int
    unanswered: int


class AttendanceTrendsResponse(BaseModel):
    """Response for attendance trends over time"""
    period: str  # "week", "month", "year"
    data: List[AttendanceTrendPoint]


class ResponseRateData(BaseModel):
    """Response rate statistics"""
    total_responses: int
    accepted: int
    declined: int
    unanswered: int
    no_answer: int
    accepted_percentage: float
    declined_percentage: float
    response_rate: float  # percentage of people who responded


class EventTypeDistribution(BaseModel):
    """Distribution of event types"""
    event_type: str
    count: int
    percentage: float


class MemberParticipationStat(BaseModel):
    """Individual member participation statistics"""
    member_id: int
    member_name: str
    total_events: int
    attended: int
    declined: int
    no_response: int
    attendance_rate: float


class MemberParticipationResponse(BaseModel):
    """Top members by participation"""
    members: List[MemberParticipationStat]
    total: int


class AnalyticsSummary(BaseModel):
    """Overall analytics summary"""
    total_events: int
    upcoming_events: int
    past_events: int
    total_members: int
    total_responses: int
    average_attendance_rate: float
    most_active_members: List[MemberParticipationStat]
    event_type_distribution: List[EventTypeDistribution]
