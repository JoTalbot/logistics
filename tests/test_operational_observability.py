from __future__ import annotations

import pytest

from logistics.operational_observability import (
    CostAttribution,
    ProviderLatency,
    RouteQualityObservation,
    build_observability_report,
)


def test_report_aggregates_latency_route_regression_and_cost() -> None:
    report = build_observability_report(
        [ProviderLatency("lardi", (100, 150, 200)), ProviderLatency("della", (50,))],
        [
            RouteQualityObservation("kyiv-odesa", 0.9, 0.79),
            RouteQualityObservation("lviv-kyiv", 0.8, 0.79),
            RouteQualityObservation("odesa-lviv", 0.7, 0.9),
        ],
        [CostAttribution("llm", 100, 0.002), CostAttribution("storage", 3, 0.5)],
    )

    assert report.provider_latency_ms == {"lardi": 150.0, "della": 50.0}
    assert report.provider_samples == {"lardi": 3, "della": 1}
    assert report.route_quality_mean_absolute_error == pytest.approx(0.1067, abs=0.001)
    assert report.route_quality_regressions == 1
    assert report.attributed_cost == 1.7


def test_empty_inputs_are_deterministic() -> None:
    report = build_observability_report([], [], [])
    assert report.provider_latency_ms == {}
    assert report.provider_samples == {}
    assert report.route_quality_mean_absolute_error == 0.0
    assert report.route_quality_regressions == 0
    assert report.attributed_cost == 0.0


def test_duplicate_provider_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="provider names must be unique"):
        build_observability_report(
            [ProviderLatency("lardi", (1,)), ProviderLatency("lardi", (2,))], [], []
        )


def test_invalid_scores_and_negative_costs_are_rejected() -> None:
    with pytest.raises(ValueError, match="expected_score"):
        RouteQualityObservation("route", 1.1, 0.5)
    with pytest.raises(ValueError, match="non-negative"):
        CostAttribution("llm", 1, -0.1)
    with pytest.raises(ValueError, match="non-negative"):
        ProviderLatency("lardi", (-1,))


def test_negative_regression_threshold_is_rejected() -> None:
    with pytest.raises(ValueError, match="regression_threshold"):
        build_observability_report([], [], [], regression_threshold=-0.1)
