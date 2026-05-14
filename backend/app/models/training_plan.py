"""
TrainingPlan — a named period (e.g. "Vaktliste JUL–SEP 2026") that owns a
set of TrainingSessionTypes. Multiple plans can coexist so admins can plan
the next quarter without polluting the current one.

Leader groups remain global (see app/models/leader_group.py) and can be
referenced from session types in any plan.
"""
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.training_session_type import TrainingSessionType


class TrainingPlan(Base, TimestampMixin):
    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    session_types: Mapped[list["TrainingSessionType"]] = relationship(
        back_populates="plan",
    )

    def __repr__(self) -> str:
        return (
            f"<TrainingPlan id={self.id} name={self.name!r} "
            f"{self.period_start}…{self.period_end}>"
        )
