"""
Prosjekter (Plane-like project management) service — CRUD for projects,
board states, labels, cycles, modules and work items, plus comments,
links and relations.

Access policy is enforced at the router layer (which endpoint + role);
this service validates cross-entity rules (identifier uniqueness, parent
cycles, state ownership) and owns the ``completed_at`` semantics: a work
item gets ``completed_at`` when it moves into a ``completed``-group state
and loses it when it moves out.

All mutating methods commit internally and return a freshly loaded row
(``populate_existing``) — the Plane importer therefore does NOT use them
(see ``plane_import_service.py``, which owns a single transaction).
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, case, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin import Admin
from app.models.project import (
    DEFAULT_STATES_NO,
    Project,
    ProjectCycle,
    ProjectLabel,
    ProjectModule,
    ProjectState,
)
from app.models.work_item import (
    WorkItem,
    WorkItemComment,
    WorkItemLink,
    WorkItemPerson,
    WorkItemRelation,
)
from app.schemas.project import (
    CycleCreate,
    CycleUpdate,
    LabelCreate,
    LabelUpdate,
    ModuleCreate,
    ModuleUpdate,
    ProjectCreate,
    ProjectUpdate,
    RelationCreate,
    StateCreate,
    StateUpdate,
    WorkItemCreate,
    WorkItemUpdate,
)

logger = logging.getLogger(__name__)


class ProjectValidationError(ValueError):
    """Raised when a project/work-item mutation is invalid (maps to HTTP 400)."""


def _display_name(admin: Admin) -> str:
    return admin.full_name or admin.email


class ProjectService:
    # ---- projects -------------------------------------------------------

    @staticmethod
    async def create_project(
        db: AsyncSession, data: ProjectCreate, created_by: Admin
    ) -> Project:
        identifier = data.identifier.strip().upper()
        existing = (
            await db.execute(select(Project.id).where(Project.identifier == identifier))
        ).scalar_one_or_none()
        if existing:
            raise ProjectValidationError("Prosjekt-ID er allerede i bruk")

        project = Project(
            name=data.name,
            identifier=identifier,
            description=data.description,
            created_by_id=created_by.id,
            created_by_name=_display_name(created_by),
        )
        db.add(project)
        await db.flush()
        # Seed the Norwegian default state set; new items land in "Å gjøre".
        for name, group, color, position in DEFAULT_STATES_NO:
            db.add(ProjectState(
                project_id=project.id,
                name=name,
                state_group=group,
                color=color,
                position=position,
                is_default=(group == "unstarted"),
            ))
        await db.commit()
        return await ProjectService.get_by_id(db, project.id)

    @staticmethod
    async def get_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
            .options(
                selectinload(Project.states),
                selectinload(Project.labels),
                selectinload(Project.cycles),
                selectinload(Project.modules),
            )
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_identifier(db: AsyncSession, identifier: str) -> Optional[Project]:
        result = await db.execute(
            select(Project).where(Project.identifier == identifier.strip().upper())
            .options(
                selectinload(Project.states),
                selectinload(Project.labels),
                selectinload(Project.cycles),
                selectinload(Project.modules),
            )
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_projects(
        db: AsyncSession, include_archived: bool = False
    ) -> Tuple[List[Project], int]:
        q = select(Project)
        if not include_archived:
            q = q.where(Project.is_archived == False)  # noqa: E712
        q = q.order_by(Project.name)
        projects = list((await db.execute(q)).scalars().all())
        return projects, len(projects)

    @staticmethod
    async def project_item_counts(
        db: AsyncSession, project_ids: List[int]
    ) -> dict[int, Tuple[int, int]]:
        """One grouped query → {project_id: (total_items, completed_items)}."""
        if not project_ids:
            return {}
        rows = (await db.execute(
            select(
                WorkItem.project_id,
                func.count(WorkItem.id),
                func.sum(case((ProjectState.state_group == "completed", 1), else_=0)),
            )
            .outerjoin(ProjectState, WorkItem.state_id == ProjectState.id)
            .where(WorkItem.project_id.in_(project_ids))
            .group_by(WorkItem.project_id)
        )).all()
        return {r[0]: (r[1] or 0, int(r[2] or 0)) for r in rows}

    @staticmethod
    async def state_item_counts(db: AsyncSession, project_id: int) -> dict[int, int]:
        rows = (await db.execute(
            select(WorkItem.state_id, func.count(WorkItem.id))
            .where(WorkItem.project_id == project_id, WorkItem.state_id.isnot(None))
            .group_by(WorkItem.state_id)
        )).all()
        return {r[0]: r[1] for r in rows}

    @staticmethod
    async def update_project(
        db: AsyncSession, project: Project, data: ProjectUpdate
    ) -> Project:
        values = data.model_dump(exclude_unset=True)
        new_identifier = values.get("identifier")
        if new_identifier and new_identifier != project.identifier:
            existing = (await db.execute(
                select(Project.id).where(
                    Project.identifier == new_identifier, Project.id != project.id
                )
            )).scalar_one_or_none()
            if existing:
                raise ProjectValidationError("Prosjekt-ID er allerede i bruk")
        for field, value in values.items():
            setattr(project, field, value)
        project.updated_at = datetime.utcnow()
        await db.commit()
        return await ProjectService.get_by_id(db, project.id)

    @staticmethod
    async def delete_project(db: AsyncSession, project: Project) -> None:
        # Relations from other projects pointing at this project's items
        # keep their identifier string but lose the FK (consistent with
        # the dangling-reference design).
        item_ids = select(WorkItem.id).where(WorkItem.project_id == project.id)
        await db.execute(
            update(WorkItemRelation)
            .where(WorkItemRelation.related_work_item_id.in_(item_ids))
            .values(related_work_item_id=None)
        )
        await db.delete(project)
        await db.commit()

    # ---- states ----------------------------------------------------------

    @staticmethod
    async def get_state(db: AsyncSession, state_id: int) -> Optional[ProjectState]:
        return await db.get(ProjectState, state_id)

    @staticmethod
    async def _get_project_state(
        db: AsyncSession, project_id: int, state_id: int
    ) -> ProjectState:
        state = await db.get(ProjectState, state_id)
        if state is None or state.project_id != project_id:
            raise ProjectValidationError("Ugyldig status for dette prosjektet")
        return state

    @staticmethod
    async def create_state(
        db: AsyncSession, project: Project, data: StateCreate
    ) -> ProjectState:
        duplicate = (await db.execute(
            select(ProjectState.id).where(
                ProjectState.project_id == project.id, ProjectState.name == data.name
            )
        )).scalar_one_or_none()
        if duplicate:
            raise ProjectValidationError("En status med dette navnet finnes allerede")
        state = ProjectState(
            project_id=project.id,
            name=data.name,
            state_group=data.group,
            color=data.color,
            position=data.position,
        )
        db.add(state)
        await db.commit()
        await db.refresh(state)
        return state

    @staticmethod
    async def update_state(
        db: AsyncSession, state: ProjectState, data: StateUpdate
    ) -> ProjectState:
        values = data.model_dump(exclude_unset=True)
        new_name = values.get("name")
        if new_name and new_name != state.name:
            duplicate = (await db.execute(
                select(ProjectState.id).where(
                    ProjectState.project_id == state.project_id,
                    ProjectState.name == new_name,
                    ProjectState.id != state.id,
                )
            )).scalar_one_or_none()
            if duplicate:
                raise ProjectValidationError("En status med dette navnet finnes allerede")
        if "group" in values:
            state.state_group = values.pop("group")
        if values.pop("is_default", None):
            # Only one default state per project.
            await db.execute(
                update(ProjectState)
                .where(ProjectState.project_id == state.project_id)
                .values(is_default=False)
            )
            state.is_default = True
        for field, value in values.items():
            setattr(state, field, value)
        await db.commit()
        await db.refresh(state)
        return state

    @staticmethod
    async def delete_state(
        db: AsyncSession, state: ProjectState, move_to_state_id: Optional[int] = None
    ) -> None:
        item_ids = list((await db.execute(
            select(WorkItem.id).where(WorkItem.state_id == state.id)
        )).scalars().all())
        if item_ids:
            if move_to_state_id is None:
                raise ProjectValidationError(
                    "Statusen er i bruk — velg en status sakene skal flyttes til"
                )
            target = await ProjectService._get_project_state(
                db, state.project_id, move_to_state_id
            )
            if target.id == state.id:
                raise ProjectValidationError("Kan ikke flytte saker til statusen som slettes")
            values: dict = {"state_id": target.id}
            if target.state_group != "completed":
                values["completed_at"] = None
            await db.execute(
                update(WorkItem).where(WorkItem.id.in_(item_ids)).values(**values)
            )
            if target.state_group == "completed":
                await db.execute(
                    update(WorkItem)
                    .where(WorkItem.id.in_(item_ids), WorkItem.completed_at.is_(None))
                    .values(completed_at=datetime.utcnow())
                )
        await db.delete(state)
        await db.commit()

    # ---- labels / cycles / modules ---------------------------------------

    @staticmethod
    async def get_label(db: AsyncSession, label_id: int) -> Optional[ProjectLabel]:
        return await db.get(ProjectLabel, label_id)

    @staticmethod
    async def create_label(
        db: AsyncSession, project: Project, data: LabelCreate
    ) -> ProjectLabel:
        duplicate = (await db.execute(
            select(ProjectLabel.id).where(
                ProjectLabel.project_id == project.id, ProjectLabel.name == data.name
            )
        )).scalar_one_or_none()
        if duplicate:
            raise ProjectValidationError("En etikett med dette navnet finnes allerede")
        label = ProjectLabel(project_id=project.id, name=data.name, color=data.color)
        db.add(label)
        await db.commit()
        await db.refresh(label)
        return label

    @staticmethod
    async def update_label(
        db: AsyncSession, label: ProjectLabel, data: LabelUpdate
    ) -> ProjectLabel:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(label, field, value)
        await db.commit()
        await db.refresh(label)
        return label

    @staticmethod
    async def delete_label(db: AsyncSession, label: ProjectLabel) -> None:
        # Association rows are removed by FK CASCADE on the secondary table.
        await db.delete(label)
        await db.commit()

    @staticmethod
    async def get_cycle(db: AsyncSession, cycle_id: int) -> Optional[ProjectCycle]:
        return await db.get(ProjectCycle, cycle_id)

    @staticmethod
    async def create_cycle(
        db: AsyncSession, project: Project, data: CycleCreate
    ) -> ProjectCycle:
        duplicate = (await db.execute(
            select(ProjectCycle.id).where(
                ProjectCycle.project_id == project.id, ProjectCycle.name == data.name
            )
        )).scalar_one_or_none()
        if duplicate:
            raise ProjectValidationError("En syklus med dette navnet finnes allerede")
        cycle = ProjectCycle(
            project_id=project.id,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            description=data.description,
        )
        db.add(cycle)
        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def update_cycle(
        db: AsyncSession, cycle: ProjectCycle, data: CycleUpdate
    ) -> ProjectCycle:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cycle, field, value)
        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def delete_cycle(db: AsyncSession, cycle: ProjectCycle) -> None:
        await db.delete(cycle)
        await db.commit()

    @staticmethod
    async def get_module(db: AsyncSession, module_id: int) -> Optional[ProjectModule]:
        return await db.get(ProjectModule, module_id)

    @staticmethod
    async def create_module(
        db: AsyncSession, project: Project, data: ModuleCreate
    ) -> ProjectModule:
        duplicate = (await db.execute(
            select(ProjectModule.id).where(
                ProjectModule.project_id == project.id, ProjectModule.name == data.name
            )
        )).scalar_one_or_none()
        if duplicate:
            raise ProjectValidationError("En modul med dette navnet finnes allerede")
        module = ProjectModule(
            project_id=project.id, name=data.name, description=data.description
        )
        db.add(module)
        await db.commit()
        await db.refresh(module)
        return module

    @staticmethod
    async def update_module(
        db: AsyncSession, module: ProjectModule, data: ModuleUpdate
    ) -> ProjectModule:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(module, field, value)
        await db.commit()
        await db.refresh(module)
        return module

    @staticmethod
    async def delete_module(db: AsyncSession, module: ProjectModule) -> None:
        await db.delete(module)
        await db.commit()

    # ---- work items ------------------------------------------------------

    @staticmethod
    async def _fetch_owned(db: AsyncSession, model, ids: List[int], project_id: int):
        """Load label/cycle/module rows by id, silently dropping foreign ones."""
        if not ids:
            return []
        rows = (await db.execute(
            select(model).where(model.id.in_(ids), model.project_id == project_id)
        )).scalars().all()
        return list(rows)

    @staticmethod
    async def _validate_parent(
        db: AsyncSession, item_id: Optional[int], project_id: int, parent_id: int
    ) -> None:
        """Parent must exist in the same project and not create a cycle."""
        parent = await db.get(WorkItem, parent_id)
        if parent is None or parent.project_id != project_id:
            raise ProjectValidationError("Ugyldig overordnet sak")
        if item_id is None:
            return
        # Walk up from the proposed parent; hitting the item itself = cycle.
        seen: set[int] = set()
        current: Optional[WorkItem] = parent
        while current is not None:
            if current.id == item_id:
                raise ProjectValidationError("Ugyldig overordnet sak")
            if current.parent_id is None or current.id in seen:
                break
            seen.add(current.id)
            current = await db.get(WorkItem, current.parent_id)

    @staticmethod
    def _add_people(
        db: AsyncSession, work_item_id: int, kind: str, people: List[dict]
    ) -> None:
        seen: set[str] = set()
        for person in people:
            name = (person.get("display_name") or "").strip()
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            db.add(WorkItemPerson(
                work_item_id=work_item_id,
                kind=kind,
                display_name=name,
                member_id=person.get("member_id"),
                admin_id=person.get("admin_id"),
            ))

    @staticmethod
    async def create_work_item(
        db: AsyncSession, project: Project, data: WorkItemCreate, created_by: Admin
    ) -> WorkItem:
        # Lock the project row for the sequence bump (FOR UPDATE on PG;
        # SQLAlchemy's SQLite dialect ignores the clause).
        locked = (await db.execute(
            select(Project).where(Project.id == project.id).with_for_update()
        )).scalar_one()
        sequence_id = locked.last_sequence_id + 1
        locked.last_sequence_id = sequence_id

        state: Optional[ProjectState] = None
        if data.state_id is not None:
            state = await ProjectService._get_project_state(db, project.id, data.state_id)
        else:
            state = (await db.execute(
                select(ProjectState)
                .where(ProjectState.project_id == project.id)
                .order_by(ProjectState.is_default.desc(), ProjectState.position)
                .limit(1)
            )).scalar_one_or_none()

        if data.parent_id is not None:
            await ProjectService._validate_parent(db, None, project.id, data.parent_id)

        max_sort = (await db.execute(
            select(func.max(WorkItem.sort_order)).where(
                WorkItem.project_id == project.id,
                WorkItem.state_id == (state.id if state else None),
            )
        )).scalar()

        item = WorkItem(
            project_id=project.id,
            sequence_id=sequence_id,
            name=data.name,
            description=data.description,
            state_id=state.id if state else None,
            priority=data.priority,
            parent_id=data.parent_id,
            start_date=data.start_date,
            target_date=data.target_date,
            estimate=(data.estimate or "").strip() or None,
            is_draft=data.is_draft,
            sort_order=(max_sort or 0.0) + 1000.0,
            created_by_id=created_by.id,
            created_by_name=_display_name(created_by),
            # Collections assigned while the object is still pending — after
            # flush the assignment would lazy-load (MissingGreenlet in async).
            labels=await ProjectService._fetch_owned(
                db, ProjectLabel, data.label_ids, project.id
            ),
            cycles=await ProjectService._fetch_owned(
                db, ProjectCycle, data.cycle_ids, project.id
            ),
            modules=await ProjectService._fetch_owned(
                db, ProjectModule, data.module_ids, project.id
            ),
        )
        if state and state.state_group == "completed":
            item.completed_at = datetime.utcnow()
        db.add(item)
        await db.flush()

        ProjectService._add_people(
            db, item.id, "assignee", [p.model_dump() for p in data.assignees]
        )
        ProjectService._add_people(
            db, item.id, "subscriber", [p.model_dump() for p in data.subscribers]
        )
        await db.commit()
        return await ProjectService.get_work_item(db, item.id)

    @staticmethod
    async def get_work_item(db: AsyncSession, item_id: int) -> Optional[WorkItem]:
        result = await db.execute(
            select(WorkItem).where(WorkItem.id == item_id)
            .options(
                selectinload(WorkItem.state),
                selectinload(WorkItem.labels),
                selectinload(WorkItem.cycles),
                selectinload(WorkItem.modules),
                selectinload(WorkItem.people),
                selectinload(WorkItem.links),
                selectinload(WorkItem.relations),
                selectinload(WorkItem.comments),
                selectinload(WorkItem.parent),
                selectinload(WorkItem.children).selectinload(WorkItem.state),
                selectinload(WorkItem.children).selectinload(WorkItem.people),
                selectinload(WorkItem.children).selectinload(WorkItem.labels),
            )
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _apply_item_filters(
        q,
        *,
        priority: Optional[str] = None,
        label_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        module_id: Optional[int] = None,
        assignee: Optional[str] = None,
        search: Optional[str] = None,
        include_completed: bool = True,
    ):
        if priority:
            q = q.where(WorkItem.priority == priority)
        if label_id is not None:
            q = q.where(WorkItem.labels.any(ProjectLabel.id == label_id))
        if cycle_id is not None:
            q = q.where(WorkItem.cycles.any(ProjectCycle.id == cycle_id))
        if module_id is not None:
            q = q.where(WorkItem.modules.any(ProjectModule.id == module_id))
        if assignee:
            q = q.where(WorkItem.people.any(and_(
                WorkItemPerson.kind == "assignee",
                WorkItemPerson.display_name.ilike(f"%{assignee}%"),
            )))
        if search:
            q = q.where(WorkItem.name.ilike(f"%{search}%"))
        if not include_completed:
            q = q.where(or_(
                WorkItem.state_id.is_(None),
                WorkItem.state.has(ProjectState.state_group != "completed"),
            ))
        return q

    @staticmethod
    async def list_work_items(
        db: AsyncSession,
        project_id: int,
        *,
        state_id: Optional[int] = None,
        priority: Optional[str] = None,
        label_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        module_id: Optional[int] = None,
        assignee: Optional[str] = None,
        search: Optional[str] = None,
        parent_id: Optional[int] = None,
        top_level_only: bool = False,
        include_completed: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[WorkItem], int]:
        q = select(WorkItem).where(WorkItem.project_id == project_id)
        if state_id is not None:
            q = q.where(WorkItem.state_id == state_id)
        if parent_id is not None:
            q = q.where(WorkItem.parent_id == parent_id)
        elif top_level_only:
            q = q.where(WorkItem.parent_id.is_(None))
        q = ProjectService._apply_item_filters(
            q,
            priority=priority, label_id=label_id, cycle_id=cycle_id,
            module_id=module_id, assignee=assignee, search=search,
            include_completed=include_completed,
        )
        total = (await db.execute(
            select(func.count()).select_from(q.subquery())
        )).scalar() or 0
        rows = (await db.execute(
            q.options(
                selectinload(WorkItem.state),
                selectinload(WorkItem.people),
                selectinload(WorkItem.labels),
            )
            .order_by(WorkItem.sequence_id.desc())
            .offset(skip).limit(limit)
        )).scalars().all()
        return list(rows), total

    @staticmethod
    async def board(
        db: AsyncSession,
        project_id: int,
        *,
        priority: Optional[str] = None,
        label_id: Optional[int] = None,
        cycle_id: Optional[int] = None,
        module_id: Optional[int] = None,
        assignee: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Tuple[ProjectState, List[WorkItem]]]:
        """One (state, items) pair per state, states ordered by position,
        items ordered by (sort_order, sequence_id)."""
        states = list((await db.execute(
            select(ProjectState)
            .where(ProjectState.project_id == project_id)
            .order_by(ProjectState.position, ProjectState.id)
        )).scalars().all())

        q = select(WorkItem).where(
            WorkItem.project_id == project_id, WorkItem.state_id.isnot(None)
        )
        q = ProjectService._apply_item_filters(
            q,
            priority=priority, label_id=label_id, cycle_id=cycle_id,
            module_id=module_id, assignee=assignee, search=search,
        )
        items = (await db.execute(
            q.options(
                selectinload(WorkItem.state),
                selectinload(WorkItem.people),
                selectinload(WorkItem.labels),
            )
            .order_by(WorkItem.sort_order, WorkItem.sequence_id)
        )).scalars().all()

        by_state: dict[int, List[WorkItem]] = {}
        for item in items:
            by_state.setdefault(item.state_id, []).append(item)
        return [(state, by_state.get(state.id, [])) for state in states]

    @staticmethod
    async def child_and_comment_counts(
        db: AsyncSession, item_ids: List[int]
    ) -> Tuple[dict[int, int], dict[int, int]]:
        """Two grouped queries → ({item_id: sub_item_count}, {item_id: comment_count})."""
        if not item_ids:
            return {}, {}
        sub_counts = dict((await db.execute(
            select(WorkItem.parent_id, func.count(WorkItem.id))
            .where(WorkItem.parent_id.in_(item_ids))
            .group_by(WorkItem.parent_id)
        )).all())
        comment_counts = dict((await db.execute(
            select(WorkItemComment.work_item_id, func.count(WorkItemComment.id))
            .where(WorkItemComment.work_item_id.in_(item_ids))
            .group_by(WorkItemComment.work_item_id)
        )).all())
        return sub_counts, comment_counts

    @staticmethod
    async def update_work_item(
        db: AsyncSession, item: WorkItem, data: WorkItemUpdate
    ) -> WorkItem:
        values = data.model_dump(exclude_unset=True)
        label_ids = values.pop("label_ids", None)
        cycle_ids = values.pop("cycle_ids", None)
        module_ids = values.pop("module_ids", None)
        assignees = values.pop("assignees", None)
        subscribers = values.pop("subscribers", None)

        if values.get("parent_id") is not None:
            await ProjectService._validate_parent(
                db, item.id, item.project_id, values["parent_id"]
            )
        if "state_id" in values:
            new_state_id = values["state_id"]
            if new_state_id is not None:
                state = await ProjectService._get_project_state(
                    db, item.project_id, new_state_id
                )
                if state.state_group == "completed":
                    if item.completed_at is None:
                        item.completed_at = datetime.utcnow()
                else:
                    item.completed_at = None
            else:
                item.completed_at = None
        if values.get("estimate") == "":
            values["estimate"] = None
        for field, value in values.items():
            setattr(item, field, value)

        if label_ids is not None:
            item.labels = await ProjectService._fetch_owned(
                db, ProjectLabel, label_ids, item.project_id
            )
        if cycle_ids is not None:
            item.cycles = await ProjectService._fetch_owned(
                db, ProjectCycle, cycle_ids, item.project_id
            )
        if module_ids is not None:
            item.modules = await ProjectService._fetch_owned(
                db, ProjectModule, module_ids, item.project_id
            )

        # People are replaced wholesale per kind: bulk Core delete + flush
        # first so re-inserted identical rows don't collide with the
        # (work_item_id, kind, display_name) unique constraint.
        for kind, people in (("assignee", assignees), ("subscriber", subscribers)):
            if people is None:
                continue
            await db.execute(delete(WorkItemPerson).where(
                WorkItemPerson.work_item_id == item.id, WorkItemPerson.kind == kind
            ))
            await db.flush()
            db.expire(item, ["people"])
            ProjectService._add_people(db, item.id, kind, people)

        item.updated_at = datetime.utcnow()
        await db.commit()
        return await ProjectService.get_work_item(db, item.id)

    @staticmethod
    async def delete_work_item(db: AsyncSession, item: WorkItem) -> None:
        # Children are orphaned (not deleted); relations pointing here keep
        # their identifier string and become dangling. Done explicitly so
        # behaviour doesn't depend on FK enforcement in the dev SQLite DB.
        await db.execute(
            update(WorkItem).where(WorkItem.parent_id == item.id).values(parent_id=None)
        )
        await db.execute(
            update(WorkItemRelation)
            .where(WorkItemRelation.related_work_item_id == item.id)
            .values(related_work_item_id=None)
        )
        await db.delete(item)
        await db.commit()

    # ---- comments --------------------------------------------------------

    @staticmethod
    async def get_comment(db: AsyncSession, comment_id: int) -> Optional[WorkItemComment]:
        return await db.get(WorkItemComment, comment_id)

    @staticmethod
    async def add_comment(
        db: AsyncSession, item: WorkItem, body: str, author: Admin
    ) -> WorkItemComment:
        comment = WorkItemComment(
            work_item_id=item.id,
            body=body,
            created_by_id=author.id,
            created_by_name=_display_name(author),
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def update_comment(
        db: AsyncSession, comment: WorkItemComment, body: str
    ) -> WorkItemComment:
        comment.body = body
        # No onupdate on this column — set manually.
        comment.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def delete_comment(db: AsyncSession, comment: WorkItemComment) -> None:
        await db.delete(comment)
        await db.commit()

    # ---- links -----------------------------------------------------------

    @staticmethod
    async def get_link(db: AsyncSession, link_id: int) -> Optional[WorkItemLink]:
        return await db.get(WorkItemLink, link_id)

    @staticmethod
    async def add_link(
        db: AsyncSession, item: WorkItem, url: str, title: Optional[str]
    ) -> WorkItemLink:
        link = WorkItemLink(work_item_id=item.id, url=url.strip(), title=title or None)
        db.add(link)
        await db.commit()
        await db.refresh(link)
        return link

    @staticmethod
    async def delete_link(db: AsyncSession, link: WorkItemLink) -> None:
        await db.delete(link)
        await db.commit()

    # ---- relations -------------------------------------------------------

    @staticmethod
    async def get_relation(
        db: AsyncSession, relation_id: int
    ) -> Optional[WorkItemRelation]:
        return await db.get(WorkItemRelation, relation_id)

    @staticmethod
    async def add_relation(
        db: AsyncSession, item: WorkItem, data: RelationCreate
    ) -> WorkItemRelation:
        related_id: Optional[int] = None
        related_identifier: str

        if data.related_work_item_id is not None:
            row = (await db.execute(
                select(WorkItem.id, WorkItem.sequence_id, Project.identifier)
                .join(Project, WorkItem.project_id == Project.id)
                .where(WorkItem.id == data.related_work_item_id)
            )).first()
            if row is None:
                raise ProjectValidationError("Relatert sak ikke funnet")
            related_id = row.id
            related_identifier = f"{row.identifier}-{row.sequence_id}"
        else:
            related_identifier = (data.related_identifier or "").strip().upper()
            if not related_identifier:
                raise ProjectValidationError("Ugyldig relasjonsmål")
            # Resolve "PREFIX-N" when the target exists locally; otherwise
            # store the identifier alone (dangling reference — allowed).
            prefix, _, num = related_identifier.rpartition("-")
            if prefix and num.isdigit():
                related_id = (await db.execute(
                    select(WorkItem.id)
                    .join(Project, WorkItem.project_id == Project.id)
                    .where(
                        Project.identifier == prefix,
                        WorkItem.sequence_id == int(num),
                    )
                )).scalar_one_or_none()

        duplicate = (await db.execute(
            select(WorkItemRelation.id).where(
                WorkItemRelation.work_item_id == item.id,
                WorkItemRelation.relation_type == data.relation_type,
                WorkItemRelation.direction == data.direction,
                WorkItemRelation.related_identifier == related_identifier,
            )
        )).scalar_one_or_none()
        if duplicate:
            raise ProjectValidationError("Relasjonen finnes allerede")

        relation = WorkItemRelation(
            work_item_id=item.id,
            relation_type=data.relation_type,
            direction=data.direction,
            related_identifier=related_identifier[:32],
            related_work_item_id=related_id,
        )
        db.add(relation)
        await db.commit()
        await db.refresh(relation)
        return relation

    @staticmethod
    async def delete_relation(db: AsyncSession, relation: WorkItemRelation) -> None:
        await db.delete(relation)
        await db.commit()
