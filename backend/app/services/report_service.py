"""
Report Service
Handles CRUD operations, report generation, and export for saved reports
"""
import csv
import io
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.report import Report
from app.services.analytics_service import AnalyticsService
from app.services.category_service import CategoryService
from app.services.event_service import EventService


class ReportService:
    """Service for managing and generating reports"""

    @staticmethod
    async def create(
        db: AsyncSession,
        admin_id: int,
        name: str,
        report_type: str,
        configuration: Dict[str, Any],
        description: Optional[str] = None,
        is_public: bool = False,
        is_favorite: bool = False,
    ) -> Report:
        """Create a new report"""
        now = datetime.utcnow()
        report = Report(
            name=name,
            description=description,
            created_by=admin_id,
            report_type=report_type,
            configuration=configuration,
            is_public=is_public,
            is_favorite=is_favorite,
            created_at=now,
            updated_at=now,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    @staticmethod
    async def update(
        db: AsyncSession,
        report_id: int,
        admin_id: int,
        **kwargs
    ) -> Optional[Report]:
        """Update an existing report"""
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == admin_id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            return None

        # Update fields
        for key, value in kwargs.items():
            if hasattr(report, key) and value is not None:
                setattr(report, key, value)

        report.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(report)
        return report

    @staticmethod
    async def delete(db: AsyncSession, report_id: int, admin_id: int) -> bool:
        """Delete a report (only by creator)"""
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == admin_id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            return False

        await db.delete(report)
        await db.commit()
        return True

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        report_id: int,
        admin_id: Optional[int] = None
    ) -> Optional[Report]:
        """Get report by ID"""
        query = select(Report).where(Report.id == report_id)

        # If admin_id provided, check ownership or public
        if admin_id is not None:
            query = query.where(
                or_(
                    Report.created_by == admin_id,
                    Report.is_public == True
                )
            )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_reports(
        db: AsyncSession,
        admin_id: int,
        include_public: bool = True,
        favorites_only: bool = False,
        report_type: Optional[str] = None
    ) -> List[Report]:
        """Get reports for a user"""
        conditions = []

        if include_public:
            conditions.append(
                or_(
                    Report.created_by == admin_id,
                    Report.is_public == True
                )
            )
        else:
            conditions.append(Report.created_by == admin_id)

        if favorites_only:
            conditions.append(Report.is_favorite == True)

        if report_type:
            conditions.append(Report.report_type == report_type)

        query = select(Report).where(and_(*conditions)).order_by(Report.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def toggle_favorite(
        db: AsyncSession,
        report_id: int,
        admin_id: int
    ) -> Optional[Report]:
        """Toggle favorite status for a report"""
        result = await db.execute(
            select(Report).where(
                and_(
                    Report.id == report_id,
                    Report.created_by == admin_id
                )
            )
        )
        report = result.scalar_one_or_none()

        if not report:
            return None

        report.is_favorite = not report.is_favorite
        report.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(report)
        return report

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        report_id: int
    ) -> Dict[str, Any]:
        """
        Generate report data based on configuration

        Args:
            db: Database session
            report_id: Report ID to generate

        Returns:
            Dictionary containing report data
        """
        # Get report
        result = await db.execute(
            select(Report).where(Report.id == report_id)
        )
        report = result.scalar_one_or_none()

        if not report:
            raise ValueError(f"Report {report_id} not found")

        config = report.configuration
        report_type = report.report_type

        # Extract common parameters
        date_range = config.get("date_range", {})
        start_date = datetime.fromisoformat(date_range.get("start")) if date_range.get("start") else None
        end_date = datetime.fromisoformat(date_range.get("end")) if date_range.get("end") else None
        group_ids = config.get("group_ids", [])
        category_ids = config.get("category_ids", [])
        metrics = config.get("metrics", [])

        # Initialize report data
        report_data = {
            "report_id": report_id,
            "report_name": report.name,
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "configuration": config,
            "data": {},
        }

        # Initialize analytics service
        analytics_service = AnalyticsService()

        # Generate data based on report type and metrics
        if report_type == "category_breakdown":
            # Category distribution
            if "category_distribution" in metrics or not metrics:
                category_stats = await CategoryService.get_category_stats(
                    db,
                    group_id=group_ids[0] if group_ids else None,
                    start_date=start_date,
                    end_date=end_date
                )
                report_data["data"]["category_distribution"] = category_stats

        elif report_type == "attendance_trends":
            # Attendance trends
            period = config.get("period", "month")
            trends = await analytics_service.get_attendance_trends(
                db,
                period=period,
                start_date=start_date,
                end_date=end_date,
                group_id=group_ids[0] if group_ids else None
            )
            report_data["data"]["attendance_trends"] = trends

        elif report_type == "comprehensive":
            # Multiple metrics
            group_id = group_ids[0] if group_ids else None

            if "summary" in metrics:
                summary = await analytics_service.get_analytics_summary(db, group_id=group_id)
                report_data["data"]["summary"] = summary

            if "category_distribution" in metrics:
                category_stats = await CategoryService.get_category_stats(
                    db, group_id=group_id, start_date=start_date, end_date=end_date
                )
                report_data["data"]["category_distribution"] = category_stats

            if "attendance_trends" in metrics:
                trends = await analytics_service.get_attendance_trends(
                    db,
                    period="month",
                    start_date=start_date,
                    end_date=end_date,
                    group_id=group_id
                )
                report_data["data"]["attendance_trends"] = trends

            if "response_rates" in metrics:
                response_rates = await analytics_service.get_response_rates(
                    db, start_date=start_date, end_date=end_date, group_id=group_id
                )
                report_data["data"]["response_rates"] = response_rates

            if "member_participation" in metrics:
                # Note: get_member_participation doesn't support date filtering
                member_stats = await analytics_service.get_member_participation(
                    db,
                    group_id=group_id,
                    limit=None  # Get all members for detailed view
                )
                # Convert Pydantic model to dict for JSON serialization
                report_data["data"]["member_participation"] = {
                    "members": [
                        {
                            "member_id": m.member_id,
                            "member_name": m.member_name,
                            "total_events": m.total_events,
                            "attended": m.attended,
                            "declined": m.declined,
                            "no_response": m.no_response,
                            "attendance_rate": m.attendance_rate
                        }
                        for m in member_stats.members
                    ],
                    "total": member_stats.total
                }

            if "event_details" in metrics:
                # Get events in report date range with response details
                events = await EventService.get_events_with_attendance(
                    db,
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date,
                    category_ids=category_ids if category_ids else None
                )
                report_data["data"]["event_details"] = events

            if "category_details" in metrics:
                # Get category stats with event counts
                category_stats = await CategoryService.get_category_stats(
                    db,
                    group_id=group_id,
                    start_date=start_date,
                    end_date=end_date
                )

                # Enhance with attendance data
                from app.models.event import Event

                enhanced_stats = []
                for cat_stat in category_stats:
                    cat_id = cat_stat["category_id"]

                    # Get events for this category
                    events_query = select(Event).where(Event.category_id == cat_id)
                    if start_date:
                        events_query = events_query.where(Event.start_time >= start_date)
                    if end_date:
                        events_query = events_query.where(Event.start_time <= end_date)
                    if group_id:
                        events_query = events_query.where(Event.group_id == group_id)

                    events_result = await db.execute(events_query)
                    cat_events = events_result.scalars().all()

                    # Calculate attendance stats
                    total_responses = 0
                    total_accepted = 0
                    total_declined = 0

                    for event in cat_events:
                        # Extract responses array (supports both old and new formats)
                        responses = []
                        if event.responses:
                            # New format: has responses array
                            if "responses" in event.responses:
                                responses = event.responses["responses"]
                            # Old format: use UID arrays
                            else:
                                for uid in event.responses.get("accepted_uids", []):
                                    responses.append({"answer": "accepted"})
                                for uid in event.responses.get("declined_uids", []):
                                    responses.append({"answer": "declined"})
                                for uid in event.responses.get("unanswered_uids", []):
                                    responses.append({"answer": "unanswered"})

                        total_responses += len(responses)
                        total_accepted += sum(1 for r in responses if r.get("answer") == "accepted")
                        total_declined += sum(1 for r in responses if r.get("answer") == "declined")

                    avg_rate = (total_accepted / total_responses * 100) if total_responses > 0 else 0

                    enhanced_stats.append({
                        "category_id": cat_id,
                        "category_name": cat_stat["category_name"],
                        "color": cat_stat["color"],
                        "icon": cat_stat.get("icon"),
                        "total_events": cat_stat["event_count"],
                        "avg_attendance_rate": round(avg_rate, 1),
                        "total_responses": total_responses,
                        "accepted": total_accepted,
                        "declined": total_declined
                    })

                report_data["data"]["category_details"] = enhanced_stats

            if "attendance_log" in metrics:
                # Reuse attendance_trends but with daily granularity
                log = await analytics_service.get_attendance_trends(
                    db,
                    period="day",  # Daily granularity
                    start_date=start_date,
                    end_date=end_date,
                    group_id=group_id
                )
                # Convert Pydantic model to dict for JSON serialization
                report_data["data"]["attendance_log"] = {
                    "period": log.period,
                    "data": [
                        {
                            "date": entry.date,
                            "total_events": entry.total_events,
                            "accepted": entry.accepted,
                            "declined": entry.declined,
                            "unanswered": entry.unanswered,
                            "acceptance_rate": round((entry.accepted / (entry.accepted + entry.declined) * 100), 1)
                                if (entry.accepted + entry.declined) > 0 else 0
                        }
                        for entry in log.data
                    ]
                }

            if "organizer_statistics" in metrics:
                # Get organizer statistics
                organizer_stats = await analytics_service.get_organizer_statistics(
                    db,
                    limit=None,  # Get all organizers for detailed view
                    group_id=group_id
                )
                report_data["data"]["organizer_statistics"] = organizer_stats

        # Update last_generated_at timestamp
        report.last_generated_at = datetime.utcnow()
        await db.commit()

        return report_data

    @staticmethod
    async def export_report_csv(
        db: AsyncSession,
        report_id: int
    ) -> bytes:
        """
        Export report data as CSV

        Args:
            db: Database session
            report_id: Report ID to export

        Returns:
            CSV data as bytes
        """
        # Generate report data
        report_data = await ReportService.generate_report(db, report_id)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([f"Report: {report_data['report_name']}"])
        writer.writerow([f"Generated: {report_data['generated_at']}"])
        writer.writerow([f"Type: {report_data['report_type']}"])
        writer.writerow([])

        # Write data based on what's available
        data = report_data.get("data", {})

        # Category distribution
        if "category_distribution" in data:
            writer.writerow(["Category Distribution"])
            writer.writerow(["Category", "Event Count", "Percentage"])
            for item in data["category_distribution"]:
                writer.writerow([
                    item["category_name"],
                    item["event_count"],
                    f"{item['percentage']:.2f}%"
                ])
            writer.writerow([])

        # Attendance trends
        if "attendance_trends" in data:
            writer.writerow(["Attendance Trends"])
            writer.writerow(["Date", "Total Events", "Accepted", "Declined", "Unanswered"])
            trends = data["attendance_trends"]
            # Handle both dict and Pydantic model
            trend_points = trends.data if hasattr(trends, 'data') else trends.get("data", [])
            for point in trend_points:
                # Handle both dict and Pydantic model
                if hasattr(point, 'date'):
                    writer.writerow([
                        point.date,
                        point.total_events,
                        point.accepted,
                        point.declined,
                        point.unanswered
                    ])
                else:
                    writer.writerow([
                        point["date"],
                        point["total_events"],
                        point["accepted"],
                        point["declined"],
                        point["unanswered"]
                    ])
            writer.writerow([])

        # Response rates
        if "response_rates" in data:
            writer.writerow(["Response Rates"])
            rates = data["response_rates"]
            # Handle both dict and Pydantic model
            if hasattr(rates, 'total_responses'):
                writer.writerow(["Total Responses", rates.total_responses])
                writer.writerow(["Accepted", f"{rates.accepted} ({rates.accepted_percentage:.2f}%)"])
                writer.writerow(["Declined", f"{rates.declined} ({rates.declined_percentage:.2f}%)"])
                writer.writerow(["Response Rate", f"{rates.response_rate:.2f}%"])
            else:
                writer.writerow(["Total Responses", rates["total_responses"]])
                writer.writerow(["Accepted", f"{rates['accepted']} ({rates['accepted_percentage']:.2f}%)"])
                writer.writerow(["Declined", f"{rates['declined']} ({rates['declined_percentage']:.2f}%)"])
                writer.writerow(["Response Rate", f"{rates['response_rate']:.2f}%"])
            writer.writerow([])

        # Summary
        if "summary" in data:
            writer.writerow(["Summary Statistics"])
            summary = data["summary"]
            writer.writerow(["Total Events", summary["total_events"]])
            writer.writerow(["Upcoming Events", summary["upcoming_events"]])
            writer.writerow(["Past Events", summary["past_events"]])
            writer.writerow(["Total Members", summary["total_members"]])
            writer.writerow(["Average Attendance", f"{summary['average_attendance_rate']:.2f}%"])

        # Convert to bytes
        csv_content = output.getvalue()
        return csv_content.encode('utf-8')
