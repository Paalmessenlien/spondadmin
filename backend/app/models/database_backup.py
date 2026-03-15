"""
Database backup model
"""
from sqlalchemy import String, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DatabaseBackup(Base, TimestampMixin):
    """
    Tracks database backups and their CDN upload status
    """
    __tablename__ = "database_backups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    cdn_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    backup_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    backup_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("admins.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<DatabaseBackup {self.filename} ({self.status})>"
