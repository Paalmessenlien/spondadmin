"""
A single block/question within a Form.
"""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.form import Form


class FormField(Base):
    __tablename__ = "form_fields"
    __table_args__ = (
        Index("ix_form_fields_form_id", "form_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(
        ForeignKey("forms.id", ondelete="CASCADE"), nullable=False
    )

    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)

    label: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Choice options ([{value,label}, ...]) for enkeltvalg/flervalg/nedtrekk;
    # scale config ({min,max,min_label,max_label}) for skala.
    options: Mapped[Optional[list | dict]] = mapped_column(JSON, nullable=True)
    # Misc per-field settings (placeholder, min/max length, etc.).
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    form: Mapped["Form"] = relationship(back_populates="fields")

    def __repr__(self) -> str:
        return f"<FormField id={self.id} form_id={self.form_id} type={self.field_type}>"
