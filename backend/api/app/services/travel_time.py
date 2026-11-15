from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from math import ceil

from api.app.models import HourlyFactor

BUSINESS_TZ = timezone(timedelta(hours=5))


def hourly_factor_at(
    departure_time: datetime, factors: Sequence[HourlyFactor]
) -> float:
    local_hour = departure_time.astimezone(BUSINESS_TZ).hour
    for factor in factors:
        if factor.hour == local_hour:
            return factor.factor
    return 1.0


def adjusted_travel_seconds(
    base_seconds: int,
    departure_time: datetime,
    factors: Sequence[HourlyFactor],
) -> int:
    return ceil(base_seconds * hourly_factor_at(departure_time, factors))
