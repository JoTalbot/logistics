from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable


@dataclass(frozen=True)
class LearningCase:
    priority_score: float | None
    predicted_margin: Decimal | None
    actual_margin: Decimal | None
    outcome: str


@dataclass(frozen=True)
class LearningBand:
    band: str
    cases: int
    won: int
    lost: int
    win_rate: float
    average_prediction_error: Decimal | None


@dataclass(frozen=True)
class CommercialLearningReport:
    cases: int
    measured_cases: int
    won: int
    lost: int
    average_prediction_error: Decimal | None
    bands: tuple[LearningBand, ...]


def _band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 0.90:
        return "0.90-1.00"
    if score >= 0.70:
        return "0.70-0.89"
    return "0.00-0.69"


def evaluate_commercial_learning(cases: Iterable[LearningCase]) -> CommercialLearningReport:
    items = list(cases)
    errors = [c.actual_margin - c.predicted_margin for c in items if c.actual_margin is not None and c.predicted_margin is not None]
    bands: dict[str, list[LearningCase]] = {}
    for case in items:
        bands.setdefault(_band(case.priority_score), []).append(case)

    band_reports = []
    for name in sorted(bands):
        group = bands[name]
        won = sum(c.outcome == "won" for c in group)
        lost = sum(c.outcome == "lost" for c in group)
        measured = [c.actual_margin - c.predicted_margin for c in group if c.actual_margin is not None and c.predicted_margin is not None]
        terminal = won + lost
        band_reports.append(
            LearningBand(
                band=name,
                cases=len(group),
                won=won,
                lost=lost,
                win_rate=round(won / terminal, 4) if terminal else 0.0,
                average_prediction_error=(sum(measured, Decimal("0")) / len(measured)).quantize(Decimal("0.01")) if measured else None,
            )
        )

    won = sum(c.outcome == "won" for c in items)
    lost = sum(c.outcome == "lost" for c in items)
    return CommercialLearningReport(
        cases=len(items),
        measured_cases=len(errors),
        won=won,
        lost=lost,
        average_prediction_error=(sum(errors, Decimal("0")) / len(errors)).quantize(Decimal("0.01")) if errors else None,
        bands=tuple(band_reports),
    )


LEARNING_POLICY = "shadow-only-v25.1"


def learning_policy_snapshot() -> dict[str, object]:
    """Return the evaluation policy; deliberately performs no policy mutation."""
    return {
        "policy": LEARNING_POLICY,
        "mode": "shadow",
        "automatic_policy_mutation": False,
        "requires_replay_and_human_review": True,
    }
