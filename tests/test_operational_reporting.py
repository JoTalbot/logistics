from datetime import datetime, timedelta, timezone

import pytest

from logistics.business_kpi import BusinessKPI
from logistics.operational_observability import OperationalObservabilityReport
from logistics.operational_reporting import (
    OperationalEvent,
    OperationalWindow,
    build_operational_snapshot,
)


def _kpi() -> BusinessKPI:
    return BusinessKPI(10, 4, 2, 1, 3, 1, 0.75, 2, 1, 1)


def _observability() -> OperationalObservabilityReport:
    return OperationalObservabilityReport(
        provider_latency_ms={"lardi": 120.5},
        provider_samples={"lardi": 4},
        route_quality_mean_absolute_error=0.05,
        route_quality_regressions=1,
        attributed_cost=2.5,
    )


def test_snapshot_selects_half_open_utc_window_and_sorts_event_counts():
    end = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
    events = (
        OperationalEvent(end - timedelta(hours=1), "accepted"),
        OperationalEvent(end - timedelta(minutes=30), "accepted"),
        OperationalEvent(end - timedelta(minutes=5), "provider_error"),
        OperationalEvent(end, "accepted"),
        OperationalEvent(end - timedelta(hours=3), "accepted"),
    )

    snapshot = build_operational_snapshot(
        OperationalWindow(end=end, duration=timedelta(hours=2)),
        events,
        _kpi(),
        _observability(),
    )

    assert snapshot.schema == "logistics.operational-snapshot.v1"
    assert snapshot.window_start == end - timedelta(hours=2)
    assert snapshot.window_end == end
    assert snapshot.event_counts == {"accepted": 2, "provider_error": 1}
    assert snapshot.business_kpi == _kpi()
    assert snapshot.observability == _observability()


def test_window_rejects_naive_end_and_non_positive_duration():
    with pytest.raises(ValueError, match="timezone-aware"):
        OperationalWindow(datetime(2026, 9, 14, 12), timedelta(hours=1))
    with pytest.raises(ValueError, match="positive"):
        OperationalWindow(datetime(2026, 9, 14, 12, tzinfo=timezone.utc), timedelta(0))


def test_event_rejects_naive_timestamp_and_empty_kind():
    with pytest.raises(ValueError, match="timezone-aware"):
        OperationalEvent(datetime(2026, 9, 14, 12), "accepted")
    with pytest.raises(ValueError, match="must not be empty"):
        OperationalEvent(datetime(2026, 9, 14, 12, tzinfo=timezone.utc), " ")
