"""Deterministic autonomy gates for simulation and controlled rollout."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ApprovalTier(StrEnum):
    AUTO = "AUTO"
    REVIEW = "REVIEW"
    HIGH_RISK = "HIGH_RISK"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class AutonomyPolicy:
    """Policy thresholds are configuration, not claims about model accuracy."""

    auto_confidence: float = 0.90
    review_confidence: float = 0.70

    def __post_init__(self) -> None:
        if not 0.0 <= self.review_confidence <= self.auto_confidence <= 1.0:
            raise ValueError("confidence thresholds must satisfy 0 <= review <= auto <= 1")

    def classify(
        self,
        confidence: float,
        *,
        critical_risk: bool = False,
        requires_human_approval: bool = False,
        authorized: bool = True,
    ) -> ApprovalTier:
        """Return the highest required approval tier without executing any action."""
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not authorized:
            return ApprovalTier.BLOCK
        if critical_risk:
            return ApprovalTier.BLOCK
        if requires_human_approval:
            return ApprovalTier.REVIEW
        if confidence >= self.auto_confidence:
            return ApprovalTier.AUTO
        if confidence >= self.review_confidence:
            return ApprovalTier.REVIEW
        return ApprovalTier.HIGH_RISK
