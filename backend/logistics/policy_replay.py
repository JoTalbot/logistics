"""Deterministic replay metrics for autonomy-policy classifications."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from .autonomy_policy import ApprovalTier


class HistoricalOutcome(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PolicyReplayCase:
    tier: ApprovalTier
    outcome: HistoricalOutcome


@dataclass(frozen=True)
class PolicyReplayReport:
    cases: int
    by_tier: dict[str, int]
    successful_auto_cases: int
    failed_auto_cases: int
    auto_failure_rate: float
    review_or_higher_cases: int


def evaluate_policy_replay(cases: Iterable[PolicyReplayCase]) -> PolicyReplayReport:
    materialized = list(cases)
    counts = Counter(case.tier.value for case in materialized)
    auto_cases = [case for case in materialized if case.tier is ApprovalTier.AUTO]
    auto_failures = sum(case.outcome is HistoricalOutcome.FAILURE for case in auto_cases)
    auto_successes = sum(case.outcome is HistoricalOutcome.SUCCESS for case in auto_cases)
    review_or_higher = sum(case.tier is not ApprovalTier.AUTO for case in materialized)
    return PolicyReplayReport(
        cases=len(materialized),
        by_tier={tier.value: counts.get(tier.value, 0) for tier in ApprovalTier},
        successful_auto_cases=auto_successes,
        failed_auto_cases=auto_failures,
        auto_failure_rate=(auto_failures / len(auto_cases)) if auto_cases else 0.0,
        review_or_higher_cases=review_or_higher,
    )
