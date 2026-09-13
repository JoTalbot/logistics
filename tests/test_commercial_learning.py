from decimal import Decimal

import pytest

from backend.logistics.commercial_learning import LearningCase, evaluate_learning, learning_gate
from backend.logistics.commercial_outcomes import CommercialOutcome, realized_margin, validate_commercial_outcome


def test_realized_margin_and_learning_metrics():
    assert realized_margin(Decimal("1200"), Decimal("900")) == Decimal("300")
    report = evaluate_learning([
        LearningCase(Decimal("300"), Decimal("320"), "won"),
        LearningCase(Decimal("200"), Decimal("150"), "lost"),
    ])
    assert report.cases == 2
    assert report.won_cases == 1
    assert report.lost_cases == 1
    assert report.mean_error == Decimal("-15")
    assert report.mean_absolute_error == Decimal("35")
    assert report.profitable_rate == 0.5


def test_learning_gate_requires_data_and_detects_drift():
    insufficient = evaluate_learning([LearningCase(Decimal("10"), Decimal("10"), "won")])
    assert learning_gate(insufficient) == "INSUFFICIENT_DATA"
    cases = [LearningCase(Decimal("0"), Decimal("150"), "won") for _ in range(20)]
    assert learning_gate(evaluate_learning(cases), max_mean_absolute_error=Decimal("100")) == "REVIEW_DRIFT"


def test_outcome_validation():
    outcome = CommercialOutcome(
        opportunity_id=__import__("uuid").uuid4(), outcome="won",
        operator_ref="operator-1", reason="completed",
        actual_revenue=Decimal("1000"), actual_cost=Decimal("700"), currency="UAH",
    )
    assert validate_commercial_outcome(outcome) == outcome
    with pytest.raises(ValueError, match="won outcome requires"):
        validate_commercial_outcome(CommercialOutcome(
            opportunity_id=outcome.opportunity_id, outcome="won",
            operator_ref="operator-1", reason="completed",
        ))
    with pytest.raises(ValueError, match="non-negative"):
        validate_commercial_outcome(CommercialOutcome(
            opportunity_id=outcome.opportunity_id, outcome="lost",
            operator_ref="operator-1", reason="bad", actual_cost=Decimal("-1"),
        ))
