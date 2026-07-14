"""
Prosjekter (Plane-like project management) API.

Access policy:
- Read (all GET endpoints): any authenticated user — viewers and kasserer
  included (``get_current_user``).
- Write (POST/PATCH/DELETE, including comments/links/relations and
  ``/import``): editor or above (``get_current_editor_or_above``).
- Deleting a whole project is destructive: admin only
  (``get_current_admin``).
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    get_current_admin,
    get_current_editor_or_above,
    get_current_user,
)
from app.db.session import get_db
from app.models.admin import Admin, UserRole
from app.models.project import Project, ProjectState
from app.models.work_item import WorkItem, WorkItemComment
from app.schemas.project import (
    BoardColumn,
    BoardResponse,
    CommentCreate,
    CommentOut,
    CommentUpdate,
    CycleCreate,
    CycleOut,
    CycleUpdate,
    LabelCreate,
    LabelOut,
    LabelUpdate,
    LinkCreate,
    LinkOut,
    ModuleCreate,
    ModuleOut,
    ModuleUpdate,
    PersonOut,
    PlaneImportResult,
    PlaneWorkItemIn,
    ProjectCreate,
    ProjectDetail,
    ProjectListItem,
    ProjectListResponse,
    ProjectUpdate,
    RelationCreate,
    RelationOut,
    StateCreate,
    StateOut,
    StateUpdate,
    WorkItemCreate,
    WorkItemDetail,
    WorkItemListItem,
    WorkItemListResponse,
    WorkItemUpdate,
)
from app.services.plane_import_service import PlaneImportError, PlaneImportService
from app.services.project_service import ProjectService, ProjectValidationError

logger = logging.getLogger(__name__)
router = APIRouter()

# NOTE — ROUTE ORDERING: all literal prefixes (/import, /work-items/...,
# /comments/..., /links/..., /relations/...) MUST be declared before the
# /{project_id} routes so the int path converter doesn't shadow them.


# ---- helpers -----------------------------------------------------------------

async def _get_project_or_404(db: AsyncSession, project_id: int) -> Project:
    project = await ProjectService.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Prosjekt ikke funnet")
    return project


async def _get_item_or_404(db: AsyncSession, item_id: int) -> WorkItem:
    item = await ProjectService.get_work_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Sak ikke funnet")
    return item


async def _names_map(db: AsyncSession, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    rows = (await db.execute(
        select(Admin.id, Admin.full_name, Admin.email).where(Admin.id.in_(ids))
    )).all()
    return {r.id: (r.full_name or r.email) for r in rows}


def _state_out(state: ProjectState, item_count: int = 0) -> StateOut:
    out = StateOut.model_validate(state)
    out.item_count = item_count
    return out


def _serialize_item(
    item: WorkItem,
    project_identifier: str,
    *,
    parent_sequence_id: Optional[int] = None,
    sub_item_count: int = 0,
    comment_count: int = 0,
) -> WorkItemListItem:
    """Compose a WorkItemListItem — identifier and parent_identifier are
    built from the project row the caller already has (no lazy loads)."""
    return WorkItemListItem(
        id=item.id,
        identifier=f"{project_identifier}-{item.sequence_id}",
        project_id=item.project_id,
        sequence_id=item.sequence_id,
        name=item.name,
        state=StateOut.model_validate(item.state) if item.state else None,
        priority=item.priority,
        parent_id=item.parent_id,
        parent_identifier=(
            f"{project_identifier}-{parent_sequence_id}"
            if parent_sequence_id is not None else None
        ),
        start_date=item.start_date,
        target_date=item.target_date,
        completed_at=item.completed_at,
        is_draft=item.is_draft,
        sort_order=item.sort_order,
        sub_item_count=sub_item_count,
        comment_count=comment_count,
        assignees=[
            PersonOut.model_validate(p) for p in item.people if p.kind == "assignee"
        ],
        labels=[LabelOut.model_validate(l) for l in item.labels],
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


async def _parent_sequence_map(
    db: AsyncSession, items: List[WorkItem]
) -> dict[int, int]:
    """{parent work_item id: sequence_id} for the parents referenced by items."""
    parent_ids = {i.parent_id for i in items if i.parent_id}
    if not parent_ids:
        return {}
    rows = (await db.execute(
        select(WorkItem.id, WorkItem.sequence_id).where(WorkItem.id.in_(parent_ids))
    )).all()
    return {r.id: r.sequence_id for r in rows}


async def _serialize_relations(
    db: AsyncSession, item: WorkItem
) -> List[RelationOut]:
    """Relation rows with target name/group/project filled in one batched query."""
    target_ids = {r.related_work_item_id for r in item.relations if r.related_work_item_id}
    target_info: dict[int, tuple] = {}
    if target_ids:
        rows = (await db.execute(
            select(
                WorkItem.id, WorkItem.name, WorkItem.project_id,
                ProjectState.state_group,
            )
            .outerjoin(ProjectState, WorkItem.state_id == ProjectState.id)
            .where(WorkItem.id.in_(target_ids))
        )).all()
        target_info = {r.id: (r.name, r.state_group, r.project_id) for r in rows}

    out: List[RelationOut] = []
    for relation in item.relations:
        ro = RelationOut(
            id=relation.id,
            relation_type=relation.relation_type,
            direction=relation.direction,
            related_identifier=relation.related_identifier,
            related_work_item_id=relation.related_work_item_id,
        )
        info = target_info.get(relation.related_work_item_id)
        if info:
            ro.related_name, ro.related_state_group, ro.related_project_id = info
        out.append(ro)
    return out


async def _serialize_item_detail(
    db: AsyncSession, item: WorkItem, project: Project
) -> WorkItemDetail:
    item_ids = [item.id] + [c.id for c in item.children]
    sub_counts, comment_counts = await ProjectService.child_and_comment_counts(
        db, item_ids
    )
    parent_sequence_id = item.parent.sequence_id if item.parent else None

    base = _serialize_item(
        item, project.identifier,
        parent_sequence_id=parent_sequence_id,
        sub_item_count=sub_counts.get(item.id, 0),
        comment_count=comment_counts.get(item.id, 0),
    )
    created_by_name = item.created_by_name
    if not created_by_name and item.created_by_id:
        names = await _names_map(db, {item.created_by_id})
        created_by_name = names.get(item.created_by_id)

    return WorkItemDetail(
        **base.model_dump(),
        description=item.description,
        estimate=item.estimate,
        archived_at=item.archived_at,
        created_by_name=created_by_name,
        subscribers=[
            PersonOut.model_validate(p) for p in item.people if p.kind == "subscriber"
        ],
        cycles=[CycleOut.model_validate(c) for c in item.cycles],
        modules=[ModuleOut.model_validate(m) for m in item.modules],
        links=[LinkOut.model_validate(l) for l in item.links],
        relations=await _serialize_relations(db, item),
        children=[
            _serialize_item(
                child, project.identifier,
                parent_sequence_id=item.sequence_id,
                sub_item_count=sub_counts.get(child.id, 0),
                comment_count=comment_counts.get(child.id, 0),
            )
            for child in item.children
        ],
        comments=[CommentOut.model_validate(c) for c in item.comments],
    )


async def _serialize_project_detail(db: AsyncSession, project: Project) -> ProjectDetail:
    totals = await ProjectService.project_item_counts(db, [project.id])
    total_items, completed_items = totals.get(project.id, (0, 0))
    state_counts = await ProjectService.state_item_counts(db, project.id)
    created_by_name = project.created_by_name
    if not created_by_name and project.created_by_id:
        names = await _names_map(db, {project.created_by_id})
        created_by_name = names.get(project.created_by_id)
    return ProjectDetail(
        id=project.id,
        name=project.name,
        identifier=project.identifier,
        description=project.description,
        is_archived=project.is_archived,
        total_items=total_items,
        completed_items=completed_items,
        created_at=project.created_at,
        updated_at=project.updated_at,
        states=[_state_out(s, state_counts.get(s.id, 0)) for s in project.states],
        labels=[LabelOut.model_validate(l) for l in project.labels],
        cycles=[CycleOut.model_validate(c) for c in project.cycles],
        modules=[ModuleOut.model_validate(m) for m in project.modules],
        created_by_name=created_by_name,
    )


def _require_comment_author_or_admin(comment: WorkItemComment, user: Admin) -> None:
    if comment.created_by_id != user.id and user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=403, detail="Du kan bare endre dine egne kommentarer"
        )


# ---- Plane import (editor+) --------------------------------------------------

@router.post("/import", response_model=PlaneImportResult)
async def import_from_plane(
    items: List[PlaneWorkItemIn],
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    """Import/sync a Plane work-item export (the raw JSON array as body)."""
    try:
        return await PlaneImportService.import_items(db, items, current_user)
    except PlaneImportError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # noqa: BLE001 — single transaction: roll back everything
        await db.rollback()
        logger.exception("Plane import failed")
        raise HTTPException(status_code=400, detail=f"Ugyldig Plane-eksport: {e}")


# ---- work items by id --------------------------------------------------------

@router.get("/work-items/{item_id}", response_model=WorkItemDetail)
async def get_work_item(
    item_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    project = await _get_project_or_404(db, item.project_id)
    return await _serialize_item_detail(db, item, project)


@router.patch("/work-items/{item_id}", response_model=WorkItemDetail)
async def update_work_item(
    item_id: int,
    payload: WorkItemUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    try:
        item = await ProjectService.update_work_item(db, item, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    project = await _get_project_or_404(db, item.project_id)
    return await _serialize_item_detail(db, item, project)


@router.delete("/work-items/{item_id}")
async def delete_work_item(
    item_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    await ProjectService.delete_work_item(db, item)
    return {"status": "deleted", "id": item_id}


# ---- comments ----------------------------------------------------------------

@router.post("/work-items/{item_id}/comments", response_model=CommentOut)
async def add_comment(
    item_id: int,
    payload: CommentCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    comment = await ProjectService.add_comment(db, item, payload.body, current_user)
    return CommentOut.model_validate(comment)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    comment = await ProjectService.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Kommentar ikke funnet")
    _require_comment_author_or_admin(comment, current_user)
    comment = await ProjectService.update_comment(db, comment, payload.body)
    return CommentOut.model_validate(comment)


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    comment = await ProjectService.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Kommentar ikke funnet")
    _require_comment_author_or_admin(comment, current_user)
    await ProjectService.delete_comment(db, comment)
    return {"status": "deleted", "id": comment_id}


# ---- links -------------------------------------------------------------------

@router.post("/work-items/{item_id}/links", response_model=LinkOut)
async def add_link(
    item_id: int,
    payload: LinkCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    link = await ProjectService.add_link(db, item, payload.url, payload.title)
    return LinkOut.model_validate(link)


@router.delete("/links/{link_id}")
async def delete_link(
    link_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    link = await ProjectService.get_link(db, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Lenke ikke funnet")
    await ProjectService.delete_link(db, link)
    return {"status": "deleted", "id": link_id}


# ---- relations ---------------------------------------------------------------

@router.post("/work-items/{item_id}/relations", response_model=RelationOut)
async def add_relation(
    item_id: int,
    payload: RelationCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    item = await _get_item_or_404(db, item_id)
    try:
        relation = await ProjectService.add_relation(db, item, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    item = await _get_item_or_404(db, item_id)
    for ro in await _serialize_relations(db, item):
        if ro.id == relation.id:
            return ro
    return RelationOut.model_validate(relation)


@router.delete("/relations/{relation_id}")
async def delete_relation(
    relation_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    relation = await ProjectService.get_relation(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="Relasjon ikke funnet")
    await ProjectService.delete_relation(db, relation)
    return {"status": "deleted", "id": relation_id}


# ---- projects ----------------------------------------------------------------

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    include_archived: bool = Query(False),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects, total = await ProjectService.list_projects(
        db, include_archived=include_archived
    )
    counts = await ProjectService.project_item_counts(db, [p.id for p in projects])
    items: List[ProjectListItem] = []
    for project in projects:
        item = ProjectListItem.model_validate(project)
        item.total_items, item.completed_items = counts.get(project.id, (0, 0))
        items.append(item)
    return ProjectListResponse(items=items, total=total)


@router.post("/", response_model=ProjectDetail)
async def create_project(
    payload: ProjectCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    try:
        project = await ProjectService.create_project(db, payload, current_user)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize_project_detail(db, project)


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    return await _serialize_project_detail(db, project)


@router.patch("/{project_id}", response_model=ProjectDetail)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    try:
        project = await ProjectService.update_project(db, project, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize_project_detail(db, project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    current_user: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Destructive: removes the project and every work item in it. Admin only."""
    project = await _get_project_or_404(db, project_id)
    await ProjectService.delete_project(db, project)
    return {"status": "deleted", "id": project_id}


