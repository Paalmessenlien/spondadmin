"""
Scraping Config model - singleton configuration for bueskyting.no scraping
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ScrapingConfig(Base, TimestampMixin):
    """Singleton configuration for the bueskyting.no scraper"""
    __tablename__ = "scraping_config"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    base_url: Mapped[str] = mapped_column(
        String(500), default="https://resultat.bueskyting.no", nullable=False
    )
    records_url: Mapped[str] = mapped_column(
        String(500), default="https://rekord.bueskyting.no", nullable=False
    )
    club_id: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    last_results_scrape: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_records_scrape: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    auto_scrape_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scrape_interval_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    def __repr__(self) -> str:
        return f"<ScrapingConfig id={self.id} club_id={self.club_id}>"
