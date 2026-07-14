"""
Plane export importer for the Prosjekter feature.

Takes the parsed JSON array of a Plane work-item export
(``PlaneWorkItemIn`` rows) and syncs it into the local project tables.
Idempotent by value: re-importing the same file is a no-op-equivalent
(item scalars overwritten with identical values, child collections
replaced wholesale), and re-importing an updated export acts as a sync.

IMPORTANT — transaction boundary: this service owns a SINGLE transaction
(one ``db.commit()`` at the very end, ``db.flush()`` between passes). It
must NOT call the committing ``ProjectService.create_project`` /
``create_work_item`` methods: they commit mid-import and seed the
Norwegian default states. ORM objects are constructed directly instead,
and import-created projects are seeded with the Plane-standard English
states (``DEFAULT_STATES_PLANE``) so get-or-create by state name hits
without duplicates.

Error policy: malformed single values (bad date, unknown priority,
ambiguous person name) degrade to warnings on the result; only
structurally hopeless input fails the request (the router rolls back and
returns HTTP 400).
"""
import logging
import unicodedata
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import Admin
from app.models.member import Member
from app.models.project import (
    DEFAULT_STATES_PLANE,
    PLANE_STATE_GROUP_MAP,
    RELATION_DIRECTIONS,
    RELATION_TYPES,
    WORK_ITEM_PRIORITIES,
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
    work_item_cycles,
    work_item_labels,
    work_item_modules,
)
from app.schemas.project import PlaneImportResult, PlaneWorkItemIn

logger = logging.getLogger(__name__)


class PlaneImportError(ValueError):
    """Raised when an import is structurally invalid (maps to HTTP 400)."""


# Rotating palette for imported labels (Plane exports carry no colors).
_LABEL_PALETTE = (
    "#3B82F6", "#22C55E", "#F59E0B", "#EF4444", "#8B5CF6",
    "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16",
)
# Color per state group for states created outside the standard five.
_GROUP_COLORS = {group: color for _, group, color, _ in DEFAULT_STATES_PLANE}

# Plane system users that must never be fuzzy-matched to a real person.
_MATCH_SKIP_NAMES = {"plane"}
# Link an FK only when the best fuzzy score reaches this threshold AND no
# runner-up candidate scores within the ambiguity margin of it.
_FUZZY_LINK_THRESHOLD = 90.0
_FUZZY_AMBIGUITY_MARGIN = 5.0


# ---- lenient parsing helpers -------------------------------------------------

def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse Plane timestamps to naive UTC.

    Handles both item timestamps (ISO-8601 with ``Z``, e.g.
    ``2026-06-03T04:59:30.697578Z``) and comment timestamps
    (``2026-06-09 15:16:56``). Returns None on blank/unparseable input.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _parse_date(value: Optional[str]) -> Optional[date]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


# ---- fuzzy person matching ----------------------------------------------------
# Mirrors archer_matching_service.py, but uses token_set_ratio so
# "Paal Messenlien Messenlien" (duplicated token) still hits
# "Paal Messenlien" at 100 and "gunnar huuse" hits "Gunnar Huuse".

def _normalize_name(name: str) -> str:
    """Normalize name for comparison: lowercase, strip accents, trim."""
    name = name.lower().strip()
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _name_similarity(n1: str, n2: str) -> float:
    """Similarity score (0-100) between two already-normalized names."""
    try:
        from rapidfuzz import fuzz
        return fuzz.token_set_ratio(n1, n2)
    except ImportError:
        if n1 == n2:
            return 100.0
        words1, words2 = set(n1.split()), set(n2.split())
        if not words1 or not words2:
            return 0.0
        return (len(words1 & words2) / max(len(words1), len(words2))) * 100


