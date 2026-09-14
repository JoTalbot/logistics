import pytest
from decimal import Decimal

from logistics.recommendation_evaluation import RecommendationEvaluationCase, evaluate_recommendations


def test_evaluation_is_deterministic_and_read_only():
    report = evaluate_recommendations([
        RecommendationEvaluationCase("r1", "high", 0.80, 0.85, Decimal("120.00"), Decimal("130.00"), "won"),
        RecommendationEvaluationCase("r2", "medium", 0.60, 0.55, Decimal("80.00"), Decimal("100.00"), "lost"),
        RecommendationEvaluationCase("r3", "low", 0.40, None, None, None, None),
    ])
    assert report.cases == 3
    assert report.evaluated_cases == 2
    assert report.accepted_cases == 1
    assert report.rejected_cases == 1
    assert report.unknown_cases == 1
    assert report.mean_score_delta == 0.0
    assert report.mean_abs_margin_error == Decimal("15.00")


def test_invalid_scores_are_rejected():
    with pytest.raises(ValueError):
        evaluate_recommendations([RecommendationEvaluationCase("r1", "high", 1.1, None, None, None, None)])
