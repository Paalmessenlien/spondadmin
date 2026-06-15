"""
Feedback form (skjema) service — CRUD, publish/close state machine, response
submission with server-side validation, and report aggregation.

Access policy is enforced at the router layer (which endpoint + role); this
service validates field-level rules and builds the stored answers.
"""
import logging
import re
import secrets
import unicodedata
from datetime import datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Admin
from app.models.form import (
    Form, FORM_CHOICE_TYPES, FORM_LAYOUT_TYPES,
)
from app.models.form_field import FormField
from app.models.form_response import FormAnswer, FormResponse
from app.schemas.form import FormCreate, FormFieldIn, FormSubmission, FormUpdate

logger = logging.getLogger(__name__)

EDITABLE_STATUS = "utkast"


class FormValidationError(ValueError):
    """Raised when a submission fails field validation (maps to HTTP 400)."""


# ---- slug -------------------------------------------------------------------

def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:48] or "skjema"


# ---- option helpers ---------------------------------------------------------

def _option_pairs(options: Any) -> List[Tuple[str, str]]:
    """Normalize a field's options into (value, label) pairs.

    Accepts ``["a", "b"]`` or ``[{"value": "a", "label": "A"}, ...]``.
    """
    pairs: List[Tuple[str, str]] = []
    if not isinstance(options, list):
        return pairs
    for opt in options:
        if isinstance(opt, dict):
            val = str(opt.get("value", opt.get("label", "")))
            label = str(opt.get("label", opt.get("value", "")))
        else:
            val = label = str(opt)
        if val != "":
            pairs.append((val, label))
    return pairs


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, dict)):
        return len(value) == 0
    return False


