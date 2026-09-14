"""Bounded operational reporting that composes existing KPI and V32 evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .business_kpi import BusinessKPI
from .operational_observability import OperationalObservabilityReport


@dataclass(frozen=True)
class OperationalEvent:
    """Timestamped evidence item used only for bounded window selection."""

    occurred_at: datetime
    kind: str

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must be timezone-aware")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")


@dataclass(frozen=True)
class OperationalWindow:
    """A validated, half-open UTC reporting window."""

    end: datetime
    duration: timedelta

    def __post_init__(self) -> None:
        if self.end.tzinfo is None:
            raise ValueError("end must be timezone-aware")
        if self.duration <= timedelta(0):
            raise ValueError("duration must be positive")

    @property
    def start(self) -> datetime:
        return self.end - self.duration


@dataclass(frozen=True)
class OperationalSnapshot:
    """Machine-readable composition of business KPIs and V32 evidence."""

    window_start: datetime
    window_end: datetime
    event_counts: dict[str, int]
    business_kpi: BusinessKPI
    observability: OperationalObservabilityReport

    @property
    def schema(self) -> str:
        return "logistics.operational-snapshot.v1"


def build_operational_snapshot(
    window: OperationalWindow,
    events: Iterable[OperationalEvent],
    business_kpi: BusinessKPI,
    observability: OperationalObservabilityReport,
) -> OperationalSnapshot:
    """Compose existing KPI/observability evidence without mutating source state."""
    start = window.start.astimezone(timezone.utc)
    end = window.end.astimezone(timezone.utc)
    selected = tuple(
        event for event in events
        if start <= event.occurred_at.astimezone(timezone.utc) < end
    )
    counts: dict[str, int] = {}
    for event in selected:
        counts[event.kind] = counts.get(event.kind, 0) + 1
    return OperationalSnapshot(
        window_start=start,
        window_end=end,
        event_counts=dict(sorted(counts.items())),
        business_kpi=business_kpi,
        observability=observability,
    )
