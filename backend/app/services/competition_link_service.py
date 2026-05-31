"""
Heuristic linking of upcoming external competitions to local entities.

An ``ExternalEvent`` (scraped from bueskyting.no) shares no id with a local
Spond ``Event`` (the club's planned attendance) or a ``Competition`` (its
results), so we *suggest* matches by date proximity + fuzzy name similarity
(rapidfuzz — already a dependency, used by archer_matching_service). Suggestions
are confirmed manually in the UI via ``set_link``; we never silently auto-write
a guess.
"""
from __future__ import annotations

import logging
from datetime import datetime, time, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competition import Competition
from app.models.event import Event
from app.models.external_event import ExternalEvent

logger = logging.getLogger(__name__)

# Tunables — a competition that the club attends usually has a Spond event
# within a few days of the published start date, with a similar name.
_DATE_WINDOW_DAYS = 3
_MIN_SCORE = 60.0
_MAX_SUGGESTIONS = 5


def _name_score(a: Optional[str], b: Optional[str]) -> float:
    """Fuzzy 0-100 name similarity. token_sort_ratio handles word reordering."""
    a, b = (a or ""), (b or "")
    try:
        from rapidfuzz import fuzz
        return float(fuzz.token_sort_ratio(a, b))
    except Exception:  # pragma: no cover — rapidfuzz is a hard dep
        la, lb = a.lower(), b.lower()
        if not la or not lb:
            return 0.0
        if la == lb:
            return 100.0
        return 50.0 if (la in lb or lb in la) else 0.0


class CompetitionLinkService:
    """Suggest and persist links from an external competition to local rows."""

    @staticmethod
    async def suggest_links(db: AsyncSession, ext: ExternalEvent) -> dict:
        """Return ranked candidate events + competitions for one external event."""
        events: list[dict] = []
        competitions: list[dict] = []

        if ext.date_start:
            lo = datetime.combine(
                ext.date_start - timedelta(days=_DATE_WINDOW_DAYS), time.min
            )
            hi = datetime.combine(
                ext.date_start + timedelta(days=_DATE_WINDOW_DAYS), time.max
            )
            rows = (
                await db.execute(
                    select(Event).where(
                        Event.start_time >= lo, Event.start_time <= hi
                    )
                )
            ).scalars().all()
            scored = [
                (s, e)
                for e in rows
                if (s := _name_score(ext.name, e.heading)) >= _MIN_SCORE
            ]
            scored.sort(key=lambda x: x[0], reverse=True)
            events = [
                {
                    "event_id": e.id,
                    "heading": e.heading,
                    "start_time": e.start_time,
                    "score": round(s, 1),
                }
                for s, e in scored[:_MAX_SUGGESTIONS]
            ]

        comps = (await db.execute(select(Competition))).scalars().all()
        scored_c = []
        for c in comps:
            if ext.date_start and c.date and abs(
                (c.date - ext.date_start).days
            ) > _DATE_WINDOW_DAYS:
                continue
            s = _name_score(ext.name, c.name)
            if s >= _MIN_SCORE:
                scored_c.append((s, c))
        scored_c.sort(key=lambda x: x[0], reverse=True)
        competitions = [
            {
                "competition_id": c.id,
                "name": c.name,
                "date": c.date,
                "score": round(s, 1),
            }
            for s, c in scored_c[:_MAX_SUGGESTIONS]
        ]

        return {"events": events, "competitions": competitions}

    @staticmethod
    async def set_link(
        db: AsyncSession,
        ext: ExternalEvent,
        *,
        event_id: Optional[int],
        competition_id: Optional[int],
    ) -> ExternalEvent:
        """Persist the (possibly cleared) links. Validates referenced rows."""
        if event_id is not None:
            ok = (
                await db.execute(select(Event.id).where(Event.id == event_id))
            ).first()
            if not ok:
                raise ValueError(f"Event {event_id} not found")
        if competition_id is not None:
            ok = (
                await db.execute(
                    select(Competition.id).where(Competition.id == competition_id)
                )
            ).first()
            if not ok:
                raise ValueError(f"Competition {competition_id} not found")
        ext.linked_event_id = event_id
        ext.linked_competition_id = competition_id
        await db.flush()
        return ext