class FormService:
    # ---- CRUD ---------------------------------------------------------------

    @staticmethod
    async def _unique_slug(db: AsyncSession, title: str) -> str:
        base = _slugify(title)
        # Always append a short random suffix to avoid collisions and guessing.
        for _ in range(5):
            candidate = f"{base}-{secrets.token_hex(3)}"
            exists = (
                await db.execute(select(Form.id).where(Form.slug == candidate))
            ).scalar_one_or_none()
            if not exists:
                return candidate
        return f"{base}-{secrets.token_hex(6)}"

    @staticmethod
    async def create(db: AsyncSession, creator: Admin, data: FormCreate) -> Form:
        slug = await FormService._unique_slug(db, data.title)
        form = Form(
            title=data.title,
            description=data.description,
            slug=slug,
            access_mode=data.access_mode or "begge",
            one_response_per_user=data.one_response_per_user,
            settings=data.settings,
            created_by_admin_id=creator.id,
            status="utkast",
        )
        db.add(form)
        await db.commit()
        return await FormService.get_by_id(db, form.id)

    @staticmethod
    async def get_by_id(db: AsyncSession, form_id: int) -> Optional[Form]:
        # populate_existing: if the form is already in the session identity map
        # (e.g. loaded earlier in the same request before a mutation), force its
        # attributes — including the eager-loaded ``fields`` collection — to be
        # overwritten from the DB so callers never see a stale field set.
        result = await db.execute(
            select(Form).where(Form.id == form_id)
            .options(selectinload(Form.fields))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Optional[Form]:
        result = await db.execute(
            select(Form).where(Form.slug == slug)
            .options(selectinload(Form.fields))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def response_count(db: AsyncSession, form_id: int) -> int:
        return (await db.execute(
            select(func.count(FormResponse.id)).where(FormResponse.form_id == form_id)
        )).scalar() or 0

    @staticmethod
    async def list_forms(db: AsyncSession, status: Optional[str] = None) -> List[dict]:
        q = select(Form)
        if status:
            q = q.where(Form.status == status)
        q = q.order_by(Form.updated_at.desc())
        forms = (await db.execute(q)).scalars().all()

        # Field + response counts in two grouped queries (avoid N+1).
        field_counts = dict((await db.execute(
            select(FormField.form_id, func.count(FormField.id)).group_by(FormField.form_id)
        )).all())
        resp_counts = dict((await db.execute(
            select(FormResponse.form_id, func.count(FormResponse.id)).group_by(FormResponse.form_id)
        )).all())

        out = []
        for f in forms:
            out.append({
                "id": f.id, "title": f.title, "slug": f.slug, "status": f.status,
                "access_mode": f.access_mode,
                "field_count": field_counts.get(f.id, 0),
                "response_count": resp_counts.get(f.id, 0),
                "created_at": f.created_at, "updated_at": f.updated_at,
                "published_at": f.published_at,
            })
        return out

    @staticmethod
    async def update(db: AsyncSession, form: Form, data: FormUpdate) -> Form:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(form, field, value)
        form.updated_at = datetime.utcnow()
        await db.commit()
        return await FormService.get_by_id(db, form.id)

    @staticmethod
    async def replace_fields(db: AsyncSession, form: Form, fields: List[FormFieldIn]) -> Form:
        """Replace the whole field set. Only allowed while the form is a draft."""
        if form.status != EDITABLE_STATUS:
            raise FormValidationError("Spørsmål kan bare endres mens skjemaet er et utkast")
        await db.execute(delete(FormField).where(FormField.form_id == form.id))
        for idx, fin in enumerate(fields):
            db.add(FormField(
                form_id=form.id,
                position=idx,
                field_type=fin.field_type,
                label=fin.label,
                help_text=fin.help_text,
                required=fin.required,
                options=fin.options,
                settings=fin.settings,
            ))
        form.updated_at = datetime.utcnow()
        await db.commit()
        return await FormService.get_by_id(db, form.id)

    @staticmethod
    async def publish(db: AsyncSession, form: Form) -> Form:
        if form.status == "publisert":
            return form
        # Need at least one answerable field.
        answerable = [f for f in form.fields if f.field_type not in FORM_LAYOUT_TYPES]
        if not answerable:
            raise FormValidationError("Legg til minst ett spørsmål før du publiserer")
        form.status = "publisert"
        if form.published_at is None:
            form.published_at = datetime.utcnow()
        form.closed_at = None
        await db.commit()
        return await FormService.get_by_id(db, form.id)

    @staticmethod
    async def close(db: AsyncSession, form: Form) -> Form:
        form.status = "lukket"
        form.closed_at = datetime.utcnow()
        await db.commit()
        return await FormService.get_by_id(db, form.id)

    @staticmethod
    async def reopen_as_draft(db: AsyncSession, form: Form) -> Form:
        """Return a form to draft so its fields can be edited again.

        Refused if responses already exist (would corrupt the report)."""
        count = await FormService.response_count(db, form.id)
        if count > 0:
            raise FormValidationError(
                "Skjemaet har allerede svar og kan ikke settes tilbake til utkast"
            )
        form.status = "utkast"
        form.published_at = None
        form.closed_at = None
        await db.commit()
        return await FormService.get_by_id(db, form.id)

    @staticmethod
    async def duplicate(db: AsyncSession, form: Form, creator: Admin) -> Form:
        slug = await FormService._unique_slug(db, form.title)
        clone = Form(
            title=f"{form.title} (kopi)",
            description=form.description,
            slug=slug,
            status="utkast",
            access_mode=form.access_mode,
            one_response_per_user=form.one_response_per_user,
            settings=form.settings,
            created_by_admin_id=creator.id,
        )
        db.add(clone)
        await db.flush()
        for f in form.fields:
            db.add(FormField(
                form_id=clone.id, position=f.position, field_type=f.field_type,
                label=f.label, help_text=f.help_text, required=f.required,
                options=f.options, settings=f.settings,
            ))
        await db.commit()
        return await FormService.get_by_id(db, clone.id)

    @staticmethod
    async def delete(db: AsyncSession, form: Form) -> None:
        await db.delete(form)
        await db.commit()

    # ---- submission ---------------------------------------------------------

    @staticmethod
    def _validate_and_textify(field: FormField, value: Any) -> Tuple[Any, str]:
        """Validate a single answer against its field; return (clean_value, text)."""
        ftype = field.field_type

        if ftype in ("kort_tekst", "lang_tekst", "epost"):
            text = str(value).strip()
            if ftype == "epost" and text and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text):
                raise FormValidationError(f"«{field.label}»: ugyldig e-postadresse")
            return text, text

        if ftype == "tall":
            try:
                num = float(value)
            except (TypeError, ValueError):
                raise FormValidationError(f"«{field.label}»: må være et tall")
            num = int(num) if num.is_integer() else num
            return num, str(num)

        if ftype == "dato":
            text = str(value).strip()
            try:
                datetime.strptime(text, "%Y-%m-%d")
            except ValueError:
                raise FormValidationError(f"«{field.label}»: ugyldig dato")
            return text, text

        if ftype == "ja_nei":
            truthy = value in (True, "ja", "Ja", "true", "1", 1)
            return bool(truthy), ("Ja" if truthy else "Nei")

        if ftype == "skala":
            try:
                num = float(value)
            except (TypeError, ValueError):
                raise FormValidationError(f"«{field.label}»: velg en verdi")
            opts = field.options if isinstance(field.options, dict) else {}
            lo = opts.get("min", 1)
            hi = opts.get("max", 5)
            if not (lo <= num <= hi):
                raise FormValidationError(f"«{field.label}»: verdi utenfor skala")
            num = int(num) if float(num).is_integer() else num
            return num, str(num)

        if ftype in ("enkeltvalg", "nedtrekk"):
            pairs = _option_pairs(field.options)
            valid = {v: l for v, l in pairs}
            val = str(value)
            if val not in valid:
                raise FormValidationError(f"«{field.label}»: ugyldig valg")
            return val, valid[val]

        if ftype == "flervalg":
            pairs = _option_pairs(field.options)
            valid = {v: l for v, l in pairs}
            vals = value if isinstance(value, list) else [value]
            clean = [str(v) for v in vals]
            for v in clean:
                if v not in valid:
                    raise FormValidationError(f"«{field.label}»: ugyldig valg")
            return clean, ", ".join(valid[v] for v in clean)

        # Fallback: store as text.
        text = str(value)
        return value, text

    @staticmethod
    async def submit(
        db: AsyncSession,
        form: Form,
        submission: FormSubmission,
        respondent_admin: Optional[Admin],
        is_anonymous: bool,
        respondent_label: Optional[str] = None,
    ) -> FormResponse:
        if form.status != "publisert":
            raise FormValidationError("Skjemaet tar ikke imot svar akkurat nå")

        # One-response-per-user guard (only meaningful for identified users).
        if form.one_response_per_user and respondent_admin is not None:
            existing = (await db.execute(
                select(FormResponse.id).where(
                    FormResponse.form_id == form.id,
                    FormResponse.respondent_admin_id == respondent_admin.id,
                )
            )).scalar_one_or_none()
            if existing:
                raise FormValidationError("Du har allerede svart på dette skjemaet")

        answers_by_field = {a.field_id: a.value for a in submission.answers}

        # Validate every answerable field, build FormAnswer rows.
        answer_rows: List[FormAnswer] = []
        for field in sorted(form.fields, key=lambda f: f.position):
            if field.field_type in FORM_LAYOUT_TYPES:
                continue
            raw = answers_by_field.get(field.id)
            if _is_empty(raw):
                if field.required:
                    raise FormValidationError(f"«{field.label}» er påkrevd")
                continue
            clean, text = FormService._validate_and_textify(field, raw)
            answer_rows.append(FormAnswer(field_id=field.id, value=clean, value_text=text))

        label = (respondent_label or "").strip() or None
        if respondent_admin is not None and not is_anonymous and not label:
            label = respondent_admin.full_name or respondent_admin.email

        response = FormResponse(
            form_id=form.id,
            respondent_admin_id=(None if is_anonymous else (respondent_admin.id if respondent_admin else None)),
            is_anonymous=is_anonymous,
            respondent_label=label,
            answers=answer_rows,
        )
        db.add(response)
        await db.commit()
        await db.refresh(response)
        return response

    # ---- responses + report -------------------------------------------------

    @staticmethod
    async def list_responses(
        db: AsyncSession, form: Form, skip: int = 0, limit: int = 100
    ) -> Tuple[List[FormResponse], int]:
        total = (await db.execute(
            select(func.count(FormResponse.id)).where(FormResponse.form_id == form.id)
        )).scalar() or 0
        rows = (await db.execute(
            select(FormResponse)
            .where(FormResponse.form_id == form.id)
            .options(selectinload(FormResponse.answers))
            .order_by(FormResponse.submitted_at.desc())
            .offset(skip).limit(limit)
        )).scalars().all()
        return list(rows), total

    @staticmethod
    async def build_report(db: AsyncSession, form: Form) -> dict:
        """Aggregate all answers per answerable field."""
        # Pull every answer for this form in one query.
        rows = (await db.execute(
            select(FormAnswer)
            .join(FormResponse, FormAnswer.response_id == FormResponse.id)
            .where(FormResponse.form_id == form.id)
        )).scalars().all()

        by_field: dict[int, list] = {}
        for a in rows:
            if a.field_id is None:
                continue
            by_field.setdefault(a.field_id, []).append(a)

        total_responses = await FormService.response_count(db, form.id)

        questions = []
        for field in sorted(form.fields, key=lambda f: f.position):
            if field.field_type in FORM_LAYOUT_TYPES:
                continue
            answers = by_field.get(field.id, [])
            summary = FormService._aggregate_field(field, answers)
            questions.append({
                "field_id": field.id,
                "label": field.label,
                "field_type": field.field_type,
                "answered_count": len(answers),
                "summary": summary,
            })

        return {
            "form_id": form.id,
            "title": form.title,
            "status": form.status,
            "response_count": total_responses,
            "questions": questions,
        }

    @staticmethod
    def _aggregate_field(field: FormField, answers: list) -> dict:
        ftype = field.field_type
        answered = len(answers)

        if ftype in FORM_CHOICE_TYPES:
            pairs = _option_pairs(field.options)
            counts = {v: 0 for v, _ in pairs}
            labels = {v: l for v, l in pairs}
            for a in answers:
                vals = a.value if isinstance(a.value, list) else [a.value]
                for v in vals:
                    key = str(v)
                    counts[key] = counts.get(key, 0) + 1
            opts = [
                {
                    "value": v, "label": labels.get(v, v), "count": counts.get(v, 0),
                    "pct": round(100 * counts.get(v, 0) / answered, 1) if answered else 0.0,
                }
                for v, _ in pairs
            ]
            return {"options": opts}

        if ftype == "ja_nei":
            ja = sum(1 for a in answers if a.value in (True, "ja", "Ja", 1, "1"))
            return {"ja": ja, "nei": answered - ja}

        if ftype in ("skala", "tall"):
            nums = []
            for a in answers:
                try:
                    nums.append(float(a.value))
                except (TypeError, ValueError):
                    pass
            dist: dict[str, int] = {}
            for n in nums:
                key = str(int(n) if float(n).is_integer() else n)
                dist[key] = dist.get(key, 0) + 1
            return {
                "avg": round(sum(nums) / len(nums), 2) if nums else None,
                "min": min(nums) if nums else None,
                "max": max(nums) if nums else None,
                "distribution": dist,
            }

        # Free-text-ish: kort_tekst, lang_tekst, epost, dato.
        samples = [a.value_text for a in answers if a.value_text][:100]
        return {"samples": samples, "total": answered}
