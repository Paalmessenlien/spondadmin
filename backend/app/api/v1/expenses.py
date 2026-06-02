"""
Expense reimbursement (utlegg) API.

Anyone authenticated can create/edit/submit their own expenses. Kasserer + admin
review (approve/reject/mark paid) and can see all expenses.
"""
import csv
import io
import logging
import re
from datetime import date as DateType
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_kasserer_or_admin
from app.db.session import get_db
from app.models.admin import Admin
from app.models.expense import Expense
from app.schemas.expense import (
    ExpenseAttachmentResponse,
    ExpenseCreate,
    ExpenseFilters,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseReviewRequest,
    ExpenseUpdate,
)
from app.services.ai_service import AIService
from app.services.cdn_storage_service import CDNStorageService, CDNNotConfigured
from app.services.expense_service import ExpenseService, is_reviewer

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MB

# Receipt MIME handling. Accept only inert raster images + PDF on upload.
# SVG and HTML are deliberately excluded: they can carry active content and
# would be a stored-XSS vector when a kasserer/admin views the receipt.
# HEIC/HEIF are allowed for iPhone photos (OCR converts them; preview may not
# render inline, but they're served as a download, never executed).
UPLOAD_ALLOWED_TYPES = {
    "image/png", "image/jpeg", "image/gif", "image/webp",
    "image/heic", "image/heif", "application/pdf",
}
# Types we're willing to serve inline (browser-renderable AND inert). Anything
# else is served as an attachment with application/octet-stream.
INLINE_SAFE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf"}


# ---- helpers ---------------------------------------------------------------

