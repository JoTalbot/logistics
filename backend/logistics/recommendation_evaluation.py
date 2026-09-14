from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class RecommendationEvaluationCase:
    recommendation_id: str
    band: str
    suggested_score: float
    later_score: float | None
    later_actual_margin: Decimal | None
    later_predicted_margin: Decimal | None
    outcome: str | None


@dataclass(frozen=True)
class RecommendationEvaluationReport:
    cases: int
    evaluated_cases: int
    accepted_cases: int
    rejected_cases: int
    unknown_cases: int
    mean_score_delta: float | None
    mean_abs_margin_error: Decimal | None


def evaluate_recommendations(cases: Iterable[RecommendationEvaluationCase]) -> RecommendationEvaluationReport:
    items = list(cases)
    if any(not 0.0 <= case.suggested_score <= 1.0 for case in items):
        raise ValueError("suggested_score must be between 0 and 1")
    if any(case.later_score is not None and not 0.0 <= case.later_score <= 1.0 for case in items):
        raise ValueError("later_score must be between 0 and 1")
    evaluated = [case for case in items if case.later_score is not None]
    terminal = [case for case in items if case.outcome in {"won", "lost"}]
    accepted = sum(case.outcome == "won" for case in terminal)
    rejected = sum(case.outcome == "lost" for case in terminal)
    margin_errors = [
        abs(case.later_predicted_margin - case.later_actual_margin)
        for case in items
        if case.later_predicted_margin is not None and case.later_actual_margin is not None
    ]
    score_deltas = [case.later_score - case.suggested_score for case in evaluated]
    return RecommendationEvaluationReport(
        cases=len(items),
        evaluated_cases=len(evaluated),
        accepted_cases=accepted,
        rejected_cases=rejected,
        unknown_cases=len(items) - len(terminal),
        mean_score_delta=round(sum(score_deltas) / len(score_deltas), 6) if score_deltas else None,
        mean_abs_margin_error=(sum(margin_errors, Decimal("0")) / len(margin_errors)).quantize(Decimal("0.01")) if margin_errors else None,
    )
