"""
Feedback / questionnaire (skjema) API.

- Managing forms (build, edit, publish, responses, reports, export) requires
  editor-or-above.
- Filling a form: authenticated users hit ``POST /{id}/submit`` (identity
  captured unless the form is anonymous-only); anonymous respondents hit the
  public ``/public/{slug}`` endpoints (no auth) when the form's access_mode
  allows it.
"""
import csv
import io
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_current_editor_or_above
from app.db.session import get_db
from app.models.admin import Admin
from app.models.form import Form, FORM_LAYOUT_TYPES
from app.schemas.form import (
    FormCreate, FormDetail, FormFieldResponse, FormFieldsUpdate, FormListResponse,
    FormReport, FormResponsesList, FormSubmission, FormUpdate, PublicForm,
)
from app.services.form_service import FormService, FormValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


# ---- helpers ---------------------------------------------------------------

async def _names_map(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    rows = (await db.execute(
        select(Admin.id, Admin.full_name, Admin.email).where(Admin.id.in_(ids))
    )).all()
    return {r.id: (r.full_name or r.email) for r in rows}


async def _serialize_detail(db: AsyncSession, form: Form) -> FormDetail:
    detail = FormDetail.model_validate(form)
    detail.response_count = await FormService.response_count(db, form.id)
    if form.created_by_admin_id:
        names = await _names_map(db, {form.created_by_admin_id})
        detail.created_by_name = names.get(form.created_by_admin_id)
    return detail


async def _get_form_or_404(db: AsyncSession, form_id: int) -> Form:
    form = await FormService.get_by_id(db, form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Skjema ikke funnet")
    return form


def _public_form(form: Form) -> PublicForm:
    return PublicForm(
        id=form.id, title=form.title, description=form.description, slug=form.slug,
        status=form.status, access_mode=form.access_mode, settings=form.settings,
        fields=[FormFieldResponse.model_validate(f).model_dump() for f in sorted(form.fields, key=lambda x: x.position)],
    )


# ---- management (editor+) --------------------------------------------------

@router.post("/", response_model=FormDetail)
async def create_form(
    payload: FormCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await FormService.create(db, current_user, payload)
    return await _serialize_detail(db, form)


@router.get("/", response_model=FormListResponse)
async def list_forms(
    status: Optional[str] = Query(None),
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    items = await FormService.list_forms(db, status=status)
    return FormListResponse(forms=items, total=len(items))


@router.get("/{form_id}", response_model=FormDetail)
async def get_form(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    return await _serialize_detail(db, form)


@router.patch("/{form_id}", response_model=FormDetail)
async def update_form(
    form_id: int,
    payload: FormUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    form = await FormService.update(db, form, payload)
    return await _serialize_detail(db, form)


@router.put("/{form_id}/fields", response_model=FormDetail)
async def replace_fields(
    form_id: int,
    payload: FormFieldsUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    try:
        form = await FormService.replace_fields(db, form, payload.fields)
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize_detail(db, form)


@router.post("/{form_id}/publish", response_model=FormDetail)
async def publish_form(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    try:
        form = await FormService.publish(db, form)
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize_detail(db, form)


@router.post("/{form_id}/close", response_model=FormDetail)
async def close_form(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    form = await FormService.close(db, form)
    return await _serialize_detail(db, form)


@router.post("/{form_id}/reopen", response_model=FormDetail)
async def reopen_form(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    try:
        form = await FormService.reopen_as_draft(db, form)
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize_detail(db, form)


@router.post("/{form_id}/duplicate", response_model=FormDetail)
async def duplicate_form(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    clone = await FormService.duplicate(db, form, current_user)
    return await _serialize_detail(db, clone)


@router.delete("/{form_id}")
async def delete_form(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    await FormService.delete(db, form)
    return {"status": "deleted", "id": form_id}


# ---- responses + reports (editor+) -----------------------------------------

@router.get("/{form_id}/responses", response_model=FormResponsesList)
async def list_responses(
    form_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    responses, total = await FormService.list_responses(db, form, skip, limit)
    names = await _names_map(db, {r.respondent_admin_id for r in responses})
    rows = []
    for r in responses:
        rows.append({
            "id": r.id,
            "respondent_admin_id": r.respondent_admin_id,
            "respondent_name": names.get(r.respondent_admin_id) or r.respondent_label,
            "is_anonymous": r.is_anonymous,
            "respondent_label": r.respondent_label,
            "submitted_at": r.submitted_at,
            "answers": [
                {"field_id": a.field_id, "value": a.value, "value_text": a.value_text}
                for a in r.answers
            ],
        })
    return FormResponsesList(
        form_id=form.id, title=form.title,
        fields=[FormFieldResponse.model_validate(f) for f in sorted(form.fields, key=lambda x: x.position)],
        responses=rows, total=total, skip=skip, limit=limit,
    )


@router.get("/{form_id}/report", response_model=FormReport)
async def form_report(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    return await FormService.build_report(db, form)


@router.get("/{form_id}/responses.csv")
async def export_responses_csv(
    form_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    responses, _ = await FormService.list_responses(db, form, skip=0, limit=100000)
    names = await _names_map(db, {r.respondent_admin_id for r in responses})

    answerable = [f for f in sorted(form.fields, key=lambda x: x.position)
                  if f.field_type not in FORM_LAYOUT_TYPES]

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Svar-ID", "Innsendt", "Respondent"] + [f.label for f in answerable])
    for r in responses:
        by_field = {a.field_id: (a.value_text or "") for a in r.answers}
        respondent = "Anonym" if r.is_anonymous else (names.get(r.respondent_admin_id) or r.respondent_label or "")
        writer.writerow(
            [r.id, r.submitted_at, respondent] + [by_field.get(f.id, "") for f in answerable]
        )
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="skjema-{form.id}-svar.csv"'},
    )


# ---- in-app fill (any authenticated user) ----------------------------------

@router.post("/{form_id}/submit", response_model=dict)
async def submit_form(
    form_id: int,
    payload: FormSubmission,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    form = await _get_form_or_404(db, form_id)
    if form.access_mode == "offentlig":
        # Anonymous-only form: store without identity even for a logged-in user.
        is_anonymous = True
        admin = None
    else:
        is_anonymous = False
        admin = current_user
    try:
        resp = await FormService.submit(db, form, payload, admin, is_anonymous, payload.respondent_label)
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "response_id": resp.id}


# ---- public (no auth) ------------------------------------------------------

@router.get("/public/{slug}", response_model=PublicForm)
async def get_public_form(slug: str, db: AsyncSession = Depends(get_db)):
    """Fetch a form for anonymous filling. Only published, publicly-accessible forms."""
    form = await FormService.get_by_slug(db, slug)
    if not form:
        raise HTTPException(status_code=404, detail="Skjema ikke funnet")
    if form.status != "publisert":
        raise HTTPException(status_code=404, detail="Skjemaet er ikke tilgjengelig")
    if form.access_mode not in ("offentlig", "begge"):
        raise HTTPException(status_code=403, detail="Dette skjemaet krever innlogging")
    return _public_form(form)


@router.post("/public/{slug}/submit", response_model=dict)
async def submit_public_form(slug: str, payload: FormSubmission, db: AsyncSession = Depends(get_db)):
    """Anonymous submission via the public share link."""
    form = await FormService.get_by_slug(db, slug)
    if not form:
        raise HTTPException(status_code=404, detail="Skjema ikke funnet")
    if form.access_mode not in ("offentlig", "begge"):
        raise HTTPException(status_code=403, detail="Dette skjemaet krever innlogging")
    try:
        resp = await FormService.submit(db, form, payload, None, is_anonymous=True,
                                        respondent_label=payload.respondent_label)
    except FormValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok", "response_id": resp.id}
