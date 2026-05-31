"""
Europe/Oslo ↔ UTC conversion helpers, dependency-free.

Spond timestamps are UTC (`…Z`); the training-plan UI works in local Oslo
wall-clock time (a shift's `start_time_override` is a local time-of-day).
These helpers bridge the two without pulling in ``zoneinfo`` / ``pytz``.

DST in Europe/Oslo runs from the last Sunday of March (02:00 → 03:00) to the
last Sunday of October. The rule is exact except within the ~1h transition
window in the small hours — training events never fall there, so the
best-effort offset is safe for this app's purposes.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date as date_type, datetime, time, timedelta

_OSLO_DST_START_MONTH = 3
_OSLO_DST_END_MONTH = 10


def _last_sunday(year: int, month: int) -> datetime:
    """Last Sunday of (year, month) at 02:00 local — the DST transition point."""
    last_day = monthrange(year, month)[1]
    for day in range(last_day, last_day - 7, -1):
        dt = datetime(year, month, day)
        if dt.weekday() == 6:  # Sunday
            return dt.replace(hour=2)
    return datetime(year, month, last_day, 2)  # fallback (unreachable)


def oslo_offset_for(d: datetime) -> timedelta:
    """Best-effort Europe/Oslo UTC offset for the given naive datetime.

    Returns +2h (CEST) inside the DST window, +1h (CET) otherwise.
    """
    naive = d.replace(tzinfo=None)
    dst_start = _last_sunday(d.year, _OSLO_DST_START_MONTH)
    dst_end = _last_sunday(d.year, _OSLO_DST_END_MONTH)
    if dst_start <= naive < dst_end:
        return timedelta(hours=2)  # CEST
    return timedelta(hours=1)  # CET


def local_oslo_to_utc_iso(d_date: date_type, t_time: time) -> str:
    """Combine a date + local Oslo time, convert to UTC, return ISO ``…Z``."""
    naive_local = datetime.combine(d_date, t_time)
    offset = oslo_offset_for(naive_local)
    utc = naive_local - offset
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_to_oslo_local(utc_dt: datetime) -> datetime:
    """Convert a naive-UTC datetime (as stored in the events table) to a naive
    Oslo local datetime. Inverse of ``local_oslo_to_utc_iso``.
    """
    naive_utc = utc_dt.replace(tzinfo=None)
    # Offset is keyed on the UTC instant — accurate except in the ~1h DST
    # transition window, which training events never hit.
    offset = oslo_offset_for(naive_utc)
    return naive_utc + offset
