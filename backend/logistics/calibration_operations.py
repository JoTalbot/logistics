from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CalibrationGate:
    eligible: bool
    reason: str
    policy_mutation: bool = False


def evaluate_calibration_gate(
    *,
    terminal_cases: int,
    drift_detected: bool,
    minimum_terminal_cases: int = 20,
    operator_approved: bool = False,
) -> CalibrationGate:
    """Return a shadow-only gate; this function never mutates production policy."""
    if terminal_cases < 0:
        raise ValueError("terminal_cases must be non-negative")
    if minimum_terminal_cases < 1:
        raise ValueError("minimum_terminal_cases must be >= 1")
    if not drift_detected:
        return CalibrationGate(False, "no material drift detected")
    if terminal_cases < minimum_terminal_cases:
        return CalibrationGate(False, "insufficient terminal sample")
    if not operator_approved:
        return CalibrationGate(False, "explicit operator approval is required")
    return CalibrationGate(True, "eligible for shadow review; production policy remains unchanged")


def bounded_adjustment(
    *,
    current_score: float,
    suggested_delta: float,
    max_abs_delta: float = 0.05,
) -> float:
    """Produce a bounded shadow suggestion, never a persisted policy mutation."""
    if not 0.0 <= current_score <= 1.0:
        raise ValueError("current_score must be between 0 and 1")
    if max_abs_delta < 0:
        raise ValueError("max_abs_delta must be non-negative")
    delta = max(-max_abs_delta, min(max_abs_delta, suggested_delta))
    return max(0.0, min(1.0, current_score + delta))
