"""
Pydantic schemas for the Prosjekter (Plane-like project management) system.

Not registered in ``schemas/__init__.py`` (per convention) — the router
imports directly. State group / priority / relation vocabularies come from
``app.models.project`` (Plane-compatible English tokens; the frontend maps
them to Norwegian labels).
"""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.project import (
    RELATION_DIRECTIONS, RELATION_TYPES, STATE_GROUPS, WORK_ITEM_PRIORITIES,
)

_PRIORITY_PATTERN = r"^(" + "|".join(WORK_ITEM_PRIORITIES) + r")$"
_GROUP_PATTERN = r"^(" + "|".join(STATE_GROUPS) + r")$"
_RELTYPE_PATTERN = r"^(" + "|".join(RELATION_TYPES) + r")$"
_DIRECTION_PATTERN = r"^(" + "|".join(RELATION_DIRECTIONS) + r")$"


# ---- states -----------------------------------------------------------------

class StateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    # Maps to the model column ``state_group``.
    group: str = Field(default="unstarted", pattern=_GROUP_PATTERN)
    color: str = Field(default="#9CA3AF", max_length=7)
    position: int = 0


class StateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    group: Optional[str] = Field(default=None, pattern=_GROUP_PATTERN)
    color: Optional[str] = Field(default=None, max_length=7)
    position: Optional[int] = None
    is_default: Optional[bool] = None


class StateOut(BaseModel):
    # populate_by_name lets manual construction pass ``group=`` while
    # from_attributes reads the model column ``state_group``.
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    group: str = Field(validation_alias="state_group", serialization_alias="group")
    color: str
    position: int
    is_default: bool = False
    item_count: int = 0


# ---- labels / cycles / modules ------------------------------------------------

class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#6B7280", max_length=7)


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    color: Optional[str] = Field(default=None, max_length=7)


class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str


class CycleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class CycleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class ModuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None


class ModuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None


# ---- projects ----------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    identifier: str = Field(min_length=2, max_length=12, pattern=r"^[A-Z0-9]+$")
    description: Optional[str] = None

    @field_validator("identifier", mode="before")
    @classmethod
    def _uppercase_identifier(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    identifier: Optional[str] = Field(
        default=None, min_length=2, max_length=12, pattern=r"^[A-Z0-9]+$"
    )
    description: Optional[str] = None
    is_archived: Optional[bool] = None

    @field_validator("identifier", mode="before")
    @classmethod
    def _uppercase_identifier(cls, v):
        if isinstance(v, str):
            return v.strip().upper()
        return v


class ProjectListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    identifier: str
    description: Optional[str] = None
    is_archived: bool = False
    total_items: int = 0
    completed_items: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectListItem):
    states: List[StateOut] = []
    labels: List[LabelOut] = []
    cycles: List[CycleOut] = []
    modules: List[ModuleOut] = []
    created_by_name: Optional[str] = None


class ProjectListResponse(BaseModel):
    items: List[ProjectListItem]
    total: int


# ---- people ------------------------------------------------------------------

class PersonIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=255)
    member_id: Optional[int] = None
    admin_id: Optional[int] = None


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    display_name: str
    member_id: Optional[int] = None
    admin_id: Optional[int] = None


# ---- comments ----------------------------------------------------------------

class CommentCreate(BaseModel):
    body: str = Field(min_length=1)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    created_by_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ---- links -------------------------------------------------------------------

class LinkCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
    title: Optional[str] = Field(default=None, max_length=500)


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    title: Optional[str] = None


# ---- relations ---------------------------------------------------------------

class RelationCreate(BaseModel):
    relation_type: str = Field(default="relates_to", pattern=_RELTYPE_PATTERN)
    direction: str = Field(default="outgoing", pattern=_DIRECTION_PATTERN)
    related_identifier: Optional[str] = Field(default=None, max_length=32)
    related_work_item_id: Optional[int] = None

    @model_validator(mode="after")
    def _require_target(self):
        if not self.related_identifier and self.related_work_item_id is None:
            raise ValueError(
                "Enten related_identifier eller related_work_item_id må oppgis"
            )
        return self


class RelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    relation_type: str
    direction: str
    related_identifier: str
    related_work_item_id: Optional[int] = None
    # Filled by the router when the target resolves.
    related_name: Optional[str] = None
    related_state_group: Optional[str] = None
    related_project_id: Optional[int] = None


# ---- work items ---------------------------------------------------------------

class WorkItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    state_id: Optional[int] = None
    priority: str = Field(default="none", pattern=_PRIORITY_PATTERN)
    parent_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    estimate: Optional[str] = Field(default=None, max_length=32)
    label_ids: List[int] = []
    cycle_ids: List[int] = []
    module_ids: List[int] = []
    assignees: List[PersonIn] = []
    subscribers: List[PersonIn] = []
    is_draft: bool = False


class WorkItemUpdate(BaseModel):
    """Partial update — apply with ``exclude_unset``. List fields replace
    the existing collection wholesale when present."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    state_id: Optional[int] = None
    priority: Optional[str] = Field(default=None, pattern=_PRIORITY_PATTERN)
    parent_id: Optional[int] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    estimate: Optional[str] = Field(default=None, max_length=32)
    sort_order: Optional[float] = None
    is_draft: Optional[bool] = None
    label_ids: Optional[List[int]] = None
    cycle_ids: Optional[List[int]] = None
    module_ids: Optional[List[int]] = None
    assignees: Optional[List[PersonIn]] = None
    subscribers: Optional[List[PersonIn]] = None


class WorkItemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str  # composed "{project.identifier}-{sequence_id}"
    project_id: int
    sequence_id: int
    name: str
    state: Optional[StateOut] = None
    priority: str = "none"
    parent_id: Optional[int] = None
    parent_identifier: Optional[str] = None
    start_date: Optional[date] = None
    target_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    is_draft: bool = False
    sort_order: float = 0.0
    sub_item_count: int = 0
    comment_count: int = 0
    assignees: List[PersonOut] = []
    labels: List[LabelOut] = []
    created_at: datetime
    updated_at: datetime


class WorkItemDetail(WorkItemListItem):
    description: Optional[str] = None
    estimate: Optional[str] = None
    archived_at: Optional[datetime] = None
    created_by_name: Optional[str] = None
    subscribers: List[PersonOut] = []
    cycles: List[CycleOut] = []
    modules: List[ModuleOut] = []
    links: List[LinkOut] = []
    relations: List[RelationOut] = []
    children: List[WorkItemListItem] = []
    comments: List[CommentOut] = []


class WorkItemListResponse(BaseModel):
    items: List[WorkItemListItem]
    total: int


# ---- board -------------------------------------------------------------------

class BoardColumn(BaseModel):
    state: StateOut
    items: List[WorkItemListItem] = []
    total: int = 0


class BoardResponse(BaseModel):
    columns: List[BoardColumn] = []


# ---- Plane import -------------------------------------------------------------
# Input mirrors the Plane CSV/JSON export exactly; unknown keys are ignored.
# Date/timestamp strings are kept as ``str`` and parsed leniently in the
# import service (a bad value becomes a warning, not a 422 for the file).

class PlaneLinkIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str
    title: Optional[str] = None


class PlaneRelationIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = "relates_to"
    issue: str
    direction: str = "outgoing"


class PlaneCommentIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    comment: str
    created_by: Optional[str] = None
    created_at: Optional[str] = None


class PlaneWorkItemIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_name: str
    project_identifier: str
    parent: Optional[str] = ""            # "" or e.g. "STYRE-13"
    identifier: Optional[str] = None      # informational; sequence_id is authoritative
    sequence_id: int
    name: str
    state_name: Optional[str] = None
    priority: str = "none"
    assignees: List[str] = []
    subscribers: List[str] = []
    created_by_name: Optional[str] = None
    start_date: Optional[str] = None
    target_date: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    archived_at: Optional[str] = None
    estimate: Optional[str] = ""
    labels: List[str] = []
    cycles: List[str] = []
    modules: List[str] = []
    links: List[PlaneLinkIn] = []
    relations: List[PlaneRelationIn] = []
    comments: List[PlaneCommentIn] = []
    is_draft: bool = False


class PlaneImportResult(BaseModel):
    projects_created: List[str] = []
    projects_updated: List[str] = []
    items_created: int = 0
    items_updated: int = 0
    states_created: int = 0
    labels_created: int = 0
    cycles_created: int = 0
    modules_created: int = 0
    comments_imported: int = 0
    links_imported: int = 0
    relations_imported: int = 0
    dangling_relations: List[str] = []
    parents_linked: int = 0
    parents_missing: List[str] = []
    people_matched: int = 0
    people_unmatched: List[str] = []
    warnings: List[str] = []
