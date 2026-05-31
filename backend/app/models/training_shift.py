"""
TrainingShift — one concrete training session on a specific date, derived from a
TrainingSessionType. Wave 1 only introduces the model + reference data; wave 2
will add the import and publish flows.
"""
from datetime import date as date_type, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.training_session_type import TrainingSessionType


SHIFT_STATUS_VALUES = ("draft", "published", "cancelled")


class TrainingShift(Base, TimestampMixin):
    __tablename__ = "training_shifts"
    __table_args__ = (
        UniqueConstraint(
            "session_type_id",
            "date",
            name="uq_training_shifts_session_type_id_date",
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'cancelled')",
            name="ck_training_shifts_status",
        ),
        Index("ix_training_shifts_session_type_id", "session_type_id"),
        Index("ix_training_shifts_date", "date"),
        Index("ix_training_shifts_leader_member_id", "leader_member_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    session_type_id: Mapped[int] = mapped_column(
        ForeignKey("training_session_types.id", ondelete="CASCADE"),
        nullable=False,
    )

    date: Mapped[date_type] = mapped_column(Date, nullable=False)

    leader_member_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
    )

    # When the importer can't resolve initials to a member, the raw value lives
    # here so the UI can surface it for manual fix-up.
    raw_initials: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    start_time_override: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time_override: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Per-shift audience override. Both NULL → fall back to the session type's
    # invite scope. `invited_member_ids` (when non-empty) wins over the
    # subgroup field.
    invited_subgroup_uids: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )
    invited_member_ids: Mapped[Optional[list[int]]] = mapped_column(
        JSON, nullable=True
    )

    # Per-shift invite scheduling override. NULL → inherit from session type
    # (and if both NULL → send immediately on publish).
    invite_lead_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    invite_send_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    spond_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Last time the reverse-sync (Spond event → this shift) wrote anything here.
    # NULL = never reconciled from Spond. Surfaced in the UI so admins can see
    # that a shift's time/leader/audience was updated from a Spond-side edit.
    last_reverse_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    session_type: Mapped["TrainingSessionType"] = relationship(back_populates="shifts")
    leader: Mapped[Optional["Member"]] = relationship(foreign_keys=[leader_member_id])

    def __repr__(self) -> str:
        return (
            f"<TrainingShift id={self.id} session_type_id={self.session_type_id} "
            f"date={self.date} status={self.status}>"
        )
