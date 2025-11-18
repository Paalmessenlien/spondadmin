"""
Sync history model for tracking API synchronization
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SyncHistory(Base):
    """
    Track synchronization history with Spond API
    """
    __tablename__ = "sync_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Sync type (events, groups, members)
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Sync timing
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Sync status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running"
    )  # running, completed, failed
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Sync statistics
    items_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_deleted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error information
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncHistory {self.sync_type} at {self.started_at}>"
