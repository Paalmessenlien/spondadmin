"""
Event model for caching Spond events
"""
from datetime import datetime, time
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, Time, JSON, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    """
    Cached event data from Spond API
    """
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Spond event ID
    spond_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Group association (spond_id of the group this event belongs to)
    group_id: Mapped[str] = mapped_column(String(255), nullable=True, index=True)

    # Category association
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("event_categories.id"), nullable=True, index=True)
    category_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Manual assignment flag

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

    # Audience override — list of Spond subgroup uids to narrow the invite
    # to. NULL / empty → invite the whole group. Mirrors
    # training_shifts.invited_subgroup_uids.
    invited_subgroup_uids: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )

    # Invite scheduling intent. NULL on either field → send immediately on
    # publish. The resolved absolute datetime is written to `invite_time`
    # above and sent to Spond as `inviteTime`. Mirrors training_shifts.
    invite_lead_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    invite_send_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

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

    # Relationships
    category = relationship("EventCategory", back_populates="events")

    def __repr__(self) -> str:
        return f"<Event {self.spond_id}: {self.heading}>"
