"""
Reverse sync: Spond event changes → linked training shifts.

The forward path (publish) builds a Spond event from a ``TrainingShift`` and
records the new event id on ``shift.spond_event_id``. This module is the
inverse: after the events sync refreshes the local ``Event`` rows, it
reconciles each linked shift so edits made in Spond (time moved, event
cancelled, responsible person or audience changed) flow back into the training
plan / calendar.

Join key: ``TrainingShift.spond_event_id == Event.spond_id``. Leader maps via
``Member.profile['id']`` (Spond ``owners[].id`` is a profile id); audience maps
via ``Member.spond_id`` (Spond ``recipients.groupMembers`` is a spond-id list).

Read-into-local only — it never re-publishes to Spond, so there is no loop.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.oslo_time import utc_to_oslo_local
from app.models.event import Event
from app.models.member import Member
from app.models.training_shift import TrainingShift

logger = logging.getLogger(__name__)


class TrainingReverseSyncService:
    """Reconcile training shifts from their linked (just-synced) Spond events."""

    @staticmethod
    async def reconcile_plan_from_events(
        db: AsyncSession, synced_spond_ids: List[str]
    ) -> Dict[str, Any]:
        """Reconcile every shift whose Spond event id is in ``synced_spond_ids``.

        Builds the member lookups once and processes all shifts in a single
        pass (no N+1). Returns ``{"shifts_updated": int, "changes": {id: [...]}}``.
        The caller owns the surrounding transaction/commit.
        """
        out: Dict[str, Any] = {"shifts_updated": 0, "changes": {}}
        if not synced_spond_ids:
            return out

        shifts = (
            (
                await db.execute(
                    select(TrainingShift)
                    .where(TrainingShift.spond_event_id.in_(synced_spond_ids))
                    .options(selectinload(TrainingShift.session_type))
                )
            )
            .scalars()
            .all()
        )
        if not shifts:
            return out

        linked_ids = [s.spond_event_id for s in shifts if s.spond_event_id]
        events = (
            (await db.execute(select(Event).where(Event.spond_id.in_(linked_ids))))
            .scalars()
            .all()
        )
        event_by_spond_id = {e.spond_id: e for e in events}

        # Member lookups, built once: by Spond member id (audience) and by
        # Spond profile id (leader/owner).
        members = (await db.execute(select(Member))).scalars().all()
        member_by_spond_id = {m.spond_id: m for m in members if m.spond_id}
        member_by_profile_id: Dict[str, Member] = {}
        for m in members:
            profile = m.profile or {}
            pid = profile.get("id") if isinstance(profile, dict) else None
            if isinstance(pid, str) and pid:
                member_by_profile_id[pid] = m

        for shift in shifts:
            event = event_by_spond_id.get(shift.spond_event_id)
            if event is None:
                continue
            changes = await TrainingReverseSyncService._reconcile_shift_from_event(
                db,
                shift,
                event,
                member_by_spond_id=member_by_spond_id,
                member_by_profile_id=member_by_profile_id,
            )
            if changes:
                shift.last_reverse_synced_at = datetime.utcnow()
                out["shifts_updated"] += 1
                out["changes"][shift.id] = changes
                logger.info(
                    "Reverse-synced shift %s from Spond event %s: %s",
                    shift.id,
                    shift.spond_event_id,
                    "; ".join(changes),
                )

        await db.flush()
        return out

    @staticmethod
    async def _reconcile_shift_from_event(
        db: AsyncSession,
        shift: TrainingShift,
        event: Event,
        *,
        member_by_spond_id: Dict[str, Member],
        member_by_profile_id: Dict[str, Member],
    ) -> List[str]:
        """Apply a single event's state to a shift. Returns a list of change
        descriptions (empty if nothing changed)."""
        changes: List[str] = []
        st = shift.session_type

        # ---- Start time + (possible) date move ----
        if event.start_time is not None:
            local_start = utc_to_oslo_local(event.start_time)
            new_start = local_start.time().replace(second=0, microsecond=0)
            default_start = st.default_start_time if st else None
            # Keep the row clean: an override equal to the session-type default
            # is stored as NULL (inherit).
            target = None if new_start == default_start else new_start
            if target != shift.start_time_override:
                shift.start_time_override = target
                changes.append(f"start_override={target}")

            new_date = local_start.date()
            if new_date != shift.date:
                clash = (
                    await db.execute(
                        select(TrainingShift.id).where(
                            TrainingShift.session_type_id == shift.session_type_id,
                            TrainingShift.date == new_date,
                            TrainingShift.id != shift.id,
                        )
                    )
                ).first()
                if clash:
                    logger.warning(
                        "Shift %s: Spond event moved to %s but that "
                        "(session_type, date) slot is taken; leaving date %s",
                        shift.id,
                        new_date,
                        shift.date,
                    )
                else:
                    shift.date = new_date
                    changes.append(f"date={new_date}")

        # ---- End time ----
        if event.end_time is not None:
            local_end = utc_to_oslo_local(event.end_time)
            new_end = local_end.time().replace(second=0, microsecond=0)
            default_end = st.default_end_time if st else None
            target = None if new_end == default_end else new_end
            if target != shift.end_time_override:
                shift.end_time_override = target
                changes.append(f"end_override={target}")

        # ---- Cancellation ----
        if event.cancelled and shift.status != "cancelled":
            shift.status = "cancelled"
            changes.append("status=cancelled")
        elif not event.cancelled and shift.status == "cancelled":
            # Un-cancelled in Spond. It still carries a spond_event_id, so the
            # correct non-cancelled state is "published".
            shift.status = "published"
            changes.append("status=published")

        # ---- Leader (owners[0].id is a Spond *profile* id) ----
        raw = event.raw_data if isinstance(event.raw_data, dict) else {}
        owners = raw.get("owners")
        if isinstance(owners, list) and owners and isinstance(owners[0], dict):
            owner_pid = owners[0].get("id")
            owner_member = (
                member_by_profile_id.get(owner_pid) if owner_pid else None
            )
            if owner_member is not None:
                if owner_member.id != shift.leader_member_id:
                    shift.leader_member_id = owner_member.id
                    changes.append(f"leader={owner_member.id}")
            elif owner_pid:
                logger.info(
                    "Shift %s: Spond owner profile %s not matched to a member; "
                    "leaving leader unchanged",
                    shift.id,
                    owner_pid,
                )

        # ---- Audience (recipients.groupMembers = list of Member.spond_id) ----
        recipients = raw.get("recipients")
        group_members = (
            recipients.get("groupMembers") if isinstance(recipients, dict) else None
        )
        if isinstance(group_members, list):
            resolved = sorted(
                member_by_spond_id[sid].id
                for sid in group_members
                if sid in member_by_spond_id
            )
            new_audience: Optional[List[int]] = resolved or None
            current = sorted(shift.invited_member_ids or [])
            if (new_audience or []) != current:
                shift.invited_member_ids = new_audience
                # invited_member_ids and invited_subgroup_uids are mutually
                # exclusive; an explicit member list wins.
                if new_audience is not None:
                    shift.invited_subgroup_uids = None
                changes.append(
                    f"audience={len(new_audience) if new_audience else 0} members"
                )

        return changes
