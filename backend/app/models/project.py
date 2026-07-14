"""
Prosjekter — Plane-like project management (projects, states, labels,
cycles, modules).

A ``Project`` is the aggregate root: it owns its board states, labels,
cycles, modules and work items. Work items live in
``app.models.work_item``.

NOTE on vocabulary: state *group* and *priority* values are deliberately
kept Plane-compatible (English tokens: ``backlog``/``unstarted``/… and
``none``/``low``/…) so imports from Plane exports map losslessly. This is
a deliberate deviation from the Norwegian-vocab-in-DB convention used
elsewhere in the codebase — the frontend maps these tokens to Norwegian
labels. State *names* are free text (Norwegian for UI-created projects,
English Plane names for imported projects).
"""
from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String, Text, Boolean, Date, Integer, ForeignKey, CheckConstraint,
    Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.work_item import WorkItem

# Vocabularies (single source of truth — schemas build patterns from these).
STATE_GROUPS = ("backlog", "unstarted", "started", "completed", "cancelled")
WORK_ITEM_PRIORITIES = ("none", "low", "medium", "high", "urgent")
RELATION_TYPES = ("relates_to", "blocks", "blocked_by", "duplicate")
RELATION_DIRECTIONS = ("outgoing", "incoming")

# Default state set seeded on every project creation (name, group, color,
# position). UI-created projects get Norwegian names; the Plane importer
# instead seeds the five Plane-standard English names so that
# get-or-create by name hits directly without duplicates.
DEFAULT_STATES_NO = (
    ("Backlogg",  "backlog",   "#9CA3AF", 0),
    ("Å gjøre",   "unstarted", "#3B82F6", 1),
    ("Pågår",     "started",   "#F59E0B", 2),
    ("Fullført",  "completed", "#22C55E", 3),
    ("Avbrutt",   "cancelled", "#EF4444", 4),
)
DEFAULT_STATES_PLANE = (
    ("Backlog",     "backlog",   "#9CA3AF", 0),
    ("Todo",        "unstarted", "#3B82F6", 1),
    ("In Progress", "started",   "#F59E0B", 2),
    ("Done",        "completed", "#22C55E", 3),
    ("Cancelled",   "cancelled", "#EF4444", 4),
)
# Map used by the importer for unknown Plane state names → state group.
PLANE_STATE_GROUP_MAP = {
    "backlog": "backlog",
    "todo": "unstarted",
    "in progress": "started",
    "done": "completed",
    "cancelled": "cancelled",
}


class Project(Base, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_identifier", "identifier", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Uppercase short code, e.g. "STYRE". Work item identifiers are
    # composed as f"{identifier}-{sequence_id}".
    identifier: Mapped[str] = mapped_column(String(12), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Highest sequence number handed out so far; the next work item gets
    # last_sequence_id + 1. The Plane importer bumps this to
    # max(existing, max sequence in file) so numbering continues correctly.
    last_sequence_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Actor ref survives admin deletion (SET NULL); display-name fallback
    # covers imported projects whose creator has no admin account.
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    created_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    states: Mapped[list["ProjectState"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectState.position",
    )
    labels: Mapped[list["ProjectLabel"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectLabel.name",
    )
    cycles: Mapped[list["ProjectCycle"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectCycle.name",
    )
    modules: Mapped[list["ProjectModule"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectModule.name",
    )
    work_items: Mapped[list["WorkItem"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="WorkItem.sequence_id",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} identifier={self.identifier!r} name={self.name!r}>"


class ProjectState(Base):
    """A board column / workflow state within a project."""

    __tablename__ = "project_states"
    __table_args__ = (
        CheckConstraint(
            "state_group IN ('backlog','unstarted','started','completed','cancelled')",
            name="ck_project_states_group",
        ),
        UniqueConstraint("project_id", "name", name="uq_project_states_project_name"),
        Index("ix_project_states_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    # Free text — English from Plane import, Norwegian from the UI.
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # One of STATE_GROUPS. Named state_group (not "group") to avoid the SQL
    # reserved word; schemas expose it as ``group``. Drives board ordering
    # and completed_at semantics.
    state_group: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unstarted", server_default="unstarted"
    )
    color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#9CA3AF", server_default="#9CA3AF"
    )
    # Column order on the board.
    position: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # State assigned to new items when none is chosen.
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    project: Mapped["Project"] = relationship(back_populates="states")

    def __repr__(self) -> str:
        return (
            f"<ProjectState id={self.id} project_id={self.project_id} "
            f"name={self.name!r} group={self.state_group}>"
        )


class ProjectLabel(Base):
    __tablename__ = "project_labels"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_labels_project_name"),
        Index("ix_project_labels_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#6B7280", server_default="#6B7280"
    )

    project: Mapped["Project"] = relationship(back_populates="labels")

    def __repr__(self) -> str:
        return f"<ProjectLabel id={self.id} project_id={self.project_id} name={self.name!r}>"


class ProjectCycle(Base):
    __tablename__ = "project_cycles"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_cycles_project_name"),
        Index("ix_project_cycles_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="cycles")

    def __repr__(self) -> str:
        return f"<ProjectCycle id={self.id} project_id={self.project_id} name={self.name!r}>"


class ProjectModule(Base):
    __tablename__ = "project_modules"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_modules_project_name"),
        Index("ix_project_modules_project_id", "project_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="modules")

    def __repr__(self) -> str:
        return f"<ProjectModule id={self.id} project_id={self.project_id} name={self.name!r}>"