class _PersonDirectory:
    """Resolves Plane display names to admin/member rows via fuzzy matching.

    A name may match a Spond member, an admin, both, or neither; the
    ambiguity guard is applied per pool. Results are memoized — the same
    display name repeats dozens of times in an export.
    """

    def __init__(
        self,
        admins: List[Tuple[str, int]],
        members: List[Tuple[str, int]],
    ) -> None:
        self._admins = admins    # [(normalized_name, admin_id)]
        self._members = members  # [(normalized_name, member_id)]
        self._memo: Dict[str, Tuple[Optional[int], Optional[int], Optional[int], List[str]]] = {}

    @staticmethod
    def _best(
        norm: str, candidates: List[Tuple[str, int]]
    ) -> Tuple[Optional[int], Optional[float], bool]:
        """Return (candidate_id, score, ambiguous) for the best unique match."""
        best_id: Optional[int] = None
        best = 0.0
        runner_up = 0.0
        for cand_norm, cand_id in candidates:
            score = _name_similarity(norm, cand_norm)
            if score > best:
                runner_up = best
                best = score
                best_id = cand_id
            elif score > runner_up:
                runner_up = score
        if best_id is None or best < _FUZZY_LINK_THRESHOLD:
            return None, None, False
        if runner_up >= best - _FUZZY_AMBIGUITY_MARGIN:
            # Not unique at the top — e.g. "Laura" token-set-matches every
            # member whose name contains "Laura". Refuse to link.
            return None, best, True
        return best_id, best, False

    def resolve(
        self, name: Optional[str]
    ) -> Tuple[Optional[int], Optional[int], Optional[int], List[str]]:
        """→ (member_id, admin_id, match_confidence, warnings)."""
        key = (name or "").strip()
        if not key or key.lower() in _MATCH_SKIP_NAMES:
            return None, None, None, []
        if key in self._memo:
            return self._memo[key]

        norm = _normalize_name(key)
        warnings: List[str] = []
        member_id, member_score, member_ambiguous = self._best(norm, self._members)
        admin_id, admin_score, admin_ambiguous = self._best(norm, self._admins)
        if member_ambiguous or admin_ambiguous:
            warnings.append(
                f"Flertydig navnetreff for «{key}» — ikke koblet automatisk"
            )

        confidence: Optional[int] = None
        linked_scores = [
            score
            for score, linked_id in ((member_score, member_id), (admin_score, admin_id))
            if linked_id is not None and score is not None
        ]
        if linked_scores:
            confidence = int(round(max(linked_scores)))

        result = (member_id, admin_id, confidence, warnings)
        self._memo[key] = result
        return result


async def _build_directory(db: AsyncSession) -> _PersonDirectory:
    admin_rows = (await db.execute(
        select(Admin.id, Admin.full_name, Admin.email)
    )).all()
    admins = [
        (_normalize_name(r.full_name), r.id)
        for r in admin_rows
        if (r.full_name or "").strip()
    ]
    member_rows = (await db.execute(
        select(Member.id, Member.first_name, Member.last_name)
    )).all()
    members = [
        (_normalize_name(f"{r.first_name or ''} {r.last_name or ''}".strip()), r.id)
        for r in member_rows
        if (r.first_name or r.last_name)
    ]
    return _PersonDirectory(admins, members)


