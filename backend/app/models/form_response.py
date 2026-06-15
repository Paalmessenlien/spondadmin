"""
A single submission to a Form, plus its per-field answers.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer, ForeignKey, JSON, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.form import Form


class FormResponse(Base):
    __tablename__ = "form_responses"
    __table_args__ = (
        Index("ix_form_responses_form_id", "form_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(
        ForeignKey("forms.id", ondelete="CASCADE"), nullable=False
    )

    # Null = anonymous. SET NULL so a removed user's responses survive (and
    # become anonymous) rather than disappearing.
    respondent_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Best-effort display label (name/email captured at submit time).
    respondent_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    form: Mapped["Form"] = relationship(back_populates="responses")
    answers: Mapped[list["FormAnswer"]] = relationship(
        back_populates="response",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FormResponse id={self.id} form_id={self.form_id} anon={self.is_anonymous}>"


class FormAnswer(Base):
    __tablename__ = "form_answers"
    __table_args__ = (
        Index("ix_form_answers_response_id", "response_id"),
        Index("ix_form_answers_field_id", "field_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    response_id: Mapped[int] = mapped_column(
        ForeignKey("form_responses.id", ondelete="CASCADE"), nullable=False
    )
    # SET NULL: keep an answer's value for the record even if the field row is
    # later removed (field structure is frozen post-publish, but be defensive).
    field_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("form_fields.id", ondelete="SET NULL"), nullable=True
    )

    # Flexible typed value: str | number | bool | list[str].
    value: Mapped[Optional[object]] = mapped_column(JSON, nullable=True)
    # Denormalized human-readable form for CSV/report/search.
    value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    response: Mapped["FormResponse"] = relationship(back_populates="answers")

    def __repr__(self) -> str:
        return f"<FormAnswer id={self.id} response_id={self.response_id} field_id={self.field_id}>"
