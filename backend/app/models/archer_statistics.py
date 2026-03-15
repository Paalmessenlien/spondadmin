"""
Archer Statistics model - yearly competition statistics per archer
"""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ArcherStatistics(Base, TimestampMixin):
    """Yearly competition statistics for an archer from bueskyting.no"""
    __tablename__ = "archer_statistics"
    __table_args__ = (
        UniqueConstraint("bueskyting_archer_id", "year", name="uq_archer_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Link to spondadmin member (nullable - may not be matched yet)
    spond_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("members.spond_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Archer identity from bueskyting.no
    bueskyting_archer_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    archer_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Statistics
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    starts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    top3: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    victories: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<ArcherStatistics archer={self.archer_name} year={self.year}>"
