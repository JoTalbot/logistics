from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from collections import defaultdict
from statistics import median

from .domain import Load


@dataclass(frozen=True)
class DemandPattern:
    key: str
    observations: int
    first_seen: datetime
    last_seen: datetime
    median_interval_hours: float | None
    regularity_score: float
    recurrence_score: float
    reasons: tuple[str, ...]


def demand_pattern_key(load: Load) -> str:
    countries = ">".join(
        stop.location.country_code or "??"
        for stop in sorted(load.stops, key=lambda x: x.sequence)
    )
    return f"{countries}|{load.cargo_type.casefold().strip()}|{load.currency.casefold()}"


def detect_recurring_demand(loads: list[Load], *, min_observations: int = 3) -> list[DemandPattern]:
    if min_observations < 2:
        raise ValueError("min_observations must be at least 2")
    groups: dict[str, list[Load]] = defaultdict(list)
    for load in loads:
        groups[demand_pattern_key(load)].append(load)

    patterns: list[DemandPattern] = []
    for key, group in groups.items():
        ordered = sorted(group, key=lambda x: x.created_at)
        if len(ordered) < min_observations:
            continue
        intervals = [
            (b.created_at - a.created_at).total_seconds() / 3600.0
            for a, b in zip(ordered, ordered[1:])
        ]
        med = median(intervals)
        if med <= 0:
            regularity = 0.0
        else:
            deviation = median(abs(x - med) for x in intervals) / med
            regularity = max(0.0, min(1.0, 1.0 - deviation))
        recurrence = min(1.0, len(ordered) / 10.0)
        reasons = [f"observations={len(ordered)}"]
        if med <= 24 * 7:
            reasons.append("weekly_or_faster")
        if regularity >= 0.7:
            reasons.append("regular_intervals")
        patterns.append(DemandPattern(
            key=key,
            observations=len(ordered),
            first_seen=ordered[0].created_at,
            last_seen=ordered[-1].created_at,
            median_interval_hours=round(med, 2),
            regularity_score=round(regularity, 4),
            recurrence_score=round(recurrence, 4),
            reasons=tuple(reasons),
        ))
    return sorted(patterns, key=lambda x: (-x.recurrence_score, -x.regularity_score, x.key))


def pattern_freshness(pattern: DemandPattern, *, now: datetime | None = None, horizon_days: int = 30) -> float:
    reference = now or datetime.now(timezone.utc)
    age_days = max(0.0, (reference - pattern.last_seen).total_seconds() / 86400.0)
    return round(max(0.0, 1.0 - age_days / horizon_days), 4)
