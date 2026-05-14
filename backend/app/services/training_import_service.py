"""
Training-plan Excel importer (wave 2).

Reads a vaktliste .xlsx (Sheet1 = `Vakliste`, columns Navn | Initialer | Dato |
Vakttype), resolves initials → members (via `member_aliases` or fuzzy match on
`Member.first_name`), and upserts `training_shifts` rows keyed on
`(session_type_id, date)`.

Decisions:
- We deliberately avoid the `openpyxl` package — parsing the .xlsx is done with
  stdlib `zipfile` + `xml.etree.ElementTree`. The vaktliste sheet uses inline
  strings, which keeps the parser tiny.
- Unknown session-type names are auto-created with default start 18:00 / end
  20:00 and `location=None`. The resulting names are reported in
  `ImportReport.created_session_types` so the user can refine them in the UI.
- Rows whose `Vakttype` matches the external-competition shorthands
  (`Stevner skive`, `Stevner skog`) are skipped silently.
- Initials lookups are case-insensitive; on a successful fuzzy match (rapidfuzz
  WRatio >= 85 against `Navn`) a new MemberAlias row is created with
  `source='auto'`.
- Existing shifts that already have `status='published'` are NEVER repointed at
  a different leader (would diverge from the Spond invite). They're reported as
  `skipped_published`. Notes on those shifts are only filled in if currently
  blank.
"""
from __future__ import annotations

import logging
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date as date_type, datetime, time, timedelta
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.member_alias import MemberAlias
from app.models.training_session_type import TrainingSessionType
from app.models.training_shift import TrainingShift
from app.schemas.training import ImportReport, ImportReportUnresolved

logger = logging.getLogger(__name__)

# Excel 1900 date system anchor (accounts for the leap-year bug).
_EXCEL_EPOCH = date_type(1899, 12, 30)

_XLSX_NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

_SKIP_VAKTTYPES = {"stevner skive", "stevner skog"}

_DEFAULT_START = time(18, 0)
_DEFAULT_END = time(20, 0)

_FUZZY_MIN_SCORE = 85


@dataclass
class _ParsedRow:
    row_number: int  # 1-based for human-readable errors
    navn: Optional[str]
    initials: Optional[str]
    date: Optional[date_type]
    vakttype: Optional[str]


# ============================================================
# .xlsx parsing (stdlib)
# ============================================================

def _col_letters_to_index(ref: str) -> int:
    """Convert a cell reference like 'B12' or 'AA3' to a zero-based column index."""
    letters = "".join(c for c in ref if c.isalpha())
    n = 0
    for c in letters:
        n = n * 26 + (ord(c.upper()) - ord("A") + 1)
    return n - 1


def _parse_xlsx_sheet1(file_bytes: bytes) -> list[dict[int, Optional[str]]]:
    """Parse the first worksheet of an .xlsx file into a list of {col_idx: value}.

    Handles inline strings, numbers, and shared strings (the vaktliste only uses
    inline strings + numbers, but we support shared strings for safety).
    """
    with zipfile.ZipFile(_to_bytesio(file_bytes)) as zf:
        names = zf.namelist()
        if "xl/worksheets/sheet1.xml" not in names:
            raise ValueError("xlsx archive is missing xl/worksheets/sheet1.xml")
        sheet_xml = zf.read("xl/worksheets/sheet1.xml")

        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            shared_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in shared_root.findall("s:si", _XLSX_NS):
                # An <si> can contain a single <t> or multiple <r><t> rich-text
                # runs; concatenate text from all <t> descendants.
                parts = [t.text or "" for t in si.findall(".//s:t", _XLSX_NS)]
                shared.append("".join(parts))

    root = ET.fromstring(sheet_xml)
    sheet_data = root.find("s:sheetData", _XLSX_NS)
    if sheet_data is None:
        return []

    rows: list[dict[int, Optional[str]]] = []
    for row in sheet_data.findall("s:row", _XLSX_NS):
        cells: dict[int, Optional[str]] = {}
        for c in row.findall("s:c", _XLSX_NS):
            ref = c.get("r") or ""
            if not ref:
                continue
            idx = _col_letters_to_index(ref)
            t = c.get("t")
            value: Optional[str] = None
            if t == "inlineStr":
                t_elem = c.find("s:is", _XLSX_NS)
                if t_elem is not None:
                    parts = [
                        elem.text or "" for elem in t_elem.findall(".//s:t", _XLSX_NS)
                    ]
                    value = "".join(parts)
            elif t == "s":
                v_elem = c.find("s:v", _XLSX_NS)
                if v_elem is not None and v_elem.text is not None:
                    try:
                        ss_idx = int(v_elem.text)
                        if 0 <= ss_idx < len(shared):
                            value = shared[ss_idx]
                    except ValueError:
                        value = None
            else:
                v_elem = c.find("s:v", _XLSX_NS)
                if v_elem is not None:
                    value = v_elem.text
            cells[idx] = value
        rows.append(cells)
    return rows


