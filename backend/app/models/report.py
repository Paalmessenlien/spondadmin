"""
Saved report configuration model
"""
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, Boolean, JSON, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    """
    Saved report configuration model.

    Attributes:
        id: Primary key
        name: Report name
        description: Optional detailed description
        created_by: Foreign key to admin user
        report_type: Type of report (e.g., "category_breakdown", "attendance_trends")
        configuration: JSON field containing report parameters
        is_public: Whether report is shared with all admins
        is_favorite: Whether report is marked as favorite by creator
        last_generated_at: Timestamp of last report generation

    Configuration JSON structure:
        {
            "date_range": {
                "start": "2025-01-01",
                "end": "2025-12-31"
            },
            "group_ids": ["group_123", "group_456"],
            "category_ids": [1, 2, 3],
            "metrics": [
                "attendance_rate",
                "response_distribution",
                "category_breakdown"
            ],
            "chart_types": ["line", "doughnut", "bar"],
            "comparison_period": "previous_year"
        }
    """
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("admins.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    creator = relationship("Admin", backref="reports")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, name='{self.name}', type='{self.report_type}')>"
