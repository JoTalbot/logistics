from decimal import Decimal

from backend.logistics.api import app
from backend.logistics.commercial_calibration import (
    CalibrationObservation,
    calibrate_observations,
    priority_band,
)
import backend.logistics.commercial_calibration_api  # noqa: F401


def test_priority_bands_are_deterministic():
    assert priority_band(0.10) == "low"
    assert priority_band(0.50) == "medium"
    assert priority_band(0.75) == "high"
    assert priority_band(0.90) == "very_high"


def test_calibration_reports_prediction_error_and_sample_gates():
    observations = [
        CalibrationObservation(0.95, Decimal("100"), Decimal("120"), "won"),
        CalibrationObservation(0.80, Decimal("100"), Decimal("80"), "lost"),
        CalibrationObservation(0.60, Decimal("50"), Decimal("55"), "won"),
        CalibrationObservation(0.20, Decimal("40"), Decimal("30"), "lost"),
    ]
    report = calibrate_observations(observations, min_sample=2)
    assert report.cases == 4
    assert report.terminal_cases == 4
    assert report.win_rate == 0.5
    assert report.mean_prediction_error == Decimal("1.25")
    assert report.mean_abs_prediction_error == Decimal("13.75")
    assert all(not band.sufficient_sample for band in report.bands)
    assert report.drift_detected is False


def test_calibration_detects_material_band_gap_only_when_sampled():
    observations = [
        *[CalibrationObservation(0.95, Decimal("100"), Decimal("120"), "won") for _ in range(3)],
        *[CalibrationObservation(0.80, Decimal("100"), Decimal("0"), "lost") for _ in range(3)],
    ]
    report = calibrate_observations(
        observations,
        min_sample=3,
        drift_win_rate_delta=0.5,
        drift_error_delta=50,
    )
    assert report.drift_detected is True
    assert "win-rate gap" in report.drift_reason


def test_calibration_api_is_registered_and_shadow_only():
    routes = {route.path: route for route in app.routes}
    assert "/api/v1/review/commercial-calibration" in routes
    assert routes["/api/v1/review/commercial-calibration"].methods == {"GET"}
