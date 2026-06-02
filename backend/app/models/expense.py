"""
Expense (Utlegg) model — out-of-pocket reimbursements submitted to the kasserer.

A standalone expense: one purpose/amount with one or more receipt attachments.
Lifecycle (status): utkast → sendt → godkjent/avvist → utbetalt.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Date, DateTime, Numeric, ForeignKey, CheckConstraint, Index, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.expense_attachment import ExpenseAttachment

# Status vocabulary + controlled expense categories (kept in sync with the
# frontend labels and the AI OCR validation).
EXPENSE_STATUSES = ("utkast", "sendt", "godkjent", "avvist", "utbetalt")
EXPENSE_CATEGORIES = (
    "utstyr", "reise", "bevertning", "kontor", "premier", "bane_anlegg", "kurs", "annet",
)


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint(
            "status IN ('utkast','sendt','godkjent','avvist','utbetalt')",
            name="ck_expenses_status",
        ),
        Index("ix_expenses_status", "status"),
        Index("ix_expenses_submitter_admin_id", "submitter_admin_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Who submitted it (Clerk-backed Admin). SET NULL so the expense survives
    # a user being removed.
    submitter_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NOK", server_default="NOK")
    expense_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Payout target — who gets reimbursed and to which account.
    payee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="utkast", server_default="utkast"
    )

    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Kasserer review.
    reviewed_by_admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    kasserer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Raw OCR result from the AI (audit / debugging).
    ai_extracted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    attachments: Mapped[list["ExpenseAttachment"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
        order_by="ExpenseAttachment.id",
    )

    def __repr__(self) -> str:
        return f"<Expense id={self.id} title={self.title!r} status={self.status}>"
