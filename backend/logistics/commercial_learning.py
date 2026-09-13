from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class LearningCase:
    predicted_margin: Decimal
    actual_margin: Decimal
    outcome: str


@dataclass(frozen=True)
class LearningReport:
    cases: int
    won_cases: int
    lost_cases: int
    mean_error: Decimal
    mean_absolute_error: Decimal
    profitable_rate: float


def evaluate_learning(cases: Iterable[LearningCase]) -> LearningReport:
    items = list(cases)
    if not items:
        return LearningReport(0, 0, 0, Decimal("0"), Decimal("0"), 0.0)
    errors = [case.actual_margin - case.predicted_margin for case in items]
    won = sum(case.outcome == "won" for case in items)
    lost = sum(case.outcome == "lost" for case in items)
    return LearningReport(
        cases=len(items),
        won_cases=won,
        lost_cases=lost,
        mean_error=sum(errors, Decimal("0")) / Decimal(len(items)),
        mean_absolute_error=sum((abs(e) for e in errors), Decimal("0")) / Decimal(len(items)),
        profitable_rate=round(won / len(items), 4),
    )


def learning_gate(report: LearningReport, *, max_mean_absolute_error: Decimal = Decimal("100"), min_cases: int = 20) -> str:
    """Return a review state; this function never mutates pricing/scoring policy."""
    if report.cases < min_cases:
        return "INSUFFICIENT_DATA"
    if report.mean_absolute_error > max_mean_absolute_error:
        return "REVIEW_DRIFT"
    return "SHADOW_READY"
