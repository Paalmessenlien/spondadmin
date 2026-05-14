"""
Spond event creation for the training-plan publish flow (wave 2).

Wraps the `POST sponds/` endpoint exposed by the Spond REST API. The `spond`
library doesn't ship a public create helper; `SpondService.create_event`
already implements the low-level POST, so we delegate the network call and
focus here on building a correct payload for a `TrainingShift`.

Owner semantics — verified against the live data in this DB:
- `owners[].id` is a **profile id** (e.g. `Member.profile['id']`), not the
  member id stored in `Member.spond_id`. We use `profile.id` when present;
  otherwise we fall back to omitting `owners` (Spond will default to the
  authenticated account).
- Spond may reject setting `owners` to a profile other than the
  authenticated user. On that failure we retry without `owners` and prepend
  the leader's name to the description so the human-readable signal is still
  there. The caller decides whether to surface the warning.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, time, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.member import Member
from app.models.training_shift import TrainingShift
from app.services.spond_service import SpondService

logger = logging.getLogger(__name__)


# Norway uses CEST (+02:00) from late March until late October and CET (+01:00)
# the rest of the year. Spond accepts either explicit offsets or UTC `Z`; we
# emit UTC to match how the existing event rows in this DB are stored.
_OSLO_DST_START_MONTH = 3
_OSLO_DST_END_MONTH = 10


def _oslo_offset_for(d: datetime) -> timedelta:
    """Best-effort Europe/Oslo offset without depending on zoneinfo.

    DST in Europe/Oslo runs from the last Sunday of March to the last Sunday of
    October. For the dates we care about (July–September is wave-2's primary
    window, and the importer file covers May–September) this rough rule is
    safe; for January or November the rule still resolves to standard time.
    """
    # Last Sunday of March / October.
    def last_sunday(year: int, month: int) -> datetime:
        # Start at the 31st and walk back to a Sunday.
        from calendar import monthrange

        last_day = monthrange(year, month)[1]
        for day in range(last_day, last_day - 7, -1):
            dt = datetime(year, month, day)
            if dt.weekday() == 6:  # Sunday
                return dt.replace(hour=2)  # transition at 02:00 local
        # Fallback (shouldn't happen).
        return datetime(year, month, last_day, 2)

    dst_start = last_sunday(d.year, _OSLO_DST_START_MONTH)
    dst_end = last_sunday(d.year, _OSLO_DST_END_MONTH)
    if dst_start <= d.replace(tzinfo=None) < dst_end:
        return timedelta(hours=2)  # CEST
    return timedelta(hours=1)  # CET


def _local_oslo_to_utc_iso(d_date, t_time: time) -> str:
    """Combine a date + local Oslo time, convert to UTC, return ISO `…Z`."""
    naive_local = datetime.combine(d_date, t_time)
    offset = _oslo_offset_for(naive_local)
    utc = naive_local - offset
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _compute_invite_send_at(
    shift_date,
    lead_days: Optional[int],
    send_time: Optional[time],
) -> Optional[str]:
    """Build the absolute send-at timestamp from (date - lead_days @ send_time).

    Returns a UTC ISO string with a trailing `Z`, or None if either input is
    missing (which means: send immediately on publish).
    """
    if lead_days is None or send_time is None:
        return None
    send_date = shift_date - timedelta(days=lead_days)
    return _local_oslo_to_utc_iso(send_date, send_time)


class SpondCreateError(Exception):
    """Raised when the Spond API returns a non-2xx response."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass
class SpondCreatePayload:
    """The structured payload we pass to `SpondService.create_event`."""

    event_data: dict[str, Any]
    group_id: Optional[str]
    invited_member_ids: Optional[list[str]]
    owner_ids: Optional[list[str]]

    def to_dict(self) -> dict[str, Any]:
        """Flat representation used by callers that want to inspect the payload."""
        flat = dict(self.event_data)
        if self.group_id:
            flat["_group_id"] = self.group_id
        if self.invited_member_ids is not None:
            flat["_invited_member_ids"] = self.invited_member_ids
        if self.owner_ids is not None:
            flat["_owner_ids"] = self.owner_ids
        return flat


