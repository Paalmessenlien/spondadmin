"""
Pydantic schemas for expense reimbursements (utlegg).
"""
from datetime import date as DateType, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.expense import EXPENSE_CATEGORIES, EXPENSE_STATUSES

_CATEGORY_PATTERN = r"^(" + "|".join(EXPENSE_CATEGORIES) + r")$"


class ExpenseAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    cdn_url: str
    uploaded_at: datetime
    ai_suggestions: Optional[dict] = None


class ExpenseCreate(BaseModel):
    """Create a draft. Everything is optional except a title."""
    title: str = Field(default="Nytt utlegg", min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, pattern=_CATEGORY_PATTERN)
    amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: str = Field(default="NOK", max_length=3)
    expense_date: Optional[DateType] = None
    payee_name: Optional[str] = Field(default=None, max_length=255)
    bank_account: Optional[str] = Field(default=None, max_length=40)
    description: Optional[str] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, pattern=_CATEGORY_PATTERN)
    amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=3)
    expense_date: Optional[DateType] = None
    payee_name: Optional[str] = Field(default=None, max_length=255)
    bank_account: Optional[str] = Field(default=None, max_length=40)
    description: Optional[str] = None


class ExpenseReviewRequest(BaseModel):
    """Kasserer decision. action: godkjenn | avvis | utbetalt."""
    action: str = Field(pattern=r"^(godkjenn|avvis|utbetalt)$")
    note: Optional[str] = None


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submitter_admin_id: Optional[int] = None
    submitter_name: Optional[str] = None
    title: str
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: str
    expense_date: Optional[DateType] = None
    payee_name: Optional[str] = None
    bank_account: Optional[str] = None
    description: Optional[str] = None
    status: str
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    reviewed_by_admin_id: Optional[int] = None
    reviewed_by_name: Optional[str] = None
    kasserer_note: Optional[str] = None
    attachments: List[ExpenseAttachmentResponse] = []
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    expenses: List[ExpenseResponse]
    total: int
    skip: int
    limit: int


class ExpenseFilters(BaseModel):
    status: Optional[str] = Field(default=None, pattern=r"^(" + "|".join(EXPENSE_STATUSES) + r")$")
    category: Optional[str] = Field(default=None, pattern=_CATEGORY_PATTERN)
    date_from: Optional[DateType] = None
    date_to: Optional[DateType] = None
    mine_only: bool = False
    skip: int = 0
    limit: int = 50