def _to_bytesio(file_bytes: bytes):
    import io

    return io.BytesIO(file_bytes)


def _excel_serial_to_date(value: Optional[str]) -> Optional[date_type]:
    if value is None:
        return None
    try:
        serial = int(float(value))
    except (TypeError, ValueError):
        return None
    if serial <= 0:
        return None
    return _EXCEL_EPOCH + timedelta(days=serial)


def _row_to_parsed(row_idx: int, cells: dict[int, Optional[str]]) -> _ParsedRow:
    return _ParsedRow(
        row_number=row_idx + 1,  # xlsx rows are 1-based; idx 0 is row 1 (header)
        navn=(cells.get(0) or None) and (cells.get(0) or "").strip() or None,
        initials=(cells.get(1) or None) and (cells.get(1) or "").strip() or None,
        date=_excel_serial_to_date(cells.get(2)),
        vakttype=(cells.get(3) or None) and (cells.get(3) or "").strip() or None,
    )


# ============================================================
# Name matching
# ============================================================

def _normalize_name(name: str) -> str:
    name = name.lower().strip()
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _fuzzy_match_member(navn: str, members: Iterable[Member]) -> Optional[Member]:
    """Return the unique best matching Member if confident, else None.

    Strategy:
    1. Exact normalized match on `first_name` — if exactly one distinct member
       (de-duplicated by Spond profile email/name pair) → take it.
    2. Otherwise, rank by `max(WRatio(first), WRatio(full_name))` and accept
       the top candidate iff score >= threshold and there's a meaningful gap
       (>= 3 points) to the next *distinct* member. Duplicate Spond rows for
       the same human (same first+last) don't count as ambiguity.
    """
    try:
        from rapidfuzz import fuzz
    except ImportError:
        logger.warning("rapidfuzz not available — falling back to exact-match only")
        norm = _normalize_name(navn)
        exact = [m for m in members if _normalize_name(m.first_name) == norm]
        return exact[0] if len(exact) == 1 else None

    target = _normalize_name(navn)

    # Step 1: exact first-name match (case-insensitive, accent-folded).
    exact = [m for m in members if _normalize_name(m.first_name or "") == target]
    if exact:
        # De-duplicate by (first_name, last_name) — Spond sometimes has multiple
        # member rows for the same person.
        unique_keys = {
            (_normalize_name(m.first_name or ""), _normalize_name(m.last_name or ""))
            for m in exact
        }
        if len(unique_keys) == 1:
            return exact[0]
        # Multiple genuinely-different members share this first name → ambiguous.
        return None

    # Step 2: weighted-ratio scan, with duplicate-aware tie handling.
    scored: list[tuple[float, Member]] = []
    for m in members:
        first = _normalize_name(m.first_name or "")
        full = _normalize_name(f"{m.first_name or ''} {m.last_name or ''}")
        score = max(fuzz.WRatio(target, first), fuzz.WRatio(target, full))
        scored.append((score, m))
    if not scored:
        return None
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_member = scored[0]
    if best_score < _FUZZY_MIN_SCORE:
        return None
    best_key = (
        _normalize_name(best_member.first_name or ""),
        _normalize_name(best_member.last_name or ""),
    )
    # Find the runner-up that's a *different* person.
    runner_up_score = 0.0
    for s, m in scored[1:]:
        key = (
            _normalize_name(m.first_name or ""),
            _normalize_name(m.last_name or ""),
        )
        if key != best_key:
            runner_up_score = s
            break
    if best_score - runner_up_score < 3 and runner_up_score >= _FUZZY_MIN_SCORE:
        return None
    return best_member


# ============================================================
# Service
# ============================================================

