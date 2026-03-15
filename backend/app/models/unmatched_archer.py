"""
Unmatched Archer model - archers from bueskyting.no not yet linked to a Spond member
"""
from typing import Optional
from sqlalchemy import String, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class UnmatchedArcher(Base, TimestampMixin):
    """An archer from bueskyting.no that hasn't been matched to a Spond member"""
    __tablename__ = "unmatched_archers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bueskyting_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Auto-match suggestion
    suggested_spond_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("members.spond_id", ondelete="SET NULL"),
        nullable=True,
    )
    match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<UnmatchedArcher id={self.id} name={self.name}>"