async def _names_map(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    rows = (await db.execute(select(Admin.id, Admin.full_name, Admin.email).where(Admin.id.in_(ids)))).all()
    return {r.id: (r.full_name or r.email) for r in rows}


async def _serialize(db: AsyncSession, expense: Expense) -> ExpenseResponse:
    names = await _names_map(db, {expense.submitter_admin_id, expense.reviewed_by_admin_id})
    resp = ExpenseResponse.model_validate(expense)
    resp.submitter_name = names.get(expense.submitter_admin_id)
    resp.reviewed_by_name = names.get(expense.reviewed_by_admin_id)
    return resp


async def _serialize_many(db: AsyncSession, expenses: list[Expense]) -> list[ExpenseResponse]:
    ids: set[int] = set()
    for e in expenses:
        ids.add(e.submitter_admin_id)
        ids.add(e.reviewed_by_admin_id)
    names = await _names_map(db, ids)
    out = []
    for e in expenses:
        resp = ExpenseResponse.model_validate(e)
        resp.submitter_name = names.get(e.submitter_admin_id)
        resp.reviewed_by_name = names.get(e.reviewed_by_admin_id)
        out.append(resp)
    return out


async def _get_viewable(db: AsyncSession, expense_id: int, user: Admin) -> Expense:
    expense = await ExpenseService.get_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Utlegg ikke funnet")
    if expense.submitter_admin_id != user.id and not is_reviewer(user):
        raise HTTPException(status_code=403, detail="Ingen tilgang til dette utlegget")
    return expense


async def _get_owned(db: AsyncSession, expense_id: int, user: Admin) -> Expense:
    expense = await ExpenseService.get_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Utlegg ikke funnet")
    if expense.submitter_admin_id != user.id:
        raise HTTPException(status_code=403, detail="Du kan bare endre dine egne utlegg")
    return expense


# ---- routes ----------------------------------------------------------------

@router.post("/", response_model=ExpenseResponse)
async def create_expense(
    payload: ExpenseCreate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a draft expense (status utkast)."""
    expense = await ExpenseService.create_draft(db, current_user, payload)
    return await _serialize(db, expense)


@router.get("/", response_model=ExpenseListResponse)
async def list_expenses(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    date_from: Optional[DateType] = Query(None),
    date_to: Optional[DateType] = Query(None),
    mine_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = ExpenseFilters(
        status=status, category=category, date_from=date_from, date_to=date_to,
        mine_only=mine_only, skip=skip, limit=limit,
    )
    expenses, total = await ExpenseService.get_for_user(db, current_user, filters)
    return ExpenseListResponse(
        expenses=await _serialize_many(db, expenses), total=total, skip=skip, limit=limit,
    )


@router.get("/export.csv")
async def export_expenses_csv(
    status: Optional[str] = Query(None),
    date_from: Optional[DateType] = Query(None),
    date_to: Optional[DateType] = Query(None),
    current_user: Admin = Depends(get_current_kasserer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """CSV export of expenses for the kasserer's bookkeeping (reviewer only)."""
    filters = ExpenseFilters(status=status, date_from=date_from, date_to=date_to, skip=0, limit=10000)
    expenses, _ = await ExpenseService.get_for_user(db, current_user, filters)
    serialized = await _serialize_many(db, expenses)

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow([
        "ID", "Tittel", "Kategori", "Beløp", "Valuta", "Dato", "Mottaker",
        "Kontonummer", "Status", "Innsendt", "Behandlet av", "Utbetalt",
    ])
    for e in serialized:
        writer.writerow([
            e.id, e.title, e.category or "", e.amount if e.amount is not None else "",
            e.currency, e.expense_date or "", e.payee_name or "", e.bank_account or "",
            e.status, e.submitted_at or "", e.reviewed_by_name or "", e.paid_at or "",
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="utlegg.csv"'},
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = await _get_viewable(db, expense_id, current_user)
    return await _serialize(db, expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = await _get_owned(db, expense_id, current_user)
    if expense.status not in ("utkast", "avvist"):
        raise HTTPException(status_code=400, detail="Utlegget kan ikke endres i denne statusen")
    expense = await ExpenseService.update(db, expense, payload)
    return await _serialize(db, expense)


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = await _get_owned(db, expense_id, current_user)
    if expense.status not in ("utkast", "avvist"):
        raise HTTPException(status_code=400, detail="Bare utkast/avviste utlegg kan slettes")
    await ExpenseService.delete(db, expense)
    return {"status": "deleted", "id": expense_id}


@router.post("/{expense_id}/attachments", response_model=ExpenseAttachmentResponse)
async def upload_attachment(
    expense_id: int,
    file: UploadFile = File(...),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a receipt (image/PDF) to the CDN; OCR images to pre-fill the form."""
    expense = await _get_owned(db, expense_id, current_user)
    if expense.status not in ("utkast", "avvist"):
        raise HTTPException(status_code=400, detail="Kan ikke legge til kvittering nå")

    content_type = (file.content_type or "application/octet-stream").lower()
    if content_type not in UPLOAD_ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Kun bilder (PNG, JPG, GIF, WEBP, HEIC) og PDF er tillatt",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Tom fil")
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise HTTPException(status_code=400, detail="Filen er for stor (maks 10 MB)")

    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "kvittering")
    cdn_path = f"spondadmin/receipts/{expense.id}/{uuid4().hex}_{safe_name}"
    try:
        cdn_url = await CDNStorageService.upload_bytes(cdn_path, data, content_type)
    except CDNNotConfigured:
        raise HTTPException(status_code=503, detail="Fillagring (CDN) er ikke konfigurert")

    # OCR images only; PDFs are stored but not auto-read.
    ai_suggestions = None
    if content_type.startswith("image/"):
        try:
            ai_suggestions = await AIService.extract_receipt(db, data, content_type)
            if ai_suggestions:
                expense.ai_extracted = ai_suggestions
                await db.commit()
        except Exception as e:  # noqa: BLE001 - OCR is best-effort
            logger.warning(f"Receipt OCR failed for expense {expense.id}: {e}")

    att = await ExpenseService.add_attachment(
        db, expense, safe_name, content_type, len(data), cdn_path, cdn_url, ai_suggestions,
    )
    return ExpenseAttachmentResponse.model_validate(att)


@router.get("/{expense_id}/attachments/{attachment_id}/file")
async def get_attachment_file(
    expense_id: int,
    attachment_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream a receipt to an authorized viewer (owner or kasserer/admin).

    Receipts are sensitive (names/amounts) so they are NOT served via a public
    CDN URL — the backend fetches them from the storage zone with the AccessKey
    and returns the bytes only after the access check.
    """
    await _get_viewable(db, expense_id, current_user)
    att = await ExpenseService.get_attachment(db, attachment_id)
    if not att or att.expense_id != expense_id:
        raise HTTPException(status_code=404, detail="Vedlegg ikke funnet")
    try:
        data = await CDNStorageService.download_bytes(att.cdn_path)
    except CDNNotConfigured:
        raise HTTPException(status_code=503, detail="Fillagring (CDN) er ikke konfigurert")
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to fetch receipt {attachment_id} from storage: {e}")
        raise HTTPException(status_code=502, detail="Kunne ikke hente kvittering fra lager")

    # Serve defensively: only inline-render an allowlist of inert types; force
    # everything else to download as octet-stream. nosniff stops MIME-sniffing
    # and the CSP sandbox neutralises any active content even if a bad type
    # slipped through. filename is re-sanitised before going into the header.
    ct = (att.content_type or "").lower()
    if ct in INLINE_SAFE_TYPES:
        media_type, disposition = ct, "inline"
    else:
        media_type, disposition = "application/octet-stream", "attachment"
    safe_filename = re.sub(r"[^A-Za-z0-9._-]", "_", att.filename or "kvittering")
    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Content-Disposition": f'{disposition}; filename="{safe_filename}"',
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
        },
    )


@router.delete("/{expense_id}/attachments/{attachment_id}")
async def delete_attachment(
    expense_id: int,
    attachment_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = await _get_owned(db, expense_id, current_user)
    if expense.status not in ("utkast", "avvist"):
        raise HTTPException(status_code=400, detail="Kan ikke fjerne kvittering nå")
    att = await ExpenseService.get_attachment(db, attachment_id)
    if not att or att.expense_id != expense.id:
        raise HTTPException(status_code=404, detail="Vedlegg ikke funnet")
    await ExpenseService.delete_attachment(db, att)
    return {"status": "deleted", "id": attachment_id}


@router.post("/{expense_id}/submit", response_model=ExpenseResponse)
async def submit_expense(
    expense_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    expense = await _get_owned(db, expense_id, current_user)
    try:
        expense = await ExpenseService.submit(db, expense)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize(db, expense)


@router.post("/{expense_id}/review", response_model=ExpenseResponse)
async def review_expense(
    expense_id: int,
    payload: ExpenseReviewRequest,
    current_user: Admin = Depends(get_current_kasserer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    expense = await ExpenseService.get_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Utlegg ikke funnet")
    try:
        expense = await ExpenseService.review(db, expense, current_user, payload.action, payload.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize(db, expense)
