"""
External Event model - upcoming competitions from bueskyting.no terminliste
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Date, DateTime, Text, Float, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ExternalEvent(Base, TimestampMixin):
    """An upcoming competition/event scraped from bueskyting.no terminliste"""
    __tablename__ = "external_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bueskyting_event_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    event_type_raw: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    organizer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    distance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registration_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    info_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    results_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    registration_deadline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registration_type_raw: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fees: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    # AI-generated fields
    ai_event_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Cross-links to local entities (advisory; confirmed in the UI). A local
    # Spond Event the club created for this competition, and/or the Competition
    # row holding its results. Both ON DELETE SET NULL via the migration.
    linked_event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )
    linked_competition_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competitions.id", ondelete="SET NULL"), nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ExternalEvent id={self.id} name={self.name} bueskyting_id={self.bueskyting_event_id}>"