# ---- work items within a project ----------------------------------------------

@router.get("/{project_id}/work-items", response_model=WorkItemListResponse)
async def list_work_items(
    project_id: int,
    state_id: Optional[int] = Query(None),
    priority: Optional[str] = Query(None),
    label_id: Optional[int] = Query(None),
    cycle_id: Optional[int] = Query(None),
    module_id: Optional[int] = Query(None),
    assignee: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    top_level_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    items, total = await ProjectService.list_work_items(
        db, project_id,
        state_id=state_id, priority=priority, label_id=label_id,
        cycle_id=cycle_id, module_id=module_id, assignee=assignee,
        search=search, parent_id=parent_id, top_level_only=top_level_only,
        skip=skip, limit=limit,
    )
    sub_counts, comment_counts = await ProjectService.child_and_comment_counts(
        db, [i.id for i in items]
    )
    parent_sequences = await _parent_sequence_map(db, items)
    return WorkItemListResponse(
        items=[
            _serialize_item(
                item, project.identifier,
                parent_sequence_id=parent_sequences.get(item.parent_id),
                sub_item_count=sub_counts.get(item.id, 0),
                comment_count=comment_counts.get(item.id, 0),
            )
            for item in items
        ],
        total=total,
    )


@router.post("/{project_id}/work-items", response_model=WorkItemDetail)
async def create_work_item(
    project_id: int,
    payload: WorkItemCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    try:
        item = await ProjectService.create_work_item(db, project, payload, current_user)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return await _serialize_item_detail(db, item, project)


@router.get("/{project_id}/board", response_model=BoardResponse)
async def get_board(
    project_id: int,
    priority: Optional[str] = Query(None),
    label_id: Optional[int] = Query(None),
    cycle_id: Optional[int] = Query(None),
    module_id: Optional[int] = Query(None),
    assignee: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: Admin = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """One column per state (ordered by position) — board-friendly single call."""
    project = await _get_project_or_404(db, project_id)
    columns = await ProjectService.board(
        db, project_id,
        priority=priority, label_id=label_id, cycle_id=cycle_id,
        module_id=module_id, assignee=assignee, search=search,
    )
    all_items = [item for _, items in columns for item in items]
    sub_counts, comment_counts = await ProjectService.child_and_comment_counts(
        db, [i.id for i in all_items]
    )
    parent_sequences = await _parent_sequence_map(db, all_items)
    return BoardResponse(columns=[
        BoardColumn(
            state=_state_out(state, len(items)),
            items=[
                _serialize_item(
                    item, project.identifier,
                    parent_sequence_id=parent_sequences.get(item.parent_id),
                    sub_item_count=sub_counts.get(item.id, 0),
                    comment_count=comment_counts.get(item.id, 0),
                )
                for item in items
            ],
            total=len(items),
        )
        for state, items in columns
    ])


# ---- states ------------------------------------------------------------------

@router.post("/{project_id}/states", response_model=StateOut)
async def create_state(
    project_id: int,
    payload: StateCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    try:
        state = await ProjectService.create_state(db, project, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _state_out(state)


@router.patch("/{project_id}/states/{state_id}", response_model=StateOut)
async def update_state(
    project_id: int,
    state_id: int,
    payload: StateUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    state = await ProjectService.get_state(db, state_id)
    if not state or state.project_id != project_id:
        raise HTTPException(status_code=404, detail="Status ikke funnet")
    try:
        state = await ProjectService.update_state(db, state, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _state_out(state)


@router.delete("/{project_id}/states/{state_id}")
async def delete_state(
    project_id: int,
    state_id: int,
    move_to: Optional[int] = Query(None, description="State id sakene flyttes til"),
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    state = await ProjectService.get_state(db, state_id)
    if not state or state.project_id != project_id:
        raise HTTPException(status_code=404, detail="Status ikke funnet")
    try:
        await ProjectService.delete_state(db, state, move_to_state_id=move_to)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "deleted", "id": state_id}


# ---- labels ------------------------------------------------------------------

@router.post("/{project_id}/labels", response_model=LabelOut)
async def create_label(
    project_id: int,
    payload: LabelCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    try:
        label = await ProjectService.create_label(db, project, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return LabelOut.model_validate(label)


@router.patch("/{project_id}/labels/{label_id}", response_model=LabelOut)
async def update_label(
    project_id: int,
    label_id: int,
    payload: LabelUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    label = await ProjectService.get_label(db, label_id)
    if not label or label.project_id != project_id:
        raise HTTPException(status_code=404, detail="Etikett ikke funnet")
    label = await ProjectService.update_label(db, label, payload)
    return LabelOut.model_validate(label)


@router.delete("/{project_id}/labels/{label_id}")
async def delete_label(
    project_id: int,
    label_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    label = await ProjectService.get_label(db, label_id)
    if not label or label.project_id != project_id:
        raise HTTPException(status_code=404, detail="Etikett ikke funnet")
    await ProjectService.delete_label(db, label)
    return {"status": "deleted", "id": label_id}


# ---- cycles ------------------------------------------------------------------

@router.post("/{project_id}/cycles", response_model=CycleOut)
async def create_cycle(
    project_id: int,
    payload: CycleCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    try:
        cycle = await ProjectService.create_cycle(db, project, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CycleOut.model_validate(cycle)


@router.patch("/{project_id}/cycles/{cycle_id}", response_model=CycleOut)
async def update_cycle(
    project_id: int,
    cycle_id: int,
    payload: CycleUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    cycle = await ProjectService.get_cycle(db, cycle_id)
    if not cycle or cycle.project_id != project_id:
        raise HTTPException(status_code=404, detail="Syklus ikke funnet")
    cycle = await ProjectService.update_cycle(db, cycle, payload)
    return CycleOut.model_validate(cycle)


@router.delete("/{project_id}/cycles/{cycle_id}")
async def delete_cycle(
    project_id: int,
    cycle_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    cycle = await ProjectService.get_cycle(db, cycle_id)
    if not cycle or cycle.project_id != project_id:
        raise HTTPException(status_code=404, detail="Syklus ikke funnet")
    await ProjectService.delete_cycle(db, cycle)
    return {"status": "deleted", "id": cycle_id}


# ---- modules -----------------------------------------------------------------

@router.post("/{project_id}/modules", response_model=ModuleOut)
async def create_module(
    project_id: int,
    payload: ModuleCreate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    project = await _get_project_or_404(db, project_id)
    try:
        module = await ProjectService.create_module(db, project, payload)
    except ProjectValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ModuleOut.model_validate(module)


@router.patch("/{project_id}/modules/{module_id}", response_model=ModuleOut)
async def update_module(
    project_id: int,
    module_id: int,
    payload: ModuleUpdate,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    module = await ProjectService.get_module(db, module_id)
    if not module or module.project_id != project_id:
        raise HTTPException(status_code=404, detail="Modul ikke funnet")
    module = await ProjectService.update_module(db, module, payload)
    return ModuleOut.model_validate(module)


@router.delete("/{project_id}/modules/{module_id}")
async def delete_module(
    project_id: int,
    module_id: int,
    current_user: Admin = Depends(get_current_editor_or_above),
    db: AsyncSession = Depends(get_db),
):
    module = await ProjectService.get_module(db, module_id)
    if not module or module.project_id != project_id:
        raise HTTPException(status_code=404, detail="Modul ikke funnet")
    await ProjectService.delete_module(db, module)
    return {"status": "deleted", "id": module_id}
