# -*- coding: utf-8 -*-
"""Common helpers for report services."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _recent_scheduled_from(
    requested_scheduled_from: date | None,
    recorded_to: datetime,
) -> date:
    recent_cutoff = (recorded_to - timedelta(hours=168)).date()
    if requested_scheduled_from is None:
        return recent_cutoff
    return max(requested_scheduled_from, recent_cutoff)
