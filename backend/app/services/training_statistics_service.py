"""
Training-plan statistics.

Aggregates training shifts over a date range into the breakdowns shown on the
plans page Statistics tab:
  - summary totals (shifts by status, distinct setups/leaders, Spond attendance)
  - by training setup (session type)
  - by leader
  - over time (per month or ISO week)

Spond attendance (accepted/declined/unanswered) is read from the linked Event
rows (shift.spond_event_id == Event.spond_id) — published shifts only.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date as date_type
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.training_session_type import TrainingSessionType
from app.models.training_shift import TrainingShift
from app.services.training_pdf_service import _leader_label


def _count_responses(event: Optional[Event]) -> tuple[int, int, int]:
    """(accepted, declined, unanswered) from an Event's responses JSON.

    Uses Spond's id arrays when present (exact + cheap), else the detailed
    responses array. Supports both the camelCase (Spond) and *_uids (legacy)
    key spellings.
    """
    if not event or not event.responses:
        return (0, 0, 0)
    r = event.responses
    if not isinstance(r, dict):
        return (0, 0, 0)
    has_arrays = any(
        k in r
        for k in ("acceptedIds", "declinedIds", "unansweredIds",
                  "accepted_uids", "declined_uids", "unanswered_uids")
    )
    if has_arrays:
        acc = len(r.get("acceptedIds") or r.get("accepted_uids") or [])
        dec = len(r.get("declinedIds") or r.get("declined_uids") or [])
        una = len(r.get("unansweredIds") or r.get("unanswered_uids") or [])
        return (acc, dec, una)
    acc = dec = una = 0
    for item in (r.get("responses") or []):
        a = item.get("answer")
        if a == "accepted":
            acc += 1
        elif a == "declined":
            dec += 1
        elif a == "unanswered":
            una += 1
    return (acc, dec, una)


def _period_key(d: date_type, period: str) -> tuple[str, str]:
    """Return (sort_key, label) for the time bucket a date falls in."""
    if period == "week":
        iso = d.isocalendar()
        return (f"{iso[0]}-W{iso[1]:02d}", f"Uke {iso[1]}, {iso[0]}")
    # default: month
    _MONTHS_NB = ("jan", "feb", "mar", "apr", "mai", "jun",
                  "jul", "aug", "sep", "okt", "nov", "des")
    return (f"{d.year}-{d.month:02d}", f"{_MONTHS_NB[d.month - 1]} {d.year}")


class TrainingStatisticsService:
    """Aggregate training shifts into the plans-page Statistics breakdowns."""

    @staticmethod
    async def get_statistics(
        db: AsyncSession,
        *,
        plan_id: Optional[int] = None,
        start_date: Optional[date_type] = None,
        end_date: Optional[date_type] = None,
        period: str = "month",
    ) -> dict:
        period = "week" if period == "week" else "month"

        stmt = (
            select(TrainingShift)
            .join(TrainingSessionType)
            .options(
                selectinload(TrainingShift.session_type),
                selectinload(TrainingShift.leader),
            )
        )
        if plan_id is not None:
            stmt = stmt.where(TrainingSessionType.plan_id == plan_id)
        if start_date is not None:
            stmt = stmt.where(TrainingShift.date >= start_date)
        if end_date is not None:
            stmt = stmt.where(TrainingShift.date <= end_date)
        shifts = (await db.execute(stmt)).scalars().unique().all()

        # Batch-load linked events for attendance (published shifts only carry
        # a spond_event_id).
        spond_ids = [s.spond_event_id for s in shifts if s.spond_event_id]
        event_by_spond: dict[str, Event] = {}
        if spond_ids:
            evs = (
                await db.execute(select(Event).where(Event.spond_id.in_(spond_ids)))
            ).scalars().all()
            event_by_spond = {e.spond_id: e for e in evs}

        def attendance_for(shift: TrainingShift) -> tuple[int, int, int]:
            if not shift.spond_event_id:
                return (0, 0, 0)
            return _count_responses(event_by_spond.get(shift.spond_event_id))

        # ---- Accumulators ----
        summary = {
            "total_shifts": 0, "draft": 0, "published": 0, "cancelled": 0,
            "accepted": 0, "declined": 0, "unanswered": 0,
            "date_from": None, "date_to": None,
        }
        setups: dict[int, dict] = {}
        leaders: dict[tuple, dict] = {}
        buckets: dict[str, dict] = {}
        setup_leaders: dict[int, set] = defaultdict(set)

        for s in shifts:
            status = s.status if s.status in ("draft", "published", "cancelled") else "draft"
            acc, dec, una = attendance_for(s)

            # summary
            summary["total_shifts"] += 1
            summary[status] += 1
            summary["accepted"] += acc
            summary["declined"] += dec
            summary["unanswered"] += una
            if summary["date_from"] is None or s.date < summary["date_from"]:
                summary["date_from"] = s.date
            if summary["date_to"] is None or s.date > summary["date_to"]:
                summary["date_to"] = s.date

            # by setup
            st = s.session_type
            sid = s.session_type_id
            row = setups.get(sid)
            if row is None:
                row = setups[sid] = {
                    "session_type_id": sid,
                    "name": st.name if st else "—",
                    "total": 0, "draft": 0, "published": 0, "cancelled": 0,
                    "accepted": 0, "declined": 0, "unanswered": 0,
                    "first_date": s.date, "last_date": s.date,
                    "distinct_leaders": 0,
                }
            row["total"] += 1
            row[status] += 1
            row["accepted"] += acc
            row["declined"] += dec
            row["unanswered"] += una
            row["first_date"] = min(row["first_date"], s.date)
            row["last_date"] = max(row["last_date"], s.date)
            if s.leader_member_id is not None:
                setup_leaders[sid].add(("m", s.leader_member_id))
            elif s.raw_initials:
                setup_leaders[sid].add(("i", s.raw_initials))

            # by leader (group by identity; label via the shared PDF helper)
            if s.leader_member_id is not None:
                lkey: tuple = ("m", s.leader_member_id)
            elif s.raw_initials:
                lkey = ("i", s.raw_initials)
            else:
                lkey = ("none",)
            lrow = leaders.get(lkey)
            if lrow is None:
                lrow = leaders[lkey] = {
                    "leader_member_id": s.leader_member_id,
                    "label": _leader_label(s),
                    "total": 0, "draft": 0, "published": 0, "cancelled": 0,
                    "accepted": 0, "declined": 0, "unanswered": 0,
                }
            lrow["total"] += 1
            lrow[status] += 1
            lrow["accepted"] += acc
            lrow["declined"] += dec
            lrow["unanswered"] += una

            # over time
            key, label = _period_key(s.date, period)
            bkt = buckets.get(key)
            if bkt is None:
                bkt = buckets[key] = {
                    "period": key, "label": label,
                    "total": 0, "draft": 0, "published": 0, "cancelled": 0,
                }
            bkt["total"] += 1
            bkt[status] += 1

        for sid, row in setups.items():
            row["distinct_leaders"] = len(setup_leaders.get(sid, ()))

        summary["session_type_count"] = len(setups)
        summary["leader_count"] = len([k for k in leaders if k != ("none",)])

        # Sort: setups by total desc then name; leaders by total desc then
        # label, unassigned last; buckets chronologically.
        by_setup = sorted(
            setups.values(), key=lambda r: (-r["total"], r["name"].lower())
        )
        by_leader = sorted(
            leaders.values(),
            key=lambda r: (r["label"] == "—", -r["total"], r["label"].lower()),
        )
        over_time = [buckets[k] for k in sorted(buckets.keys())]

        return {
            "period": period,
            "summary": summary,
            "by_setup": by_setup,
            "by_leader": by_leader,
            "over_time": over_time,
        }
