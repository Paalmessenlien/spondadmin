"""
GroupMember association — multi-group membership for a Spond member.
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.member import Member


class GroupMember(Base, TimestampMixin):
    __tablename__ = "group_members"

    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    role_uids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    subgroup_uids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    member: Mapped["Member"] = relationship(back_populates="group_associations")
    group: Mapped["Group"] = relationship(back_populates="member_associations")

    def __repr__(self) -> str:
        return f"<GroupMember member_id={self.member_id} group_id={self.group_id}>"
