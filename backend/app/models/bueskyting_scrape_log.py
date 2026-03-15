"""
Bueskyting Scrape Log model - tracks scraping operations
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BueskytingScrapeLog(Base):
    """Log entry for a bueskyting.no scraping operation"""
    __tablename__ = "bueskyting_scrape_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scrape_type: Mapped[str] = mapped_column(String(50), nullable=False)  # club, archer, records, full, event_dates
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # running, completed, failed
    items_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<BueskytingScrapeLog id={self.id} type={self.scrape_type} status={self.status}>"
