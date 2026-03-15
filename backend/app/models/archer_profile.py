"""
Archer Profile model - archery-specific data for members
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ArcherProfile(Base, TimestampMixin):
    """
    Archery-specific profile data, linked 1:1 to a Member via spond_id.
    Uses spond_id as the FK so the link survives member re-syncs.
    """
    __tablename__ = "archer_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Link to member via spond_id
    spond_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("members.spond_id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
    )

    # Archery details
    bow_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # recurve, compound, barebow, longbow, etc.

    division: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g. senior, junior, under-18, etc.

    skill_level: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # beginner, intermediate, advanced, elite

    club_join_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    archery_gb_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    current_classification: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g. Archer 3rd Class, Bowman, Master Bowman

    current_handicap: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Link to bueskyting.no archer ID for competition data matching
    bueskyting_id: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<ArcherProfile spond_id={self.spond_id} bow={self.bow_type}>"
