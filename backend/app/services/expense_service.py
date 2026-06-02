"""
Expense (utlegg) service — CRUD + submit/review state machine.

Access model:
- Any authenticated user can create/edit/submit their OWN expenses.
- Kasserer + admin can see all expenses and review (approve/reject/mark paid).
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Admin
from app.models.expense import Expense
from app.models.expense_attachment import ExpenseAttachment
from app.schemas.expense import ExpenseCreate, ExpenseFilters, ExpenseUpdate
from app.services.cdn_storage_service import CDNStorageService

logger = logging.getLogger(__name__)

REVIEWER_ROLES = ("admin", "kasserer")
EDITABLE_STATUSES = ("utkast", "avvist")


def is_reviewer(user: Admin) -> bool:
    return user.role in REVIEWER_ROLES


class ExpenseService:
    @staticmethod
    async def create_draft(db: AsyncSession, submitter: Admin, data: ExpenseCreate) -> Expense:
        expense = Expense(
            submitter_admin_id=submitter.id,
            title=data.title,
            category=data.category,
            amount=data.amount,
            currency=data.currency or "NOK",
            expense_date=data.expense_date,
            payee_name=data.payee_name or submitter.full_name,
            bank_account=data.bank_account,
            description=data.description,
            status="utkast",
        )
        db.add(expense)
        await db.commit()
        return await ExpenseService.get_by_id(db, expense.id)

    @staticmethod
    async def get_by_id(db: AsyncSession, expense_id: int) -> Optional[Expense]:
        result = await db.execute(
            select(Expense)
            .where(Expense.id == expense_id)
            .options(selectinload(Expense.attachments))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_for_user(
        db: AsyncSession, user: Admin, filters: ExpenseFilters
    ) -> Tuple[List[Expense], int]:
        conditions = []
        # Submitters only ever see their own. Reviewers see all unless they
        # explicitly ask for "mine_only".
        if not is_reviewer(user) or filters.mine_only:
            conditions.append(Expense.submitter_admin_id == user.id)
        if filters.status:
            conditions.append(Expense.status == filters.status)
        if filters.category:
            conditions.append(Expense.category == filters.category)
        if filters.date_from:
            conditions.append(Expense.expense_date >= filters.date_from)
        if filters.date_to:
            conditions.append(Expense.expense_date <= filters.date_to)

        count_q = select(func.count(Expense.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await db.execute(count_q)).scalar() or 0

        q = select(Expense).options(selectinload(Expense.attachments))
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(Expense.created_at.desc()).offset(filters.skip).limit(filters.limit)
        rows = (await db.execute(q)).scalars().all()
        return list(rows), total

    @staticmethod
    async def update(db: AsyncSession, expense: Expense, data: ExpenseUpdate) -> Expense:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(expense, field, value)
        expense.updated_at = datetime.utcnow()
        await db.commit()
        return await ExpenseService.get_by_id(db, expense.id)

    @staticmethod
    async def submit(db: AsyncSession, expense: Expense) -> Expense:
        if expense.status not in EDITABLE_STATUSES:
            raise ValueError(f"Kan ikke sende inn et utlegg med status '{expense.status}'")
        if not expense.attachments:
            raise ValueError("Legg ved minst én kvittering før innsending")
        if expense.amount is None:
            raise ValueError("Beløp må fylles ut før innsending")
        expense.status = "sendt"
        expense.submitted_at = datetime.utcnow()
        # Clear any previous rejection note on resubmit.
        expense.kasserer_note = None
        expense.reviewed_by_admin_id = None
        expense.reviewed_at = None
        await db.commit()
        return await ExpenseService.get_by_id(db, expense.id)

    @staticmethod
    async def review(
        db: AsyncSession, expense: Expense, reviewer: Admin, action: str, note: Optional[str]
    ) -> Expense:
        now = datetime.utcnow()
        if action == "godkjenn":
            if expense.status != "sendt":
                raise ValueError("Bare innsendte utlegg kan godkjennes")
            expense.status = "godkjent"
        elif action == "avvis":
            if expense.status != "sendt":
                raise ValueError("Bare innsendte utlegg kan avvises")
            expense.status = "avvist"
        elif action == "utbetalt":
            if expense.status != "godkjent":
                raise ValueError("Bare godkjente utlegg kan markeres som utbetalt")
            expense.status = "utbetalt"
            expense.paid_at = now
        else:
            raise ValueError(f"Ukjent handling: {action}")

        expense.reviewed_by_admin_id = reviewer.id
        expense.reviewed_at = now
        if note is not None:
            expense.kasserer_note = note
        await db.commit()
        return await ExpenseService.get_by_id(db, expense.id)

    @staticmethod
    async def delete(db: AsyncSession, expense: Expense) -> None:
        # Best-effort CDN cleanup before the cascade removes attachment rows.
        for att in expense.attachments:
            await CDNStorageService.delete(att.cdn_path)
        await db.delete(expense)
        await db.commit()

    @staticmethod
    async def add_attachment(
        db: AsyncSession,
        expense: Expense,
        filename: str,
        content_type: Optional[str],
        size_bytes: int,
        cdn_path: str,
        cdn_url: str,
        ai_suggestions: Optional[dict] = None,
    ) -> ExpenseAttachment:
        att = ExpenseAttachment(
            expense_id=expense.id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            cdn_path=cdn_path,
            cdn_url=cdn_url,
            ai_suggestions=ai_suggestions,
        )
        db.add(att)
        await db.commit()
        await db.refresh(att)
        return att

    @staticmethod
    async def get_attachment(db: AsyncSession, attachment_id: int) -> Optional[ExpenseAttachment]:
        return await db.get(ExpenseAttachment, attachment_id)

    @staticmethod
    async def delete_attachment(db: AsyncSession, att: ExpenseAttachment) -> None:
        await CDNStorageService.delete(att.cdn_path)
        await db.delete(att)
        await db.commit()
