"""
Work items (saker) for the Prosjekter feature — the issue/task rows of a
project, plus their children: people (assignees/subscribers), comments,
links and relations, and the association tables tying items to labels,
cycles and modules.

Priority / relation vocabularies are Plane-compatible English tokens
(see ``app.models.project``); the frontend maps them to Norwegian labels.

NOTE for the Plane importer: ``created_at``/``updated_at`` come from
TimestampMixin with server defaults — assign them explicitly after
construction to preserve history from an export (an assigned attribute
wins over server_default/onupdate). Never assign ``None`` to them.
"""
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import (
    String, Text, Boolean, Date, DateTime, Float, Integer, ForeignKey,
    CheckConstraint, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import (
        Project, ProjectCycle, ProjectLabel, ProjectModule, ProjectState,
    )

# Association tables (composite PK, CASCADE both ways).
work_item_labels = sa.Table(
    "work_item_labels",
    Base.metadata,
    sa.Column(
        "work_item_id",
        sa.ForeignKey("work_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "label_id",
        sa.ForeignKey("project_labels.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

work_item_cycles = sa.Table(
    "work_item_cycles",
    Base.metadata,
    sa.Column(
        "work_item_id",
        sa.ForeignKey("work_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "cycle_id",
        sa.ForeignKey("project_cycles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

work_item_modules = sa.Table(
    "work_item_modules",
    Base.metadata,
    sa.Column(
        "work_item_id",
        sa.ForeignKey("work_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "module_id",
        sa.ForeignKey("project_modules.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class WorkItem(Base, TimestampMixin):
    __tablename__ = "work_items"
    __table_args__ = (
        # The idempotency key for Plane imports: identifier = "{IDENT}-{seq}".
        UniqueConstraint("project_id", "sequence_id", name="uq_work_items_project_seq"),
        CheckConstraint(
            "priority IN ('none','low','medium','high','urgent')",
            name="ck_work_items_priority",
        ),
        Index("ix_work_items_project_id", "project_id"),
        Index("ix_work_items_state_id", "state_id"),
        Index("ix_work_items_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    # Per-project number; identifier is composed as
    # f"{project.identifier}-{sequence_id}" in routers/services (never
    # stored — avoids lazy-loading the project in async contexts).
    sequence_id: Mapped[int] = mapped_column(Integer, nullable=False)

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    # Not present in Plane exports; UI-editable.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    state_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("project_states.id", ondelete="SET NULL"), nullable=True
    )
    priority: Mapped[str] = mapped_column(
        String(8), nullable=False, default="none", server_default="none"
    )
    # Self-reference; deleting a parent orphans (not deletes) sub-items.
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )

    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Set when moved to a completed-group state; cleared when moved out.
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Free-text estimate; import normalizes "" → NULL.
    estimate: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_draft: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    # Manual ordering within a board column (midpoint insertion).
    sort_order: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, server_default="0"
    )

    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    # Display-name fallback (import: "Laura", "Plane", ...).
    created_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    project: Mapped["Project"] = relationship(back_populates="work_items")
    state: Mapped[Optional["ProjectState"]] = relationship()
    parent: Mapped[Optional["WorkItem"]] = relationship(
        remote_side="WorkItem.id", back_populates="children"
    )
    children: Mapped[list["WorkItem"]] = relationship(
        back_populates="parent", order_by="WorkItem.sequence_id"
    )
    labels: Mapped[list["ProjectLabel"]] = relationship(
        secondary=work_item_labels, order_by="ProjectLabel.name"
    )
    cycles: Mapped[list["ProjectCycle"]] = relationship(
        secondary=work_item_cycles, order_by="ProjectCycle.name"
    )
    modules: Mapped[list["ProjectModule"]] = relationship(
        secondary=work_item_modules, order_by="ProjectModule.name"
    )
    people: Mapped[list["WorkItemPerson"]] = relationship(
        back_populates="work_item",
        cascade="all, delete-orphan",
        order_by="WorkItemPerson.id",
    )
    comments: Mapped[list["WorkItemComment"]] = relationship(
        back_populates="work_item",
        cascade="all, delete-orphan",
        order_by="WorkItemComment.created_at",
    )
    links: Mapped[list["WorkItemLink"]] = relationship(
        back_populates="work_item",
        cascade="all, delete-orphan",
        order_by="WorkItemLink.id",
    )
    relations: Mapped[list["WorkItemRelation"]] = relationship(
        back_populates="work_item",
        cascade="all, delete-orphan",
        foreign_keys="WorkItemRelation.work_item_id",
        order_by="WorkItemRelation.id",
    )

    def __repr__(self) -> str:
        return (
            f"<WorkItem id={self.id} project_id={self.project_id} "
            f"seq={self.sequence_id} name={self.name!r}>"
        )


class WorkItemPerson(Base):
    """
    One row per (work item, kind, person) — kind is assignee or subscriber.

    ``display_name`` is the source of truth (Plane exports only carry free
    text names); ``member_id``/``admin_id`` are optional fuzzy-matched
    references — a name may match a Spond member, an admin, both, or
    neither (follows the MemberAlias/UnmatchedArcher precedent).
    """

    __tablename__ = "work_item_people"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('assignee','subscriber')", name="ck_work_item_people_kind"
        ),
        # Dedupes the duplicate assignee entries present in Plane exports.
        UniqueConstraint(
            "work_item_id", "kind", "display_name",
            name="uq_work_item_people_item_kind_name",
        ),
        Index("ix_work_item_people_work_item_id", "work_item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    work_item_id: Mapped[int] = mapped_column(
        ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Fuzzy-matched Spond member / admin (either, both, or neither).
    member_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("members.id", ondelete="SET NULL"), nullable=True
    )
    admin_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    # rapidfuzz score at match time (audit).
    match_confidence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    work_item: Mapped["WorkItem"] = relationship(back_populates="people")

    def __repr__(self) -> str:
        return (
            f"<WorkItemPerson id={self.id} work_item_id={self.work_item_id} "
            f"kind={self.kind} name={self.display_name!r}>"
        )


class WorkItemComment(Base):
    __tablename__ = "work_item_comments"
    __table_args__ = (
        Index("ix_work_item_comments_work_item_id", "work_item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    work_item_id: Mapped[int] = mapped_column(
        ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )
    created_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Importer assigns explicitly (when parseable) to preserve history.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    work_item: Mapped["WorkItem"] = relationship(back_populates="comments")

    def __repr__(self) -> str:
        return f"<WorkItemComment id={self.id} work_item_id={self.work_item_id}>"


class WorkItemLink(Base):
    __tablename__ = "work_item_links"
    __table_args__ = (
        Index("ix_work_item_links_work_item_id", "work_item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    work_item_id: Mapped[int] = mapped_column(
        ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    work_item: Mapped["WorkItem"] = relationship(back_populates="links")

    def __repr__(self) -> str:
        return f"<WorkItemLink id={self.id} work_item_id={self.work_item_id}>"


class WorkItemRelation(Base):
    """
    A relation from one work item to another (possibly external) item.

    The raw target identifier string (e.g. "SOMEJUBILE-20") is always
    stored, plus a resolvable FK when the target exists in the DB (any
    project). Direction is kept verbatim from the Plane export — lossless,
    and tolerant of dangling references to projects never imported.
    """

    __tablename__ = "work_item_relations"
    __table_args__ = (
        CheckConstraint(
            "relation_type IN ('relates_to','blocks','blocked_by','duplicate')",
            name="ck_work_item_relations_type",
        ),
        CheckConstraint(
            "direction IN ('outgoing','incoming')",
            name="ck_work_item_relations_direction",
        ),
        # Re-import idempotency key.
        UniqueConstraint(
            "work_item_id", "relation_type", "direction", "related_identifier",
            name="uq_work_item_relations_key",
        ),
        Index("ix_work_item_relations_work_item_id", "work_item_id"),
        Index("ix_work_item_relations_related_id", "related_work_item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Owning/source item.
    work_item_id: Mapped[int] = mapped_column(
        ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="relates_to", server_default="relates_to"
    )
    direction: Mapped[str] = mapped_column(
        String(8), nullable=False, default="outgoing", server_default="outgoing"
    )
    # e.g. "SOMEJUBILE-20" — kept even when unresolvable.
    related_identifier: Mapped[str] = mapped_column(String(32), nullable=False)
    # Resolved target; NULL = dangling reference.
    related_work_item_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("work_items.id", ondelete="SET NULL"), nullable=True
    )

    work_item: Mapped["WorkItem"] = relationship(
        back_populates="relations", foreign_keys=[work_item_id]
    )

    def __repr__(self) -> str:
        return (
            f"<WorkItemRelation id={self.id} work_item_id={self.work_item_id} "
            f"{self.relation_type} {self.direction} {self.related_identifier!r}>"
        )
