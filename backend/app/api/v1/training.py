"""
Training-plan API (waves 1 + 2).

Wave 1: reference-data CRUD for training session types and member aliases.
Wave 2: training-shift CRUD, .xlsx importer, and per-shift Spond publish.
"""
import calendar
import logging
from datetime import date as date_type
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import (
    get_current_admin,
    get_current_editor_or_above,
    get_current_user,
)
from app.db.session import get_db
from app.models.admin import Admin
from app.models.leader_group import LeaderGroup, LeaderGroupMember
from app.models.member import Member
from app.models.member_alias import MemberAlias
from app.models.training_plan import TrainingPlan
from app.models.training_session_type import TrainingSessionType
from app.models.training_shift import TrainingShift
from app.schemas.training import (
    ImportReport,
    LeaderGroupCreate,
    LeaderGroupListResponse,
    LeaderGroupMembersUpdate,
    LeaderGroupResponse,
    LeaderGroupUpdate,
    MemberAliasCreate,
    MemberAliasListResponse,
    MemberAliasResponse,
    MemberAliasUpdate,
    TrainingPlanCreate,
    TrainingPlanListResponse,
    TrainingPlanResponse,
    TrainingPlanUpdate,
    TrainingSessionTypeCreate,
    TrainingSessionTypeListResponse,
    TrainingSessionTypeResponse,
    TrainingSessionTypeUpdate,
    TrainingShiftCreate,
    TrainingShiftListResponse,
    TrainingShiftResponse,
    TrainingShiftUpdate,
)
from app.services.spond_event_create_service import (
    SpondCreateError,
    spond_event_create_service,
)
from app.services.spond_service import get_spond_service
from app.services.training_import_service import training_import_service
from app.services.training_pdf_service import render_plan_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Helpers
# ============================================================