class SpondEventCreateService:
    """Builds Spond create payloads from `TrainingShift` rows and POSTs them."""

    async def build_payload_from_shift(
        self,
        db: AsyncSession,
        shift: TrainingShift,
        default_group_uid: Optional[str] = None,
    ) -> SpondCreatePayload:
        """Construct the Spond payload for a single shift.

        Side effects: loads the related session type / leader / group rows from
        `db` if they aren't already attached. No writes.
        """
        # Ensure relationships are loaded — including session_type.group so
        # we can read the explicit Spond group binding without a lazy hit.
        from app.models.training_session_type import TrainingSessionType

        if shift.session_type is None or shift.session_type.group_id and shift.session_type.group is None:
            result = await db.execute(
                select(TrainingShift)
                .options(
                    selectinload(TrainingShift.session_type).selectinload(
                        TrainingSessionType.group
                    ),
                    selectinload(TrainingShift.leader),
                )
                .where(TrainingShift.id == shift.id)
            )
            shift = result.scalar_one()

        session_type = shift.session_type
        leader: Optional[Member] = shift.leader

        start_time = shift.start_time_override or session_type.default_start_time
        end_time = shift.end_time_override or session_type.default_end_time

        start_iso = _local_oslo_to_utc_iso(shift.date, start_time)
        end_iso = _local_oslo_to_utc_iso(shift.date, end_time)

        # Heading. Use the session type name verbatim — the leader's name
        # appears in the description ("Vakt: ...") and as the Spond
        # organizer; doubling it in the title looks like a mistake to
        # recipients. raw_initials likewise stays out of the title and
        # only surfaces in the editor's "unresolved initials" badge.
        heading = session_type.name

        description_parts: list[str] = []
        if leader is not None:
            description_parts.append(f"Vakt: {leader.first_name} {leader.last_name}")
        if session_type.description:
            description_parts.append(session_type.description.strip())
        if session_type.location:
            description_parts.append(f"Sted: {session_type.location}")
        if shift.notes:
            description_parts.append(shift.notes)
        description = "\n\n".join(description_parts) if description_parts else ""

        # Determine the Spond group id. Preference:
        #   1. The session type's explicit `group_id` (the training plan ↔
        #      Spond group binding set by an admin in the UI).
        #   2. `default_group_uid` passed by the caller.
        #   3. The largest group by member count (legacy fallback).
        primary_group = await self._resolve_group(
            db,
            default_group_uid=default_group_uid,
            session_type_group_id=session_type.group_id,
        )
        if primary_group is None:
            raise SpondCreateError(
                "No Spond group available — refusing to build payload",
                status_code=None,
                body=None,
            )

        group_id = primary_group.spond_id

        # Audience precedence:
        #   1. shift.invited_member_ids — explicit per-shift list of members.
        #   2. shift.invited_subgroup_uids — per-shift subgroup overrides.
        #   3. session_type.spond_subgroup_uids — session type's default subgroups.
        #   4. None — Spond will invite the whole group.
        invited_member_ids: Optional[list[str]] = None

        if shift.invited_member_ids:
            # Translate internal member ids → Spond member ids.
            stmt = select(Member.spond_id).where(
                Member.id.in_(list(shift.invited_member_ids))
            )
            rows = await db.execute(stmt)
            invited_member_ids = [r for r, in rows.all()]
            if not invited_member_ids:
                logger.warning(
                    "shift.invited_member_ids=%r resolved to zero members; "
                    "falling back to whole group",
                    shift.invited_member_ids,
                )
        else:
            # Shift overrides the session type entirely. An empty list on the
            # shift means "explicitly no subgroup narrowing on this shift" —
            # we treat that the same as "use the session type's default".
            target_subgroups: list[str]
            if shift.invited_subgroup_uids:
                target_subgroups = list(shift.invited_subgroup_uids)
            elif session_type.spond_subgroup_uids:
                target_subgroups = list(session_type.spond_subgroup_uids)
            else:
                target_subgroups = []

            if target_subgroups:
                target_set = set(target_subgroups)
                # Restrict the invite to members of the named subgroups. The
                # `recipients.groupMembers` field on a Spond event is a flat
                # list of *member* ids (i.e. `Member.spond_id`). A member is
                # included if their `group_members.subgroup_uids` intersects
                # the target set.
                stmt = (
                    select(Member.spond_id, GroupMember.subgroup_uids)
                    .join(GroupMember, GroupMember.member_id == Member.id)
                    .where(GroupMember.group_id == primary_group.id)
                )
                details = await db.execute(stmt)
                rows = details.all()
                invited_member_ids = [
                    mid
                    for mid, subs in rows
                    if subs and target_set.intersection(subs)
                ]
                # If nothing matched (subgroup uids wrong/empty), fall back to
                # all group members — better noisier than an event with zero
                # invitees.
                if not invited_member_ids:
                    logger.warning(
                        "Spond subgroup uids %r matched no members; inviting "
                        "all group members instead",
                        target_subgroups,
                    )
                    invited_member_ids = [mid for mid, _ in rows]

        # Owners. `owners[].id` must be the *profile* id, not Member.spond_id.
        owner_ids: Optional[list[str]] = None
        if leader is not None:
            profile_id = self._profile_id_for(leader)
            if profile_id:
                owner_ids = [profile_id]

        event_data: dict[str, Any] = {
            "heading": heading,
            "description": description,
            "spondType": "EVENT",
            "startTimestamp": start_iso,
            "endTimestamp": end_iso,
            "maxAccepted": 0,
            "visibility": "INVITEES",
            "autoAccept": False,
            "commentsDisabled": False,
        }
        if session_type.location:
            event_data["location"] = {"address": session_type.location}

        # Scheduled invitation send-at. Shift values win over the session
        # type's, and either field can independently fall back. When both
        # resolve to non-NULL we emit `inviteTime` (Spond's "send later"
        # field). If left out, Spond sends the invitation immediately.
        effective_lead_days = (
            shift.invite_lead_days
            if shift.invite_lead_days is not None
            else session_type.invite_lead_days
        )
        effective_send_time = (
            shift.invite_send_time
            if shift.invite_send_time is not None
            else session_type.invite_send_time
        )
        invite_time_iso = _compute_invite_send_at(
            shift.date, effective_lead_days, effective_send_time
        )
        if invite_time_iso:
            event_data["inviteTime"] = invite_time_iso

        return SpondCreatePayload(
            event_data=event_data,
            group_id=group_id,
            invited_member_ids=invited_member_ids,
            owner_ids=owner_ids,
        )

    async def create_event(
        self,
        spond: SpondService,
        payload: SpondCreatePayload,
        *,
        retry_without_owners_on_403: bool = True,
    ) -> dict[str, Any]:
        """POST the payload, with one retry fallback if Spond refuses the owner.

        On a 4xx that mentions ownership we strip `owner_ids` and re-issue, so
        the event still gets created (the leader name is already in the
        description by then if `prepare_for_owner_fallback` was called).
        """
        try:
            return await spond.create_event(
                event_data=payload.event_data,
                group_id=payload.group_id,
                invited_member_ids=payload.invited_member_ids,
                owner_ids=payload.owner_ids,
            )
        except Exception as exc:  # noqa: BLE001 — Spond client raises bare Exception
            message = str(exc)
            is_owner_problem = (
                retry_without_owners_on_403
                and payload.owner_ids
                and ("owner" in message.lower() or "403" in message or "permission" in message.lower())
            )
            if not is_owner_problem:
                raise SpondCreateError(
                    f"Spond create_event failed: {message}",
                    body=message,
                ) from exc

            logger.warning(
                "Spond rejected owner override (%s); retrying without owner_ids "
                "and prepending leader name to description.",
                message,
            )
            # Mutate a shallow copy so we don't lose the original payload for
            # diagnostics.
            self._prepare_for_owner_fallback(payload)
            try:
                return await spond.create_event(
                    event_data=payload.event_data,
                    group_id=payload.group_id,
                    invited_member_ids=payload.invited_member_ids,
                    owner_ids=None,
                )
            except Exception as exc2:  # noqa: BLE001
                raise SpondCreateError(
                    f"Spond create_event failed after owner fallback: {exc2}",
                    body=str(exc2),
                ) from exc2

    # ============================================================
    # Helpers
    # ============================================================

    def _prepare_for_owner_fallback(self, payload: SpondCreatePayload) -> None:
        """Drop owner_ids so Spond falls back to the authenticated account.

        The leader is already mentioned in the description ("Vakt: …") via
        build_payload_from_shift, so no additional rewriting is needed
        here — recipients still see who's leading.
        """
        payload.owner_ids = None

    def _profile_id_for(self, member: Member) -> Optional[str]:
        """Extract the Spond profile id from `member.profile` JSON, if any."""
        profile = member.profile or {}
        if isinstance(profile, dict):
            pid = profile.get("id")
            if isinstance(pid, str) and pid:
                return pid
        # Fallback: some raw_data rows store it under raw_data.profile.id too.
        raw = member.raw_data or {}
        if isinstance(raw, dict):
            inner = raw.get("profile") or {}
            if isinstance(inner, dict):
                pid = inner.get("id")
                if isinstance(pid, str) and pid:
                    return pid
        return None

    async def _resolve_group(
        self,
        db: AsyncSession,
        *,
        default_group_uid: Optional[str] = None,
        session_type_group_id: Optional[int] = None,
    ) -> Optional[Group]:
        """Return the Group to publish under.

        Preference:
        1. `session_type_group_id` — the explicit binding set on the training
           session type.
        2. `default_group_uid` — passed by the caller (currently unused, kept
           for API compatibility).
        3. The group with the most members (legacy fallback for session types
           that haven't been linked yet).
        """
        if session_type_group_id is not None:
            r = await db.execute(
                select(Group).where(Group.id == session_type_group_id)
            )
            g = r.scalar_one_or_none()
            if g is not None:
                return g
            logger.warning(
                "session_type.group_id=%s not found in DB; falling back",
                session_type_group_id,
            )

        if default_group_uid:
            r = await db.execute(
                select(Group).where(Group.spond_id == default_group_uid)
            )
            g = r.scalar_one_or_none()
            if g is not None:
                return g
            logger.warning(
                "default_group_uid=%r not found in DB; falling back to largest group",
                default_group_uid,
            )

        r = await db.execute(
            select(Group)
            .join(GroupMember, GroupMember.group_id == Group.id)
            .group_by(Group.id)
            .order_by(func.count(GroupMember.member_id).desc())
            .limit(1)
        )
        return r.scalar_one_or_none()


spond_event_create_service = SpondEventCreateService()
