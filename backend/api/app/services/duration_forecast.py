from __future__ import annotations

from collections import defaultdict
from math import ceil
from statistics import median
from typing import Any


MIN_HISTORY_SAMPLES = 3


def apply_duration_forecasts(
    orders: list[dict[str, Any]],
    history: list[dict[str, Any]],
    work_types: list[dict[str, Any]],
) -> None:
    exact_samples: dict[tuple[str, str], list[int]] = defaultdict(list)
    type_samples: dict[str, list[int]] = defaultdict(list)
    for row in history:
        duration = int(row["actual_duration_min"])
        if duration <= 0:
            continue
        code = str(row["work_type_code"])
        technology = str(row["technology"])
        exact_samples[(code, technology)].append(duration)
        type_samples[code].append(duration)

    norms = {
        str(item["code"]): int(item["duration_min"])
        for item in work_types
    }

    for order in orders:
        code = str(order["work_type_code"])
        technology = str(order["technology"])
        samples = exact_samples[(code, technology)]
        if len(samples) < MIN_HISTORY_SAMPLES:
            samples = type_samples[code]
        if len(samples) >= MIN_HISTORY_SAMPLES:
            order["duration_estimate_min"] = ceil(median(samples))
            order["duration_source"] = "HISTORY"
        else:
            order["duration_estimate_min"] = norms.get(code, 60)
            order["duration_source"] = "NORM"
