"""
Analytics Service
Provides analytics and reporting data
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict, Counter

from app.models.event import Event
from app.models.member import Member
from app.schemas.analytics import (
    AttendanceTrendPoint,
    AttendanceTrendsResponse,
    ResponseRateData,
    EventTypeDistribution,
    MemberParticipationStat,
    MemberParticipationResponse,
    AnalyticsSummary
)


class AnalyticsService:
    """Service for analytics operations"""

    async def get_attendance_trends(
        self,
        db: AsyncSession,
        period: str = "month",  # "week", "month", "year"
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AttendanceTrendsResponse:
        """Get attendance trends over time"""

        # Default date range: last 3 months
        if not end_date:
            end_date = datetime.now(timezone.utc)
        if not start_date:
            if period == "week":
                start_date = end_date - timedelta(weeks=12)
            elif period == "month":
                start_date = end_date - timedelta(days=90)
            else:  # year
                start_date = end_date - timedelta(days=365)

        # Get all events in date range
        stmt = select(Event).where(
            and_(
                Event.start_time >= start_date,
                Event.start_time <= end_date
            )
        ).order_by(Event.start_time)

        result = await db.execute(stmt)
        events = result.scalars().all()

        # Group events by period
        trends: Dict[str, AttendanceTrendPoint] = {}

        for event in events:
            # Determine period key
            if period == "week":
                # ISO week format
                period_key = event.start_time.strftime("%Y-W%V")
            elif period == "month":
                period_key = event.start_time.strftime("%Y-%m")
            else:  # year
                period_key = event.start_time.strftime("%Y")

            if period_key not in trends:
                trends[period_key] = AttendanceTrendPoint(
                    date=period_key,
                    total_events=0,
                    accepted=0,
                    declined=0,
                    unanswered=0
                )

            trends[period_key].total_events += 1

            # Count responses
            if event.responses:
                for response in event.responses.get("responses", []):
                    answer = response.get("answer", "").lower()
                    if answer == "accepted":
                        trends[period_key].accepted += 1
                    elif answer == "declined":
                        trends[period_key].declined += 1
                    elif answer in ["unanswered", "waitinglistavailable", "waiting"]:
                        trends[period_key].unanswered += 1

        return AttendanceTrendsResponse(
            period=period,
            data=sorted(trends.values(), key=lambda x: x.date)
        )

    async def get_response_rates(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ResponseRateData:
        """Get overall response rate statistics"""

        stmt = select(Event)
        if start_date and end_date:
            stmt = stmt.where(
                and_(
                    Event.start_time >= start_date,
                    Event.start_time <= end_date
                )
            )

        result = await db.execute(stmt)
        events = result.scalars().all()

        total_responses = 0
        accepted = 0
        declined = 0
        unanswered = 0
        no_answer = 0

        for event in events:
            if event.responses and "responses" in event.responses:
                for response in event.responses["responses"]:
                    total_responses += 1
                    answer = response.get("answer", "").lower()

                    if answer == "accepted":
                        accepted += 1
                    elif answer == "declined":
                        declined += 1
                    elif answer in ["unanswered", "waitinglistavailable", "waiting"]:
                        unanswered += 1
                    else:
                        no_answer += 1

        # Calculate percentages
        accepted_percentage = (accepted / total_responses * 100) if total_responses > 0 else 0
        declined_percentage = (declined / total_responses * 100) if total_responses > 0 else 0
        response_rate = ((accepted + declined) / total_responses * 100) if total_responses > 0 else 0

        return ResponseRateData(
            total_responses=total_responses,
            accepted=accepted,
            declined=declined,
            unanswered=unanswered,
            no_answer=no_answer,
            accepted_percentage=round(accepted_percentage, 2),
            declined_percentage=round(declined_percentage, 2),
            response_rate=round(response_rate, 2)
        )

    async def get_event_type_distribution(
        self,
        db: AsyncSession
    ) -> List[EventTypeDistribution]:
        """Get distribution of event types"""

        stmt = select(Event.event_type, func.count(Event.id)).group_by(Event.event_type)
        result = await db.execute(stmt)
        type_counts = result.all()

        total_events = sum(count for _, count in type_counts)

        distribution = []
        for event_type, count in type_counts:
            percentage = (count / total_events * 100) if total_events > 0 else 0
            distribution.append(
                EventTypeDistribution(
                    event_type=event_type or "Unknown",
                    count=count,
                    percentage=round(percentage, 2)
                )
            )

        return sorted(distribution, key=lambda x: x.count, reverse=True)

    async def get_member_participation(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> MemberParticipationResponse:
        """Get top members by participation"""

        # Get all members
        members_stmt = select(Member)
        members_result = await db.execute(members_stmt)
        members = members_result.scalars().all()

        # Get all events
        events_stmt = select(Event)
        events_result = await db.execute(events_stmt)
        events = events_result.scalars().all()

        # Build participation stats
        member_stats: Dict[str, Dict[str, Any]] = {}

        for member in members:
            member_id = member.spond_id
            member_stats[member_id] = {
                "member_id": member.id,
                "member_name": f"{member.first_name} {member.last_name}",
                "total_events": 0,
                "attended": 0,
                "declined": 0,
                "no_response": 0
            }

        # Count responses for each member
        for event in events:
            if event.responses and "responses" in event.responses:
                for response in event.responses["responses"]:
                    profile_id = response.get("profile", {}).get("id")

                    if profile_id in member_stats:
                        member_stats[profile_id]["total_events"] += 1

                        answer = response.get("answer", "").lower()
                        if answer == "accepted":
                            member_stats[profile_id]["attended"] += 1
                        elif answer == "declined":
                            member_stats[profile_id]["declined"] += 1
                        else:
                            member_stats[profile_id]["no_response"] += 1

        # Create participation stats
        participation_stats = []
        for stats in member_stats.values():
            if stats["total_events"] > 0:
                attendance_rate = (stats["attended"] / stats["total_events"] * 100)
                participation_stats.append(
                    MemberParticipationStat(
                        member_id=stats["member_id"],
                        member_name=stats["member_name"],
                        total_events=stats["total_events"],
                        attended=stats["attended"],
                        declined=stats["declined"],
                        no_response=stats["no_response"],
                        attendance_rate=round(attendance_rate, 2)
                    )
                )

        # Sort by total events participated
        participation_stats.sort(key=lambda x: x.total_events, reverse=True)

        return MemberParticipationResponse(
            members=participation_stats[:limit],
            total=len(participation_stats)
        )

    async def get_analytics_summary(
        self,
        db: AsyncSession
    ) -> AnalyticsSummary:
        """Get overall analytics summary"""

        # Get counts
        events_stmt = select(func.count(Event.id))
        events_result = await db.execute(events_stmt)
        total_events = events_result.scalar() or 0

        # Upcoming events
        now = datetime.now(timezone.utc)
        upcoming_stmt = select(func.count(Event.id)).where(Event.start_time >= now)
        upcoming_result = await db.execute(upcoming_stmt)
        upcoming_events = upcoming_result.scalar() or 0

        past_events = total_events - upcoming_events

        # Total members
        members_stmt = select(func.count(Member.id))
        members_result = await db.execute(members_stmt)
        total_members = members_result.scalar() or 0

        # Get response rates
        response_rates = await self.get_response_rates(db)

        # Get event type distribution
        event_distribution = await self.get_event_type_distribution(db)

        # Get most active members (top 5)
        member_participation = await self.get_member_participation(db, limit=5)

        return AnalyticsSummary(
            total_events=total_events,
            upcoming_events=upcoming_events,
            past_events=past_events,
            total_members=total_members,
            total_responses=response_rates.total_responses,
            average_attendance_rate=response_rates.accepted_percentage,
            most_active_members=member_participation.members,
            event_type_distribution=event_distribution
        )
