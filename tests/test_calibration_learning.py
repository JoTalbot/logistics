from decimal import Decimal
from uuid import UUID, uuid4

from logistics.calibration_learning import build_shadow_recommendations
from logistics.commercial_calibration import CalibrationBand, CalibrationReport


def report(*, drift=True):
    bands = (
        CalibrationBand("low", 20, 20, 8, 0.4, Decimal("120.00"), Decimal("120.00"), True),
        CalibrationBand("medium", 20, 20, 12, 0.6, Decimal("-80.00"), Decimal("80.00"), True),
        CalibrationBand("high", 5, 5, 3, 0.6, Decimal("50.00"), Decimal("50.00"), False),
        CalibrationBand("very_high", 0, 0, 0, 0.0, None, None, False),
    )
    return CalibrationReport(40, 45 if False else 40, 0.5, Decimal("20.00"), Decimal("100.00"), bands, drift, "test drift")


def test_recommendations_are_deterministic_and_bounded():
    snapshot_id = UUID("00000000-0000-0000-0000-000000000001")
    first = build_shadow_recommendations(report(), snapshot_id=snapshot_id)
    second = build_shadow_recommendations(report(), snapshot_id=snapshot_id)
    assert first == second
    assert {item.band for item in first} == {"low", "medium"}
    assert all(abs(item.suggested_delta) <= Decimal("0.05") for item in first)
    assert all(item.policy_mutation is False for item in first)


def test_no_drift_produces_no_recommendations():
    assert build_shadow_recommendations(report(drift=False), snapshot_id=uuid4()) == ()


def test_snapshot_recommendations_never_mutate_live_policy():
    items = build_shadow_recommendations(report(), snapshot_id=uuid4())
    assert all(Decimal("0.00") <= item.suggested_score <= Decimal("1.00") for item in items)
