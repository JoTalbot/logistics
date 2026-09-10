from decimal import Decimal

from logistics.commercial_replay import ReplayCase, evaluate_replay


def test_replay_is_deterministic_and_side_effect_free():
    report = evaluate_replay([
        ReplayCase("a", Decimal("1000"), Decimal("1200"), "profitable"),
        ReplayCase("b", Decimal("900"), Decimal("800"), "loss"),
        ReplayCase("c", Decimal("700"), Decimal("700"), "unknown"),
    ])
    assert report.cases == 3
    assert report.profitable_cases == 1
    assert report.loss_cases == 1
    assert report.unknown_cases == 1
    assert report.profitable_rate == 0.3333


def test_empty_replay_has_zero_rate():
    assert evaluate_replay([]).profitable_rate == 0.0
