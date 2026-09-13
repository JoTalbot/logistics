from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
from typing import Iterable


BANDS = ("low", "medium", "high", "very_high")


@dataclass(frozen=True)
class CalibrationObservation:
    priority_score: float
    predicted_margin: Decimal | None
    actual_margin: Decimal | None
    outcome: str


@dataclass(frozen=True)
class CalibrationBand:
    band: str
    cases: int
    terminal_cases: int
    wins: int
    win_rate: float
    mean_prediction_error: Decimal | None
    mean_abs_prediction_error: Decimal | None
    sufficient_sample: bool


@dataclass(frozen=True)
class CalibrationReport:
    cases: int
    terminal_cases: int
    win_rate: float
    mean_prediction_error: Decimal | None
    mean_abs_prediction_error: Decimal | None
    bands: tuple[CalibrationBand, ...]
    drift_detected: bool
    drift_reason: str


def priority_band(score: float) -> str:
    if not 0.0 <= score <= 1.0:
        raise ValueError("priority_score must be between 0 and 1")
    if score >= 0.90:
        return "very_high"
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium"
    return "low"


def _error_values(items: Iterable[CalibrationObservation]) -> list[Decimal]:
    return [
        item.actual_margin - item.predicted_margin
        for item in items
        if item.actual_margin is not None and item.predicted_margin is not None
    ]


def _band(items: list[CalibrationObservation], name: str, min_sample: int) -> CalibrationBand:
    terminal = [item for item in items if item.outcome in {"won", "lost"}]
    wins = sum(item.outcome == "won" for item in terminal)
    errors = _error_values(items)
    return CalibrationBand(
        band=name,
        cases=len(items),
        terminal_cases=len(terminal),
        wins=wins,
        win_rate=round(wins / len(terminal), 4) if terminal else 0.0,
        mean_prediction_error=(mean(errors).quantize(Decimal("0.01")) if errors else None),
        mean_abs_prediction_error=(mean(abs(value) for value in errors).quantize(Decimal("0.01")) if errors else None),
        sufficient_sample=len(terminal) >= min_sample,
    )


def calibrate_observations(
    observations: Iterable[CalibrationObservation],
    *,
    min_sample: int = 10,
    drift_win_rate_delta: float = 0.15,
    drift_error_delta: Decimal = Decimal("100.00"),
) -> CalibrationReport:
    """Evaluate realized outcomes without changing pricing, scoring or policy."""
    if min_sample < 1:
        raise ValueError("min_sample must be positive")
    if drift_win_rate_delta < 0 or drift_error_delta < 0:
        raise ValueError("drift thresholds must be non-negative")

    items = list(observations)
    terminal = [item for item in items if item.outcome in {"won", "lost"}]
    errors = _error_values(items)
    bands = tuple(
        _band([item for item in items if priority_band(item.priority_score) == name], name, min_sample)
        for name in BANDS
    )

    sufficiently_sampled = [band for band in bands if band.sufficient_sample]
    reasons: list[str] = []
    for left, right in zip(sufficiently_sampled, sufficiently_sampled[1:]):
        if abs(left.win_rate - right.win_rate) >= drift_win_rate_delta:
            reasons.append(f"win-rate gap {left.band}->{right.band} exceeds threshold")
        if left.mean_abs_prediction_error is not None and right.mean_abs_prediction_error is not None:
            if abs(left.mean_abs_prediction_error - right.mean_abs_prediction_error) >= drift_error_delta:
                reasons.append(f"prediction-error gap {left.band}->{right.band} exceeds threshold")

    return CalibrationReport(
        cases=len(items),
        terminal_cases=len(terminal),
        win_rate=round(sum(item.outcome == "won" for item in terminal) / len(terminal), 4) if terminal else 0.0,
        mean_prediction_error=mean(errors).quantize(Decimal("0.01")) if errors else None,
        mean_abs_prediction_error=mean(abs(value) for value in errors).quantize(Decimal("0.01")) if errors else None,
        bands=bands,
        drift_detected=bool(reasons),
        drift_reason="; ".join(reasons) if reasons else "no statistically actionable drift signal",
    )


def load_calibration_observations(conn: object, *, tenant_id: object, limit: int = 5000) -> list[CalibrationObservation]:
    if not 1 <= limit <= 10000:
        raise ValueError("limit must be between 1 and 10000")
    rows = conn.execute(
        """
        SELECT o.priority_score, o.estimated_margin, h.actual_margin, h.outcome
          FROM commercial_outcome_history h
          JOIN opportunities o ON o.id=h.opportunity_id AND o.tenant_id=h.tenant_id
         WHERE h.tenant_id=%s
         ORDER BY h.recorded_at DESC, h.id DESC
         LIMIT %s
        """,
        (tenant_id, limit),
    ).fetchall()
    return [
        CalibrationObservation(
            priority_score=float(row[0]) if row[0] is not None else 0.0,
            predicted_margin=Decimal(str(row[1])) if row[1] is not None else None,
            actual_margin=Decimal(str(row[2])) if row[2] is not None else None,
            outcome=row[3],
        )
        for row in rows
    ]
