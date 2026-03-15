"""
Competition model - archery competition events
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Competition(Base, TimestampMixin):
    """A competition/event from bueskyting.no"""
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    event_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Competition id={self.id} name={self.name}>"
