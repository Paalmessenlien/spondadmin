"""
Member model for caching Spond members
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.group_member import GroupMember


class Member(Base, TimestampMixin):
    """
    Cached member data from Spond API.

    Group membership lives in the `group_members` association table — a member
    can belong to multiple Spond groups, with per-group `role_uids` and
    `subgroup_uids` stored on each association row.
    """
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Spond member ID
    spond_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Member details
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(50), nullable=True)

    # Profile information
    profile: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Member created time
    member_created_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Extensible custom fields from Spond
    fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=True)

    # Raw data from Spond API
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    # Sync metadata
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # Per-group membership rows (with role_uids, subgroup_uids).
    group_associations: Mapped[list["GroupMember"]] = relationship(
        back_populates="member",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    # Read-only secondary for direct group access.
    groups: Mapped[list["Group"]] = relationship(
        secondary="group_members",
        viewonly=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Member {self.spond_id}: {self.first_name} {self.last_name}>"

    @property
    def full_name(self) -> str:
        """Get member's full name"""
        return f"{self.first_name} {self.last_name}"
