"""
Schemas for the training-plan feature (waves 1 + 2).

Wave 1: TrainingSessionType and MemberAlias request/response shapes.
Wave 2: TrainingShift CRUD, the .xlsx importer report, and the response shape
for /training/shifts (which embeds session_type + a compact leader summary).
"""
from datetime import date, datetime, time
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================================
# TrainingPlan
# ============================================================

class TrainingPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    period_start: date
    period_end: date
    description: Optional[str] = None
    is_active: bool = True

    @model_validator(mode="after")
    def _check_period(self) -> "TrainingPlanBase":
        if self.period_end < self.period_start:
            raise ValueError("period_end must not be before period_start")
        return self


class TrainingPlanCreate(TrainingPlanBase):
    pass


class TrainingPlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class TrainingPlanResponse(TrainingPlanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    # Counts populated at query time; never persisted on the row.
    session_type_count: int = 0
    shift_count: int = 0


class TrainingPlanListResponse(BaseModel):
    items: List[TrainingPlanResponse]
    total: int


# ============================================================
# LeaderGroup
# ============================================================

class LeaderGroupMemberSummary(BaseModel):
    """Compact member shape used inside LeaderGroupResponse.members."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: str
    first_name: str
    last_name: str


class LeaderGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class LeaderGroupCreate(LeaderGroupBase):
    # Optional initial member list (by member id) for one-shot creation.
    member_ids: Optional[List[int]] = None


class LeaderGroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None


class LeaderGroupResponse(LeaderGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    members: List[LeaderGroupMemberSummary] = Field(default_factory=list)


class LeaderGroupSummary(BaseModel):
    """Compact representation embedded on TrainingSessionTypeResponse."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class LeaderGroupListResponse(BaseModel):
    items: List[LeaderGroupResponse]
    total: int


class LeaderGroupMembersUpdate(BaseModel):
    """Bulk replacement of a leader group's member roster."""

    member_ids: List[int] = Field(default_factory=list)


# ============================================================
# TrainingSessionType
# ============================================================

class TrainingSessionTypeGroup(BaseModel):
    """Compact group summary embedded on session-type responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: str
    name: str


class TrainingSessionTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    plan_id: int  # The TrainingPlan this session type belongs to.
    default_start_time: time
    default_end_time: time
    location: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    group_id: Optional[int] = None
    # NULL or empty list → fall through to invited_member_ids / whole group.
    spond_subgroup_uids: Optional[List[str]] = None
    # Explicit member ids (members.id, internal). Takes precedence over
    # spond_subgroup_uids in the publish flow.
    invited_member_ids: Optional[List[int]] = None
    leader_group_id: Optional[int] = None
    # Default invite scheduling — see model docstring for semantics.
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None


class TrainingSessionTypeCreate(TrainingSessionTypeBase):
    pass


class TrainingSessionTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    # Moving a session type between plans isn't expected day-to-day, but
    # keep it possible — useful if an admin imports into the wrong plan.
    plan_id: Optional[int] = None
    default_start_time: Optional[time] = None
    default_end_time: Optional[time] = None
    location: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    group_id: Optional[int] = None
    spond_subgroup_uids: Optional[List[str]] = None
    invited_member_ids: Optional[List[int]] = None
    leader_group_id: Optional[int] = None
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None


class TrainingSessionTypeResponse(TrainingSessionTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group: Optional[TrainingSessionTypeGroup] = None
    leader_group: Optional[LeaderGroupSummary] = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# MemberAlias
# ============================================================

AliasSource = Literal["vaktliste", "manual", "auto"]


class MemberAliasMember(BaseModel):
    """Compact member summary embedded in alias responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: str
    first_name: str
    last_name: str


class MemberAliasBase(BaseModel):
    member_id: int
    initials: str = Field(..., min_length=1, max_length=16)
    source: AliasSource = "manual"


class MemberAliasCreate(MemberAliasBase):
    pass


class MemberAliasUpdate(BaseModel):
    member_id: Optional[int] = None
    initials: Optional[str] = Field(default=None, min_length=1, max_length=16)
    source: Optional[AliasSource] = None


class MemberAliasResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    initials: str
    source: str
    member: Optional[MemberAliasMember] = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# List wrappers
# ============================================================

class TrainingSessionTypeListResponse(BaseModel):
    items: List[TrainingSessionTypeResponse]
    total: int


class MemberAliasListResponse(BaseModel):
    items: List[MemberAliasResponse]
    total: int


# ============================================================
# TrainingShift
# ============================================================

ShiftStatus = Literal["draft", "published", "cancelled"]


class MemberLeaderSummary(BaseModel):
    """Compact member representation used in shift list responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    spond_id: str
    first_name: str
    last_name: str


class TrainingShiftCreate(BaseModel):
    session_type_id: int
    date: date
    leader_member_id: Optional[int] = None
    raw_initials: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = None
    start_time_override: Optional[time] = None
    end_time_override: Optional[time] = None
    invited_subgroup_uids: Optional[List[str]] = None
    invited_member_ids: Optional[List[int]] = None
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None

    @model_validator(mode="after")
    def _enforce_mutually_exclusive_invite(self) -> "TrainingShiftCreate":
        if self.invited_member_ids and self.invited_subgroup_uids:
            raise ValueError(
                "Set either invited_member_ids or invited_subgroup_uids, not both"
            )
        return self


class TrainingShiftUpdate(BaseModel):
    """Partial update; only fields explicitly set are applied.

    For published shifts the API only honors `notes` — leader, time
    overrides, and audience overrides are locked to whatever was sent to
    Spond. `status` may also be set to `cancelled` to soft-cancel a
    published shift.
    """

    leader_member_id: Optional[int] = None
    raw_initials: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = None
    start_time_override: Optional[time] = None
    end_time_override: Optional[time] = None
    invited_subgroup_uids: Optional[List[str]] = None
    invited_member_ids: Optional[List[int]] = None
    invite_lead_days: Optional[int] = Field(default=None, ge=0, le=365)
    invite_send_time: Optional[time] = None
    status: Optional[ShiftStatus] = None
    # Set by manual workflow when a user creates the Spond event themselves.
    spond_event_id: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _enforce_mutually_exclusive_invite(self) -> "TrainingShiftUpdate":
        if self.invited_member_ids and self.invited_subgroup_uids:
            raise ValueError(
                "Set either invited_member_ids or invited_subgroup_uids, not both"
            )
        return self


class TrainingShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_type_id: int
    date: date
    leader_member_id: Optional[int]
    raw_initials: Optional[str]
    notes: Optional[str]
    start_time_override: Optional[time]
    end_time_override: Optional[time]
    invited_subgroup_uids: Optional[List[str]] = None
    invited_member_ids: Optional[List[int]] = None
    invite_lead_days: Optional[int] = None
    invite_send_time: Optional[time] = None
    status: ShiftStatus
    spond_event_id: Optional[str]
    published_at: Optional[datetime]
    last_reverse_synced_at: Optional[datetime] = None
    # Local Event row id for this shift's published Spond event, if that event
    # has been synced into the events table. Computed at query time via
    # Event.spond_id == TrainingShift.spond_event_id — the inverse of the
    # event side's `linked_shift_id`. None when not published / not yet synced.
    linked_event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    session_type: TrainingSessionTypeResponse
    leader: Optional[MemberLeaderSummary] = None


class TrainingShiftListResponse(BaseModel):
    items: List[TrainingShiftResponse]
    total: int


# ============================================================
# Import report
# ============================================================

class ImportReportUnresolved(BaseModel):
    initials: Optional[str]
    name: Optional[str]
    date: Optional[date]
    session_type_name: Optional[str]


class ImportReport(BaseModel):
    created: int = 0
    updated: int = 0
    skipped_published: int = 0
    skipped_unknown: int = 0
    unresolved_initials: List[ImportReportUnresolved] = Field(default_factory=list)
    created_session_types: List[str] = Field(default_factory=list)
    created_aliases: int = 0
    errors: List[str] = Field(default_factory=list)


# ============================================================
# Statistics (plans-page Statistics tab)
# ============================================================

class TrainingStatSummary(BaseModel):
    total_shifts: int = 0
    draft: int = 0
    published: int = 0
    cancelled: int = 0
    accepted: int = 0
    declined: int = 0
    unanswered: int = 0
    session_type_count: int = 0
    leader_count: int = 0
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class TrainingStatSetupRow(BaseModel):
    session_type_id: int
    name: str
    total: int = 0
    draft: int = 0
    published: int = 0
    cancelled: int = 0
    accepted: int = 0
    declined: int = 0
    unanswered: int = 0
    distinct_leaders: int = 0
    first_date: Optional[date] = None
    last_date: Optional[date] = None


class TrainingStatLeaderRow(BaseModel):
    leader_member_id: Optional[int] = None
    label: str
    total: int = 0
    draft: int = 0
    published: int = 0
    cancelled: int = 0
    accepted: int = 0
    declined: int = 0
    unanswered: int = 0


class TrainingStatTimeBucket(BaseModel):
    period: str
    label: str
    total: int = 0
    draft: int = 0
    published: int = 0
    cancelled: int = 0


class TrainingStatisticsResponse(BaseModel):
    period: Literal["month", "week"]
    summary: TrainingStatSummary
    by_setup: List[TrainingStatSetupRow]
    by_leader: List[TrainingStatLeaderRow]
    over_time: List[TrainingStatTimeBucket]