class TrainingImportService:
    """Imports vaktliste .xlsx rows into training_shifts."""

    async def import_xlsx(
        self, db: AsyncSession, file_bytes: bytes
    ) -> ImportReport:  # noqa: C901 — single orchestration method, kept linear for readability
        rows = _parse_xlsx_sheet1(file_bytes)
        if not rows:
            return ImportReport(
                created=0,
                updated=0,
                skipped_published=0,
                skipped_unknown=0,
                unresolved_initials=[],
                created_session_types=[],
                created_aliases=0,
                errors=["Worksheet is empty"],
            )

        # Skip header row (idx 0).
        parsed: list[_ParsedRow] = []
        for i, cells in enumerate(rows):
            if i == 0:
                continue
            parsed.append(_row_to_parsed(i, cells))

        # Pre-load all members for fuzzy matching + alias lookups.
        members_result = await db.execute(select(Member))
        members = list(members_result.scalars().all())
        members_by_id = {m.id: m for m in members}

        aliases_result = await db.execute(select(MemberAlias))
        alias_map: dict[str, MemberAlias] = {
            a.initials.upper(): a for a in aliases_result.scalars().all()
        }

        # Pre-load session types into a name-keyed dict (case-insensitive).
        st_result = await db.execute(select(TrainingSessionType))
        session_types: dict[str, TrainingSessionType] = {
            s.name.lower(): s for s in st_result.scalars().all()
        }

        # Pre-load existing shifts keyed by (session_type_id, date).
        shifts_result = await db.execute(select(TrainingShift))
        existing_shifts: dict[tuple[int, date_type], TrainingShift] = {
            (s.session_type_id, s.date): s for s in shifts_result.scalars().all()
        }

        report = ImportReport(
            created=0,
            updated=0,
            skipped_published=0,
            skipped_unknown=0,
            unresolved_initials=[],
            created_session_types=[],
            created_aliases=0,
            errors=[],
        )

        for row in parsed:
            try:
                await self._process_row(
                    db,
                    row,
                    members,
                    members_by_id,
                    alias_map,
                    session_types,
                    existing_shifts,
                    report,
                )
            except Exception as exc:  # noqa: BLE001 — we want to keep going
                logger.exception("Failed to process vaktliste row %s", row)
                report.errors.append(f"Row {row.row_number}: {exc}")

        # Flush so callers can commit in their own transaction context.
        await db.flush()
        return report

    async def _process_row(
        self,
        db: AsyncSession,
        row: _ParsedRow,
        members: list[Member],
        members_by_id: dict[int, Member],
        alias_map: dict[str, MemberAlias],
        session_types: dict[str, TrainingSessionType],
        existing_shifts: dict[tuple[int, date_type], TrainingShift],
        report: ImportReport,
    ) -> None:
        # Empty / external-competition rows -> skip silently.
        if not row.vakttype:
            report.skipped_unknown += 1
            return
        if row.vakttype.lower() in _SKIP_VAKTTYPES:
            report.skipped_unknown += 1
            return
        if row.date is None:
            report.errors.append(
                f"Row {row.row_number}: missing or invalid Dato (vakttype={row.vakttype!r})"
            )
            return

        # Resolve/create the session type.
        session_type = session_types.get(row.vakttype.lower())
        if session_type is None:
            session_type = TrainingSessionType(
                name=row.vakttype,
                default_start_time=_DEFAULT_START,
                default_end_time=_DEFAULT_END,
                location=None,
                spond_subgroup_uids=None,
            )
            db.add(session_type)
            # Flush so the new session type has an id we can use to key the
            # `(session_type_id, date)` cache for subsequent rows.
            await db.flush()
            session_types[row.vakttype.lower()] = session_type
            report.created_session_types.append(row.vakttype)
            logger.info(
                "Auto-created session type %r (defaults %s–%s)",
                row.vakttype,
                _DEFAULT_START,
                _DEFAULT_END,
            )

        # Resolve initials -> member.
        leader: Optional[Member] = None
        raw_initials_to_store: Optional[str] = None
        if row.initials:
            initials_key = row.initials.upper()
            alias = alias_map.get(initials_key)
            if alias is not None:
                leader = members_by_id.get(alias.member_id)
            else:
                # Fuzzy-match by first name / full name.
                if row.navn:
                    matched = _fuzzy_match_member(row.navn, members)
                    if matched is not None:
                        new_alias = MemberAlias(
                            member_id=matched.id,
                            initials=initials_key,
                            source="auto",
                        )
                        db.add(new_alias)
                        alias_map[initials_key] = new_alias
                        report.created_aliases += 1
                        leader = matched
                        logger.info(
                            "Auto-created alias %r → member #%s (%s %s)",
                            initials_key,
                            matched.id,
                            matched.first_name,
                            matched.last_name,
                        )
                if leader is None:
                    raw_initials_to_store = row.initials
                    report.unresolved_initials.append(
                        ImportReportUnresolved(
                            initials=row.initials,
                            name=row.navn,
                            date=row.date,
                            session_type_name=row.vakttype,
                        )
                    )

        # Upsert the shift.
        key = (session_type.id, row.date)
        existing = existing_shifts.get(key)

        if existing is not None:
            if existing.status == "published":
                report.skipped_published += 1
                # Update notes if still blank, but never touch leader or
                # initials — that would diverge from the Spond invite.
                if not existing.notes and row.navn:
                    pass  # No spreadsheet column produces notes; nothing to do.
                return
            # Update draft / cancelled shift.
            existing.leader_member_id = leader.id if leader else None
            existing.raw_initials = raw_initials_to_store
            # Keep status as-is (draft or cancelled — user can re-draft).
            report.updated += 1
        else:
            new_shift = TrainingShift(
                session_type=session_type,
                date=row.date,
                leader_member_id=leader.id if leader else None,
                raw_initials=raw_initials_to_store,
                status="draft",
            )
            db.add(new_shift)
            # Keep the local cache up to date in case the same (session, date)
            # appears twice in the spreadsheet (would be a data bug, but…).
            existing_shifts[key] = new_shift
            report.created += 1


training_import_service = TrainingImportService()
