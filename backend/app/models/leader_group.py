"""
LeaderGroup — a named pool of members who can lead training shifts. A
TrainingSessionType can be bound to a LeaderGroup; when it is, the shift
editor filters the leader picker to that pool. Multiple session types can
share the same leader group.
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.member import Member


class LeaderGroup(Base, TimestampMixin):
    __tablename__ = "leader_groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    members: Mapped[list["Member"]] = relationship(
        secondary="leader_group_members",
        backref="leader_groups",
    )

    def __repr__(self) -> str:
        return f"<LeaderGroup id={self.id} name={self.name!r}>"


class LeaderGroupMember(Base):
    """Plain association row — composite PK, no extra columns yet."""

    __tablename__ = "leader_group_members"

    leader_group_id: Mapped[int] = mapped_column(
        ForeignKey("leader_groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"),
        primary_key=True,
    )
