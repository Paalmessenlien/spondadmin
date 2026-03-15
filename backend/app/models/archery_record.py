"""
Archery Record model - Norwegian archery records
"""
from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, Date, Text, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ArcheryRecord(Base, TimestampMixin):
    """A Norwegian archery record from rekord.bueskyting.no"""
    __tablename__ = "archery_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Link to spondadmin member (nullable for team records or unmatched)
    spond_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("members.spond_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    archer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Record classification
    division: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    distance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    round_type: Mapped[str] = mapped_column(String(200), nullable=False)

    # Score and date
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    record_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Record type
    record_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="individual"
    )  # 'individual' or 'team'
    team_members: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Source
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<ArcheryRecord id={self.id} division={self.division} score={self.score}>"