async def _get_session_type_or_404(
    db: AsyncSession, session_type_id: int
) -> TrainingSessionType:
    result = await db.execute(
        select(TrainingSessionType)
        .options(
            selectinload(TrainingSessionType.group),
            selectinload(TrainingSessionType.leader_group),
        )
        .where(TrainingSessionType.id == session_type_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Session type not found")
    return obj


async def _get_alias_or_404(db: AsyncSession, alias_id: int) -> MemberAlias:
    result = await db.execute(
        select(MemberAlias)
        .options(selectinload(MemberAlias.member))
        .where(MemberAlias.id == alias_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Alias not found")
    return obj


async def _ensure_member_exists(db: AsyncSession, member_id: int) -> None:
    result = await db.execute(select(Member.id).where(Member.id == member_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=400, detail=f"Member {member_id} not found")


# ============================================================
# Training plans
# ============================================================


async def _get_plan_or_404(db: AsyncSession, plan_id: int) -> TrainingPlan:
    result = await db.execute(
        select(TrainingPlan).where(TrainingPlan.id == plan_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Training plan not found")
    return obj


async def _plan_to_response(
    db: AsyncSession, plan: TrainingPlan
) -> TrainingPlanResponse:
    """Build a TrainingPlanResponse with the two count fields populated."""
    session_type_count = (
        await db.scalar(
            select(func.count(TrainingSessionType.id)).where(
                TrainingSessionType.plan_id == plan.id
            )
        )
    ) or 0
    shift_count = (
        await db.scalar(
            select(func.count(TrainingShift.id))
            .join(TrainingSessionType)
            .where(TrainingSessionType.plan_id == plan.id)
        )
    ) or 0
    payload = TrainingPlanResponse.model_validate(plan).model_dump()
    payload["session_type_count"] = session_type_count
    payload["shift_count"] = shift_count
    return TrainingPlanResponse(**payload)


@router.get("/plans", response_model=TrainingPlanListResponse)
async def list_plans(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List training plans, newest-period first."""
    result = await db.execute(
        select(TrainingPlan).order_by(
            TrainingPlan.period_start.desc(), TrainingPlan.id.desc()
        )
    )
    plans = result.scalars().all()
    items = [await _plan_to_response(db, p) for p in plans]
    return TrainingPlanListResponse(items=items, total=len(items))


@router.post(
    "/plans",
    response_model=TrainingPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    data: TrainingPlanCreate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new training plan (admin only)."""
    obj = TrainingPlan(**data.model_dump())
    db.add(obj)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A training plan named {data.name!r} already exists",
        )
    await db.refresh(obj)
    return await _plan_to_response(db, obj)


@router.patch("/plans/{plan_id}", response_model=TrainingPlanResponse)
async def update_plan(
    plan_id: int,
    data: TrainingPlanUpdate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a training plan (admin only)."""
    obj = await _get_plan_or_404(db, plan_id)
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(obj, key, value)
    if obj.period_end < obj.period_start:
        raise HTTPException(
            status_code=400,
            detail="period_end must not be before period_start",
        )
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Plan name conflicts with another plan",
        )
    await db.refresh(obj)
    return await _plan_to_response(db, obj)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a training plan (admin only). Refuses if any session types
    still reference it — the FK is ON DELETE RESTRICT for safety."""
    obj = await _get_plan_or_404(db, plan_id)
    st_count = await db.scalar(
        select(func.count(TrainingSessionType.id)).where(
            TrainingSessionType.plan_id == plan_id
        )
    )
    if st_count:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete plan — {st_count} session type(s) still "
                "reference it. Remove or reassign those first."
            ),
        )
    await db.delete(obj)
    await db.commit()
    return None


@router.get("/plans/{plan_id}/export.pdf")
async def export_plan_pdf(
    plan_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Render a chronological-shift-list PDF for one plan.

    Available to any authenticated user (admin/editor/viewer) — printing
    the plan is a read action.
    """
    plan = await _get_plan_or_404(db, plan_id)

    # Load every shift in the plan + the leader + session_type needed by
    # the renderer. One round-trip with selectinload — avoids N+1 lazy
    # loads inside render_plan_pdf.
    result = await db.execute(
        select(TrainingShift)
        .join(TrainingSessionType)
        .where(TrainingSessionType.plan_id == plan_id)
        .options(
            selectinload(TrainingShift.session_type),
            selectinload(TrainingShift.leader),
        )
        .order_by(TrainingShift.date.asc(), TrainingSessionType.name.asc())
    )
    shifts = list(result.scalars().all())

    pdf_bytes = render_plan_pdf(plan, shifts)

    # Sanitize the filename — strip newlines and constrain to ASCII-ish
    # so Content-Disposition stays well-formed across browsers.
    safe_name = (
        plan.name.replace("\n", " ").replace("\r", " ").replace('"', "")
        if plan.name
        else f"plan-{plan_id}"
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}.pdf"',
        },
    )


# ============================================================
# Training session types
# ============================================================

@router.get("/session-types", response_model=TrainingSessionTypeListResponse)
async def list_session_types(
    plan_id: Optional[int] = Query(
        None,
        description=(
            "Filter to a single training plan. When omitted, returns "
            "session types from every plan."
        ),
    ),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List training session types, optionally scoped to one plan."""
    stmt = select(TrainingSessionType).options(
        selectinload(TrainingSessionType.group),
        selectinload(TrainingSessionType.leader_group),
    )
    if plan_id is not None:
        stmt = stmt.where(TrainingSessionType.plan_id == plan_id)
    stmt = stmt.order_by(TrainingSessionType.name.asc())
    result = await db.execute(stmt)
    items = result.scalars().all()
    return TrainingSessionTypeListResponse(
        items=[TrainingSessionTypeResponse.model_validate(o) for o in items],
        total=len(items),
    )


@router.post(
    "/session-types",
    response_model=TrainingSessionTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_type(
    data: TrainingSessionTypeCreate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a training session type (admin only)."""
    obj = TrainingSessionType(**data.model_dump())
    db.add(obj)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Session type with name {data.name!r} already exists",
        )

    # Re-fetch with relationships eager-loaded so Pydantic can serialize
    # without triggering lazy IO at attribute-access time. A targeted
    # `db.refresh(obj, attribute_names=[...])` is not enough — server-side
    # defaults like updated_at also expire after commit.
    fresh = await _get_session_type_or_404(db, obj.id)
    return TrainingSessionTypeResponse.model_validate(fresh)


@router.patch("/session-types/{session_type_id}", response_model=TrainingSessionTypeResponse)
async def update_session_type(
    session_type_id: int,
    data: TrainingSessionTypeUpdate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a training session type (admin only)."""
    obj = await _get_session_type_or_404(db, session_type_id)

    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(obj, key, value)

    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Session type name conflicts with an existing record",
        )

    # Re-fetch fresh — see create_session_type for why a targeted refresh
    # isn't enough.
    fresh = await _get_session_type_or_404(db, obj.id)
    return TrainingSessionTypeResponse.model_validate(fresh)


@router.delete("/session-types/{session_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_type(
    session_type_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a training session type (admin only). Refuses if shifts exist."""
    obj = await _get_session_type_or_404(db, session_type_id)

    shift_count = await db.scalar(
        select(func.count(TrainingShift.id)).where(
            TrainingShift.session_type_id == session_type_id
        )
    )
    if shift_count:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete session type — {shift_count} shift(s) still reference it. "
                "Remove or reassign those shifts first."
            ),
        )

    await db.delete(obj)
    await db.commit()
    return None


# ============================================================
# Member aliases (initials)
# ============================================================

@router.get("/aliases", response_model=MemberAliasListResponse)
async def list_aliases(
    member_id: Optional[int] = Query(None, description="Filter by member id"),
    search: Optional[str] = Query(None, description="Substring match on initials"),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List member aliases (admin/editor/viewer)."""
    stmt = select(MemberAlias).options(selectinload(MemberAlias.member))
    if member_id is not None:
        stmt = stmt.where(MemberAlias.member_id == member_id)
    if search:
        stmt = stmt.where(MemberAlias.initials.ilike(f"%{search}%"))
    stmt = stmt.order_by(MemberAlias.initials.asc())

    result = await db.execute(stmt)
    items = result.scalars().all()
    return MemberAliasListResponse(
        items=[MemberAliasResponse.model_validate(o) for o in items],
        total=len(items),
    )


@router.post(
    "/aliases",
    response_model=MemberAliasResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alias(
    data: MemberAliasCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Create a member alias (admin/editor)."""
    await _ensure_member_exists(db, data.member_id)

    obj = MemberAlias(
        member_id=data.member_id,
        initials=data.initials,
        source=data.source,
    )
    db.add(obj)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Alias {data.initials!r} already exists",
        )

    # Reload with the member relationship eagerly for the response.
    return MemberAliasResponse.model_validate(await _get_alias_or_404(db, obj.id))


@router.patch("/aliases/{alias_id}", response_model=MemberAliasResponse)
async def update_alias(
    alias_id: int,
    data: MemberAliasUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Update a member alias (admin/editor)."""
    obj = await _get_alias_or_404(db, alias_id)

    changes = data.model_dump(exclude_unset=True)
    if "member_id" in changes and changes["member_id"] is not None:
        await _ensure_member_exists(db, changes["member_id"])

    for key, value in changes.items():
        if value is None and key in {"initials", "member_id", "source"}:
            # Don't null out non-nullable columns from a PATCH.
            continue
        setattr(obj, key, value)

    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Alias initials conflict with an existing record",
        )

    return MemberAliasResponse.model_validate(await _get_alias_or_404(db, obj.id))


@router.delete("/aliases/{alias_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alias(
    alias_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Delete a member alias (admin/editor)."""
    obj = await _get_alias_or_404(db, alias_id)
    await db.delete(obj)
    await db.commit()
    return None


# ============================================================
# Training shifts
# ============================================================

async def _load_shift_for_response(
    db: AsyncSession, shift_id: int
) -> TrainingShift:
    """Reload a shift with `session_type` and `leader` eagerly attached.

    Used after creates / updates so the response schema can validate.
    """
    result = await db.execute(
        select(TrainingShift)
        .options(
            selectinload(TrainingShift.session_type).selectinload(
                TrainingSessionType.group
            ),
            selectinload(TrainingShift.session_type).selectinload(
                TrainingSessionType.leader_group
            ),
            selectinload(TrainingShift.leader),
        )
        .where(TrainingShift.id == shift_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return obj


def _parse_month(month: str) -> tuple[date_type, date_type]:
    """Parse a YYYY-MM string into (first_day, last_day_inclusive)."""
    try:
        year_s, mon_s = month.split("-", 1)
        year, mon = int(year_s), int(mon_s)
        if not (1 <= mon <= 12):
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid month parameter {month!r}; expected YYYY-MM",
        )
    last_day = calendar.monthrange(year, mon)[1]
    return date_type(year, mon, 1), date_type(year, mon, last_day)


@router.get("/shifts", response_model=TrainingShiftListResponse)
async def list_shifts(
    month: Optional[str] = Query(
        None, description="Filter to a single month, format YYYY-MM"
    ),
    plan_id: Optional[int] = Query(
        None,
        description=(
            "Filter to a single training plan via the shifts' session_type. "
            "When omitted, returns shifts from every plan."
        ),
    ),
    session_type_id: Optional[int] = Query(
        None, description="Filter by session type id"
    ),
    leader_member_id: Optional[int] = Query(
        None, description="Filter by resolved leader member id"
    ),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status (draft/published/cancelled)"
    ),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List training shifts ordered by date then session-type name (admin/editor/viewer)."""
    stmt = select(TrainingShift).options(
        selectinload(TrainingShift.session_type).selectinload(
            TrainingSessionType.group
        ),
        selectinload(TrainingShift.session_type).selectinload(
            TrainingSessionType.leader_group
        ),
        selectinload(TrainingShift.leader),
    )
    if month:
        start, end = _parse_month(month)
        stmt = stmt.where(TrainingShift.date >= start, TrainingShift.date <= end)
    if session_type_id is not None:
        stmt = stmt.where(TrainingShift.session_type_id == session_type_id)
    if leader_member_id is not None:
        stmt = stmt.where(TrainingShift.leader_member_id == leader_member_id)
    if status_filter:
        stmt = stmt.where(TrainingShift.status == status_filter)
    stmt = stmt.join(TrainingSessionType)
    if plan_id is not None:
        stmt = stmt.where(TrainingSessionType.plan_id == plan_id)
    stmt = stmt.order_by(
        TrainingShift.date.asc(),
        TrainingSessionType.name.asc(),
    )

    result = await db.execute(stmt)
    items = result.scalars().unique().all()
    return TrainingShiftListResponse(
        items=[TrainingShiftResponse.model_validate(o) for o in items],
        total=len(items),
    )


@router.post(
    "/shifts",
    response_model=TrainingShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_shift(
    data: TrainingShiftCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Create a training shift (admin/editor). Refuses duplicates."""
    await _get_session_type_or_404(db, data.session_type_id)
    if data.leader_member_id is not None:
        await _ensure_member_exists(db, data.leader_member_id)

    # Duplicate check up front for a friendlier error than IntegrityError.
    existing = await db.execute(
        select(TrainingShift.id).where(
            TrainingShift.session_type_id == data.session_type_id,
            TrainingShift.date == data.date,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A shift for session_type_id={data.session_type_id} on "
                f"{data.date} already exists"
            ),
        )

    obj = TrainingShift(
        session_type_id=data.session_type_id,
        date=data.date,
        leader_member_id=data.leader_member_id,
        raw_initials=data.raw_initials,
        notes=data.notes,
        start_time_override=data.start_time_override,
        end_time_override=data.end_time_override,
        status="draft",
    )
    db.add(obj)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Shift creation conflicted with an existing record",
        )

    obj = await _load_shift_for_response(db, obj.id)
    return TrainingShiftResponse.model_validate(obj)


@router.patch("/shifts/{shift_id}", response_model=TrainingShiftResponse)
async def update_shift(
    shift_id: int,
    data: TrainingShiftUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Partial update. Published shifts only allow `notes`, `status` and `spond_event_id`."""
    obj = await _load_shift_for_response(db, shift_id)
    changes = data.model_dump(exclude_unset=True)

    if obj.status == "published":
        # Lock leader/times to whatever was sent to Spond; only notes,
        # cancellation, and (rarely) re-linking spond_event_id are allowed.
        allowed = {"notes", "status", "spond_event_id"}
        rejected = [k for k in changes if k not in allowed]
        if rejected:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Shift is published; only "
                    + ", ".join(sorted(allowed))
                    + f" may be modified. Refused: {', '.join(rejected)}"
                ),
            )

    if "leader_member_id" in changes and changes["leader_member_id"] is not None:
        await _ensure_member_exists(db, changes["leader_member_id"])
    if "status" in changes and changes["status"] not in {
        "draft",
        "published",
        "cancelled",
    }:
        raise HTTPException(
            status_code=400, detail="Invalid status value"
        )

    for key, value in changes.items():
        setattr(obj, key, value)

    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Shift update conflicted with the unique constraint",
        )

    obj = await _load_shift_for_response(db, shift_id)
    return TrainingShiftResponse.model_validate(obj)


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shift(
    shift_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a shift (admin only). Refuses if published — cancel via PATCH first."""
    obj = await _load_shift_for_response(db, shift_id)
    if obj.status == "published":
        raise HTTPException(
            status_code=409,
            detail=(
                "Shift is published — cancel it via PATCH (status=cancelled) "
                "first to preserve the audit trail."
            ),
        )
    await db.delete(obj)
    await db.commit()
    return None


# ============================================================
# Excel importer
# ============================================================

@router.post("/plans/{plan_id}/import", response_model=ImportReport)
async def import_xlsx(
    plan_id: int,
    file: UploadFile = File(..., description="Vaktliste .xlsx file"),
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Import a vaktliste .xlsx into a specific training plan (admin only).

    Session-type dedup is scoped to `(plan_id, name)` — importing the same
    xlsx shape into two different plans creates parallel session-type sets.
    """
    await _get_plan_or_404(db, plan_id)

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        report = await training_import_service.import_xlsx(
            db, contents, plan_id=plan_id
        )
        await db.commit()
        return report
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        await db.rollback()
        logger.exception("Vaktliste import failed")
        raise HTTPException(
            status_code=500, detail=f"Import failed: {exc}"
        )


# ============================================================
# Per-shift publish
# ============================================================

@router.post("/shifts/{shift_id}/publish", response_model=TrainingShiftResponse)
async def publish_shift(
    shift_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a Spond event from a single draft shift (admin only).

    This is the **manual, per-shift** publish path. There is intentionally no
    bulk endpoint — admins must trigger each shift individually so the
    audience, leader, and send-at fields can be reviewed before a real Spond
    invitation goes out.
    """
    from app.core.config import settings

    if not (settings.SPOND_USERNAME and settings.SPOND_PASSWORD):
        raise HTTPException(
            status_code=503,
            detail=(
                "Spond credentials are not configured on this server. "
                "Set SPOND_USERNAME and SPOND_PASSWORD or create the event "
                "manually and link it via PATCH /training/shifts/{id} with "
                "spond_event_id."
            ),
        )

    obj = await _load_shift_for_response(db, shift_id)
    if obj.status != "draft":
        raise HTTPException(
            status_code=409,
            detail=f"Shift is {obj.status!r}; only draft shifts can be published",
        )

    spond = await get_spond_service()
    try:
        payload = await spond_event_create_service.build_payload_from_shift(
            db, obj
        )
        response = await spond_event_create_service.create_event(spond, payload)
    except SpondCreateError as exc:
        logger.warning("Spond publish failed for shift %s: %s", shift_id, exc)
        msg = str(exc)
        # Known upstream issue (Olen/Spond#229): login URL returns 404. The
        # spond library can't authenticate, so no Spond call actually
        # happened — the shift is unchanged. Surface a clearer hint so the
        # admin doesn't think *our* code is broken.
        if "/login" in msg and "404" in msg:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Spond's login endpoint is returning 404 — this is an "
                    "upstream issue in the spond library "
                    "(github.com/Olen/Spond/issues/229). No event was "
                    "created on Spond, the shift is still in draft. Until "
                    "this is fixed, create the event manually in Spond and "
                    "link it via PATCH /training/shifts/{id} with "
                    "spond_event_id."
                ),
            )
        raise HTTPException(
            status_code=502,
            detail=f"Spond rejected the event: {exc}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error publishing shift %s", shift_id)
        raise HTTPException(
            status_code=502,
            detail=f"Spond create_event failed: {exc}",
        )

    spond_event_id = response.get("id") or response.get("uid")
    if not spond_event_id:
        logger.error("Spond response missing id/uid: %s", response)
        raise HTTPException(
            status_code=502,
            detail="Spond response did not include an event id",
        )

    obj.spond_event_id = spond_event_id
    obj.status = "published"
    from datetime import datetime as _dt

    obj.published_at = _dt.utcnow()
    await db.commit()

    obj = await _load_shift_for_response(db, shift_id)
    return TrainingShiftResponse.model_validate(obj)


# ============================================================
# Leader groups
# ============================================================

async def _get_leader_group_or_404(
    db: AsyncSession, leader_group_id: int
) -> LeaderGroup:
    result = await db.execute(
        select(LeaderGroup)
        .options(selectinload(LeaderGroup.members))
        .where(LeaderGroup.id == leader_group_id)
    )
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="Leader group not found")
    return obj


@router.get("/leader-groups", response_model=LeaderGroupListResponse)
async def list_leader_groups(
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all leader groups with their members."""
    result = await db.execute(
        select(LeaderGroup)
        .options(selectinload(LeaderGroup.members))
        .order_by(LeaderGroup.name.asc())
    )
    items = result.scalars().unique().all()
    return LeaderGroupListResponse(
        items=[LeaderGroupResponse.model_validate(o) for o in items],
        total=len(items),
    )


@router.post(
    "/leader-groups",
    response_model=LeaderGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_leader_group(
    data: LeaderGroupCreate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a leader group (admin only). Optionally seed with member ids."""
    obj = LeaderGroup(name=data.name, description=data.description)
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Leader group {data.name!r} already exists",
        )

    if data.member_ids:
        await _replace_leader_group_members(db, obj.id, data.member_ids)

    await db.commit()
    fresh = await _get_leader_group_or_404(db, obj.id)
    return LeaderGroupResponse.model_validate(fresh)


@router.patch("/leader-groups/{leader_group_id}", response_model=LeaderGroupResponse)
async def update_leader_group(
    leader_group_id: int,
    data: LeaderGroupUpdate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Rename / re-describe a leader group (admin only)."""
    obj = await _get_leader_group_or_404(db, leader_group_id)
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(obj, key, value)
    try:
        await db.flush()
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Leader group name conflicts with an existing record",
        )
    fresh = await _get_leader_group_or_404(db, obj.id)
    return LeaderGroupResponse.model_validate(fresh)


@router.delete(
    "/leader-groups/{leader_group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_leader_group(
    leader_group_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a leader group. Session types that referenced it are not deleted —
    the FK is ON DELETE SET NULL, so they fall back to inheriting nothing."""
    obj = await _get_leader_group_or_404(db, leader_group_id)
    await db.delete(obj)
    await db.commit()
    return None


@router.put("/leader-groups/{leader_group_id}/members", response_model=LeaderGroupResponse)
async def replace_leader_group_members(
    leader_group_id: int,
    data: LeaderGroupMembersUpdate,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Replace the leader group's full member roster with the given list."""
    await _get_leader_group_or_404(db, leader_group_id)
    await _replace_leader_group_members(db, leader_group_id, data.member_ids)
    await db.commit()
    fresh = await _get_leader_group_or_404(db, leader_group_id)
    return LeaderGroupResponse.model_validate(fresh)


async def _replace_leader_group_members(
    db: AsyncSession, leader_group_id: int, member_ids: list[int]
) -> None:
    """Wipe and recreate the leader_group_members rows for one group."""
    from sqlalchemy import delete

    await db.execute(
        delete(LeaderGroupMember).where(
            LeaderGroupMember.leader_group_id == leader_group_id
        )
    )
    if not member_ids:
        return

    # Validate that all referenced member ids exist; missing ones produce a 400.
    existing = await db.execute(
        select(Member.id).where(Member.id.in_(member_ids))
    )
    existing_ids = {row for row, in existing.all()}
    missing = [mid for mid in member_ids if mid not in existing_ids]
    if missing:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Unknown member ids: {sorted(missing)}",
        )

    for mid in dict.fromkeys(member_ids):  # de-dup while preserving order
        db.add(LeaderGroupMember(leader_group_id=leader_group_id, member_id=mid))
    await db.flush()
