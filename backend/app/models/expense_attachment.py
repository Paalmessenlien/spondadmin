"""
Expense attachment — a receipt image/PDF stored on Bunny CDN for an Expense.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.expense import Expense


class ExpenseAttachment(Base):
    __tablename__ = "expense_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Bunny CDN object key + public URL.
    cdn_path: Mapped[str] = mapped_column(String(500), nullable=False)
    cdn_url: Mapped[str] = mapped_column(String(700), nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Per-receipt OCR suggestions returned to the frontend at upload time.
    ai_suggestions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    expense: Mapped["Expense"] = relationship(back_populates="attachments")

    def __repr__(self) -> str:
        return f"<ExpenseAttachment id={self.id} expense_id={self.expense_id} {self.filename!r}>"
