"""
Feedback / questionnaire forms (Spørreskjema).

A Tally-inspired form builder. A ``Form`` owns an ordered list of ``FormField``
blocks. Respondents submit a ``FormResponse`` holding one ``FormAnswer`` per
answered field. Forms can be filled by registered (logged-in) users — whose
identity is captured — or anonymously via a public share link, depending on
``access_mode``.

Lifecycle (status): utkast → publisert → lukket.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer, ForeignKey, CheckConstraint, Index, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.form_field import FormField
    from app.models.form_response import FormResponse

# Status + access vocabularies (kept in sync with the frontend labels).
FORM_STATUSES = ("utkast", "publisert", "lukket")
# offentlig = public anonymous link; innlogget = registered users only (identity
# captured); begge = both (public anonymous AND logged-in tracked).
FORM_ACCESS_MODES = ("offentlig", "innlogget", "begge")

# Field block types. ``overskrift`` is a non-input layout/section block.
FORM_FIELD_TYPES = (
    "kort_tekst", "lang_tekst", "enkeltvalg", "flervalg", "nedtrekk",
    "skala", "tall", "dato", "epost", "ja_nei", "overskrift",
)
# Types that don't capture an answer.
FORM_LAYOUT_TYPES = ("overskrift",)
# Types whose ``options`` is a list of choices.
FORM_CHOICE_TYPES = ("enkeltvalg", "flervalg", "nedtrekk")


class Form(Base, TimestampMixin):
    __tablename__ = "forms"
    __table_args__ = (
        CheckConstraint(
            "status IN ('utkast','publisert','lukket')", name="ck_forms_status",
        ),
        CheckConstraint(
            "access_mode IN ('offentlig','innlogget','begge')", name="ck_forms_access_mode",
        ),
        Index("ix_forms_status", "status"),
        Index("ix_forms_slug", "slug", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Public link key, e.g. /f/{slug}. Unique.
    slug: Mapped[str] = mapped_column(String(80), nullable=False)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="utkast", server_default="utkast"
    )
    access_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="begge", server_default="begge"
    )

    # Only one submission per registered user (anonymous submissions are never
    # de-duplicated since they have no identity).
    one_response_per_user: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Free-form settings: confirmation message, theme accent, etc.
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_by_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )

    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    fields: Mapped[list["FormField"]] = relationship(
        back_populates="form",
        cascade="all, delete-orphan",
        order_by="FormField.position",
    )
    responses: Mapped[list["FormResponse"]] = relationship(
        back_populates="form",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Form id={self.id} title={self.title!r} status={self.status}>"
