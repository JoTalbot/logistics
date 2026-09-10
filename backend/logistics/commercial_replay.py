from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    expected_minimum_price: Decimal
    observed_price: Decimal
    outcome: str


@dataclass(frozen=True)
class ReplayReport:
    cases: int
    profitable_cases: int
    loss_cases: int
    unknown_cases: int
    profitable_rate: float


def evaluate_replay(cases: Iterable[ReplayCase]) -> ReplayReport:
    """Evaluate historical/synthetic commercial cases without external side effects."""
    cases = tuple(cases)
    profitable = sum(1 for case in cases if case.observed_price >= case.expected_minimum_price and case.outcome == "profitable")
    losses = sum(1 for case in cases if case.outcome == "loss")
    unknown = sum(1 for case in cases if case.outcome not in {"profitable", "loss"})
    rate = profitable / len(cases) if cases else 0.0
    return ReplayReport(
        cases=len(cases),
        profitable_cases=profitable,
        loss_cases=losses,
        unknown_cases=unknown,
        profitable_rate=round(rate, 4),
    )
