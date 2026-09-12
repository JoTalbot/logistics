from __future__ import annotations

from decimal import Decimal

from logistics.commercial_learning import LearningCase, evaluate_commercial_learning, learning_policy_snapshot


def test_learning_report_calibrates_priority_bands_without_mutation():
    report = evaluate_commercial_learning([
        LearningCase(0.95, Decimal("30000"), Decimal("28000"), "won"),
        LearningCase(0.80, Decimal("20000"), Decimal("25000"), "won"),
        LearningCase(0.60, Decimal("10000"), Decimal("5000"), "lost"),
    ])
    assert report.cases == 3
    assert report.measured_cases == 3
    assert report.won == 2
    assert report.lost == 1
    assert report.average_prediction_error == Decimal("-666.67")
    assert report.bands[0].band == "0.00-0.69"
    assert report.bands[-1].band == "0.90-1.00"


def test_learning_policy_is_shadow_only():
    snapshot = learning_policy_snapshot()
    assert snapshot["mode"] == "shadow"
    assert snapshot["automatic_policy_mutation"] is False
    assert snapshot["requires_replay_and_human_review"] is True
