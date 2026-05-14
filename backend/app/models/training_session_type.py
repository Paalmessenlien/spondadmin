"""
TrainingSessionType — a recurring training-session template (e.g. "Barn & Ungdom",
"Søndag Ensby"). Each TrainingShift refers to one of these, inheriting default
start/end times unless the shift overrides them.
"""
from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.leader_group import LeaderGroup
    from app.models.training_plan import TrainingPlan
    from app.models.training_shift import TrainingShift


class TrainingSessionType(Base, TimestampMixin):
    __tablename__ = "training_session_types"
    __table_args__ = (
        # Names are unique *within a plan* — two plans may carry the same
        # session-type name (e.g. each quarter has its own "Barn & Ungdom").
        UniqueConstraint(
            "plan_id", "name", name="uq_training_session_types_plan_id_name"
        ),
        Index("ix_training_session_types_plan_id", "plan_id"),
        Index("ix_training_session_types_group_id", "group_id"),
        Index("ix_training_session_types_leader_group_id", "leader_group_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Which training plan this session type belongs to. RESTRICT keeps the
    # plan around as long as it has session types — admins must reassign or
    # delete the children first.
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("training_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    default_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    default_end_time: Mapped[time] = mapped_column(Time, nullable=False)

    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Free-form description used as the base text for the Spond event
    # description when shifts of this type are published.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # The Spond group this training plan belongs to. Drives the audience when
    # shifts of this type are published. Nullable so publish can still fall back
    # to the largest group for legacy rows; the UI guides admins to set it.
    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # uids of the Spond subgroups that should be invited when shifts of this
    # type are published. NULL or empty list → invite the whole `group_id`.
    # Members are considered if their `group_members.subgroup_uids` intersects
    # with this list.
    spond_subgroup_uids: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )

    # Optional binding to a named pool of leaders. When set, the shift
    # editor narrows the leader picker to members of this group.
    leader_group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("leader_groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Default invitation scheduling. NULL → send immediately on publish.
    # Otherwise: send the Spond invitation `invite_lead_days` days before the
    # shift date, at `invite_send_time` local Oslo time. The shift can
    # override either field; the publish service falls back here when the
    # override is NULL.
    invite_lead_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    invite_send_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    plan: Mapped["TrainingPlan"] = relationship(back_populates="session_types")
    group: Mapped[Optional["Group"]] = relationship(foreign_keys=[group_id])
    leader_group: Mapped[Optional["LeaderGroup"]] = relationship(
        foreign_keys=[leader_group_id]
    )

    shifts: Mapped[list["TrainingShift"]] = relationship(
        back_populates="session_type",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TrainingSessionType id={self.id} name={self.name!r}>"
