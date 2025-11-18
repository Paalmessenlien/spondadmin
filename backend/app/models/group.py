"""
Group model for caching Spond groups
"""
from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Group(Base, TimestampMixin):
    """
    Cached group data from Spond API
    """
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Spond group ID
    spond_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Group details
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Roles and subgroups (stored as JSON arrays)
    roles: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    subgroups: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    field_defs: Mapped[list] = mapped_column(JSON, default=list, nullable=True)

    # Raw data from Spond API
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Sync metadata
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Group {self.spond_id}: {self.name}>"
