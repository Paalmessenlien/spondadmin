"""
Competition Result model - individual archer results from competitions
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CompetitionResult(Base, TimestampMixin):
    """An individual result from a competition, scraped from bueskyting.no"""
    __tablename__ = "competition_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Link to spondadmin member (nullable - may not be matched yet)
    spond_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("members.spond_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Archer identity from bueskyting.no
    archer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    bueskyting_archer_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )

    # Competition link
    competition_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("competitions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Result details
    event_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    distance: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    equipment_class: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    round_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ranking: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    event_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CompetitionResult id={self.id} archer={self.archer_name} score={self.score}>"
