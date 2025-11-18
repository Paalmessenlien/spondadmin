"""
Event model for caching Spond events
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    """
    Cached event data from Spond API
    """
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Spond event ID
    spond_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Event details
    heading: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # AVAILABILITY, EVENT, RECURRING

    # Timestamps
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    invite_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Status
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Location
    location_address: Mapped[str] = mapped_column(String(500), nullable=True)
    location_latitude: Mapped[float] = mapped_column(nullable=True)
    location_longitude: Mapped[float] = mapped_column(nullable=True)

    # Participants
    max_accepted: Mapped[int] = mapped_column(default=0, nullable=False)

    # Responses (stored as JSON)
    responses: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Raw data from Spond API
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Sync metadata
    sync_status: Mapped[str] = mapped_column(
        String(50),
        default="synced",
        nullable=False,
        index=True
    )  # synced, pending, local_only, error
    sync_error: Mapped[str] = mapped_column(Text, nullable=True)  # Error message if sync failed
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Event {self.spond_id}: {self.heading}>"