class PlaneImportService:

    @staticmethod
    async def import_items(
        db: AsyncSession, items: List[PlaneWorkItemIn], imported_by: Admin
    ) -> PlaneImportResult:
        if not items:
            raise PlaneImportError("Ugyldig Plane-eksport: ingen saker i filen")

        result = PlaneImportResult()
        directory = await _build_directory(db)
        unmatched_names: set[str] = set()

        def warn(message: str) -> None:
            if message not in result.warnings:
                result.warnings.append(message)

        def resolve(name: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[int]]:
            member_id, admin_id, confidence, warnings = directory.resolve(name)
            for w in warnings:
                warn(w)
            return member_id, admin_id, confidence

        # Group items by project, preserving file order.
        groups: Dict[str, List[PlaneWorkItemIn]] = {}
        for payload in items:
            groups.setdefault(payload.project_identifier.strip(), []).append(payload)

        # ---- Pass 1: projects, dimensions, item scalars ------------------
        # processed: (item, payload, label_objs, cycle_objs, module_objs, ident_str)
        processed: List[tuple] = []
        updated_ids: List[int] = []

        for project_identifier, group in groups.items():
            project = (await db.execute(
                select(Project).where(Project.identifier == project_identifier)
            )).scalar_one_or_none()
            if project is None:
                project = Project(
                    name=group[0].project_name[:255],
                    identifier=project_identifier[:12],
                    last_sequence_id=0,
                    created_by_id=imported_by.id,
                    created_by_name=imported_by.full_name or imported_by.email,
                )
                db.add(project)
                await db.flush()
                for name, state_group, color, position in DEFAULT_STATES_PLANE:
                    db.add(ProjectState(
                        project_id=project.id,
                        name=name,
                        state_group=state_group,
                        color=color,
                        position=position,
                        is_default=(state_group == "unstarted"),
                    ))
                    result.states_created += 1
                await db.flush()
                result.projects_created.append(project_identifier)
            else:
                result.projects_updated.append(project_identifier)

            # Per-project name-keyed caches (case-sensitive, as Plane exports them).
            states = {s.name: s for s in (await db.execute(
                select(ProjectState).where(ProjectState.project_id == project.id)
            )).scalars()}
            labels = {l.name: l for l in (await db.execute(
                select(ProjectLabel).where(ProjectLabel.project_id == project.id)
            )).scalars()}
            cycles = {c.name: c for c in (await db.execute(
                select(ProjectCycle).where(ProjectCycle.project_id == project.id)
            )).scalars()}
            modules = {m.name: m for m in (await db.execute(
                select(ProjectModule).where(ProjectModule.project_id == project.id)
            )).scalars()}
            existing_items = {w.sequence_id: w for w in (await db.execute(
                select(WorkItem).where(WorkItem.project_id == project.id)
            )).scalars()}
            next_position = max((s.position for s in states.values()), default=-1) + 1

            seen_sequences: set[int] = set()
            for payload in group:
                ident_str = f"{project_identifier}-{payload.sequence_id}"
                if payload.sequence_id in seen_sequences:
                    warn(f"Duplisert sekvensnummer {ident_str} i filen — hoppet over")
                    continue
                seen_sequences.add(payload.sequence_id)

                # State get-or-create by name; unknown names get a group from
                # PLANE_STATE_GROUP_MAP, the next position and the group color.
                state: Optional[ProjectState] = None
                state_name = (payload.state_name or "").strip()[:100]
                if state_name:
                    state = states.get(state_name)
                    if state is None:
                        state_group = PLANE_STATE_GROUP_MAP.get(
                            state_name.lower(), "unstarted"
                        )
                        state = ProjectState(
                            project_id=project.id,
                            name=state_name,
                            state_group=state_group,
                            color=_GROUP_COLORS.get(state_group, "#9CA3AF"),
                            position=next_position,
                        )
                        next_position += 1
                        db.add(state)
                        await db.flush()
                        states[state_name] = state
                        result.states_created += 1

                label_objs: List[ProjectLabel] = []
                for raw in dict.fromkeys((n or "").strip()[:100] for n in payload.labels):
                    if not raw:
                        continue
                    label = labels.get(raw)
                    if label is None:
                        label = ProjectLabel(
                            project_id=project.id,
                            name=raw,
                            color=_LABEL_PALETTE[len(labels) % len(_LABEL_PALETTE)],
                        )
                        db.add(label)
                        labels[raw] = label
                        result.labels_created += 1
                    label_objs.append(label)

                cycle_objs: List[ProjectCycle] = []
                for raw in dict.fromkeys((n or "").strip()[:255] for n in payload.cycles):
                    if not raw:
                        continue
                    cycle = cycles.get(raw)
                    if cycle is None:
                        cycle = ProjectCycle(project_id=project.id, name=raw)
                        db.add(cycle)
                        cycles[raw] = cycle
                        result.cycles_created += 1
                    cycle_objs.append(cycle)

                module_objs: List[ProjectModule] = []
                for raw in dict.fromkeys((n or "").strip()[:255] for n in payload.modules):
                    if not raw:
                        continue
                    module = modules.get(raw)
                    if module is None:
                        module = ProjectModule(project_id=project.id, name=raw)
                        db.add(module)
                        modules[raw] = module
                        result.modules_created += 1
                    module_objs.append(module)

                priority = payload.priority
                if priority not in WORK_ITEM_PRIORITIES:
                    warn(f"Ukjent prioritet «{priority}» på {ident_str} — satt til 'none'")
                    priority = "none"

                # Upsert on (project_id, sequence_id) — the idempotency key.
                item = existing_items.get(payload.sequence_id)
                if item is None:
                    item = WorkItem(
                        project_id=project.id,
                        sequence_id=payload.sequence_id,
                        name=payload.name[:500],
                        sort_order=payload.sequence_id * 1000.0,
                    )
                    db.add(item)
                    existing_items[payload.sequence_id] = item
                    result.items_created += 1
                else:
                    updated_ids.append(item.id)
                    result.items_updated += 1

                item.name = payload.name[:500]
                item.state_id = state.id if state else None
                item.priority = priority
                item.is_draft = bool(payload.is_draft)
                item.estimate = (payload.estimate or "").strip() or None
                item.created_by_name = (payload.created_by_name or "").strip()[:255] or None
                _member_id, creator_admin_id, _conf = resolve(payload.created_by_name)
                item.created_by_id = creator_admin_id

                item.start_date = _parse_date(payload.start_date)
                if payload.start_date and payload.start_date.strip() and item.start_date is None:
                    warn(f"Kunne ikke tolke startdato «{payload.start_date}» på {ident_str}")
                item.target_date = _parse_date(payload.target_date)
                if payload.target_date and payload.target_date.strip() and item.target_date is None:
                    warn(f"Kunne ikke tolke frist «{payload.target_date}» på {ident_str}")
                item.completed_at = _parse_dt(payload.completed_at)
                if payload.completed_at and payload.completed_at.strip() and item.completed_at is None:
                    warn(f"Kunne ikke tolke completed_at «{payload.completed_at}» på {ident_str}")
                item.archived_at = _parse_dt(payload.archived_at)
                if payload.archived_at and payload.archived_at.strip() and item.archived_at is None:
                    warn(f"Kunne ikke tolke archived_at «{payload.archived_at}» på {ident_str}")

                # created_at/updated_at are NOT NULL — assign ONLY when parsing
                # succeeds; on failure new rows fall back to server_default and
                # updated rows keep their current value. Never assign None.
                created_at = _parse_dt(payload.created_at)
                if created_at is not None:
                    item.created_at = created_at
                elif payload.created_at and payload.created_at.strip():
                    warn(f"Kunne ikke tolke created_at «{payload.created_at}» på {ident_str}")
                updated_at = _parse_dt(payload.updated_at)
                if updated_at is not None:
                    item.updated_at = updated_at
                elif payload.updated_at and payload.updated_at.strip():
                    warn(f"Kunne ikke tolke updated_at «{payload.updated_at}» på {ident_str}")

                processed.append(
                    (item, payload, label_objs, cycle_objs, module_objs, ident_str)
                )

            # Guarantees correct next-sequence continuation even when the
            # export has gaps (e.g. 18 items, max sequence 19 → next is 20).
            project.last_sequence_id = max(
                project.last_sequence_id or 0,
                max(p.sequence_id for p in group),
            )

        await db.flush()

        # ---- Pass 1b: replace children of updated items wholesale --------
        # Bulk Core deletes + flush BEFORE re-adding: SQLAlchemy flushes
        # INSERTs before DELETEs on the same table, so ORM collection
        # replacement would collide with the unique constraints on re-import.
        if updated_ids:
            for model in (WorkItemPerson, WorkItemComment, WorkItemLink, WorkItemRelation):
                await db.execute(
                    delete(model).where(model.work_item_id.in_(updated_ids))
                )
            for table in (work_item_labels, work_item_cycles, work_item_modules):
                await db.execute(
                    delete(table).where(table.c.work_item_id.in_(updated_ids))
                )
            await db.flush()

        # ---- Pass 1c: re-add child rows from the file ---------------------
        label_rows: List[dict] = []
        cycle_rows: List[dict] = []
        module_rows: List[dict] = []
        for item, payload, label_objs, cycle_objs, module_objs, ident_str in processed:
            for kind, names in (
                ("assignee", payload.assignees),
                ("subscriber", payload.subscribers),
            ):
                seen: set[str] = set()
                for raw in names:
                    display_name = (raw or "").strip()[:255]
                    if not display_name or display_name.lower() in seen:
                        continue
                    seen.add(display_name.lower())
                    member_id, admin_id, confidence = resolve(display_name)
                    db.add(WorkItemPerson(
                        work_item_id=item.id,
                        kind=kind,
                        display_name=display_name,
                        member_id=member_id,
                        admin_id=admin_id,
                        match_confidence=confidence,
                    ))
                    if member_id is not None or admin_id is not None:
                        result.people_matched += 1
                    elif display_name.lower() not in _MATCH_SKIP_NAMES:
                        unmatched_names.add(display_name)

            for comment_in in payload.comments:
                _member_id, author_admin_id, _conf = resolve(comment_in.created_by)
                comment = WorkItemComment(
                    work_item_id=item.id,
                    body=comment_in.comment,
                    created_by_id=author_admin_id,
                    created_by_name=(comment_in.created_by or "").strip()[:255] or None,
                )
                # NOT NULL with server_default — assign only when parseable.
                comment_created_at = _parse_dt(comment_in.created_at)
                if comment_created_at is not None:
                    comment.created_at = comment_created_at
                elif comment_in.created_at and comment_in.created_at.strip():
                    warn(
                        f"Kunne ikke tolke kommentar-tidsstempel "
                        f"«{comment_in.created_at}» på {ident_str}"
                    )
                db.add(comment)
                result.comments_imported += 1

            for link_in in payload.links:
                url = (link_in.url or "").strip()
                if not url:
                    continue
                db.add(WorkItemLink(
                    work_item_id=item.id,
                    url=url,
                    title=(link_in.title or "").strip()[:500] or None,
                ))
                result.links_imported += 1

            label_rows.extend(
                {"work_item_id": item.id, "label_id": label.id} for label in label_objs
            )
            cycle_rows.extend(
                {"work_item_id": item.id, "cycle_id": cycle.id} for cycle in cycle_objs
            )
            module_rows.extend(
                {"work_item_id": item.id, "module_id": module.id} for module in module_objs
            )

        # Association rows via Core inserts (updated items were bulk-cleared
        # in pass 1b; created items have none yet).
        await db.flush()
        if label_rows:
            await db.execute(work_item_labels.insert(), label_rows)
        if cycle_rows:
            await db.execute(work_item_cycles.insert(), cycle_rows)
        if module_rows:
            await db.execute(work_item_modules.insert(), module_rows)

        # ---- Pass 2: parents + relations ----------------------------------
        # id_map spans ALL work items in the DB, not just this file —
        # parents/relations may target previously imported projects.
        rows = (await db.execute(
            select(WorkItem.id, WorkItem.sequence_id, Project.identifier)
            .join(Project, WorkItem.project_id == Project.id)
        )).all()
        id_map: Dict[str, int] = {
            f"{r.identifier}-{r.sequence_id}": r.id for r in rows
        }

        for item, payload, _labels, _cycles, _modules, ident_str in processed:
            # Assign unconditionally so a parent removed in a newer export is
            # cleared on re-import (sync semantics).
            parent_identifier = (payload.parent or "").strip()
            if parent_identifier:
                parent_db_id = id_map.get(parent_identifier)
                if parent_db_id is None:
                    if parent_identifier not in result.parents_missing:
                        result.parents_missing.append(parent_identifier)
                    item.parent_id = None
                elif parent_db_id == item.id:
                    warn(f"{ident_str} kan ikke være sin egen overordnede — hoppet over")
                    item.parent_id = None
                else:
                    item.parent_id = parent_db_id
                    result.parents_linked += 1
            else:
                item.parent_id = None

            seen_relations: set[tuple] = set()
            for relation_in in payload.relations:
                issue = (relation_in.issue or "").strip()
                if not issue:
                    continue
                relation_type = relation_in.type
                if relation_type not in RELATION_TYPES:
                    warn(
                        f"Ukjent relasjonstype «{relation_type}» på {ident_str} "
                        f"— satt til 'relates_to'"
                    )
                    relation_type = "relates_to"
                direction = relation_in.direction
                if direction not in RELATION_DIRECTIONS:
                    warn(
                        f"Ukjent relasjonsretning «{direction}» på {ident_str} "
                        f"— satt til 'outgoing'"
                    )
                    direction = "outgoing"
                key = (relation_type, direction, issue)
                if key in seen_relations:
                    continue
                seen_relations.add(key)
                related_db_id = id_map.get(issue)
                db.add(WorkItemRelation(
                    work_item_id=item.id,
                    relation_type=relation_type,
                    direction=direction,
                    related_identifier=issue[:32],
                    related_work_item_id=related_db_id,
                ))
                result.relations_imported += 1
                if related_db_id is None and issue not in result.dangling_relations:
                    result.dangling_relations.append(issue)

        await db.flush()

        # Backfill: relation rows from earlier imports that dangled on an
        # identifier this import just created now get their FK resolved.
        dangling_identifiers = (await db.execute(
            select(WorkItemRelation.related_identifier)
            .where(WorkItemRelation.related_work_item_id.is_(None))
            .distinct()
        )).scalars().all()
        for identifier in dangling_identifiers:
            target_id = id_map.get(identifier)
            if target_id is not None:
                await db.execute(
                    update(WorkItemRelation)
                    .where(
                        WorkItemRelation.related_work_item_id.is_(None),
                        WorkItemRelation.related_identifier == identifier,
                    )
                    .values(related_work_item_id=target_id)
                )

        result.people_unmatched = sorted(unmatched_names)
        await db.commit()
        logger.info(
            "Plane import: %d created, %d updated across %d project(s); "
            "%d dangling relation target(s), %d warning(s)",
            result.items_created, result.items_updated, len(groups),
            len(result.dangling_relations), len(result.warnings),
        )
        return result
