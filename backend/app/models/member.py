"""
Member model for caching Spond members
"""
from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Member(Base, TimestampMixin):
    """
    Cached member data from Spond API
    """
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Spond member ID
    spond_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Group association
    group_id: Mapped[str] = mapped_column(String(255), ForeignKey("groups.spond_id"), nullable=True)

    # Member details
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=True)

    # Profile information
    profile: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Member created time
    member_created_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Roles and subgroups (stored as JSON arrays)
    role_uids: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    subgroup_uids: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)

    # Raw data from Spond API
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Sync metadata
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Member {self.spond_id}: {self.first_name} {self.last_name}>"

    @property
    def full_name(self) -> str:
        """Get member's full name"""
        return f"{self.first_name} {self.last_name}"
