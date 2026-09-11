"""Side-effect-free shadow decision records for controlled autonomy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from .autonomy_policy import ApprovalTier, AutonomyPolicy


POLICY_VERSION = "v21.1"


class DecisionMode(StrEnum):
    SIMULATION = "SIMULATION"
    SHADOW = "SHADOW"


@dataclass(frozen=True)
class ShadowDecision:
    decision_id: str
    tenant_id: str
    action: str
    confidence: float
    tier: ApprovalTier
    mode: DecisionMode
    policy_version: str
    classification_reason: str
    created_at: datetime


def classify_shadow_decision(
    *,
    decision_id: str,
    tenant_id: str,
    action: str,
    confidence: float,
    mode: DecisionMode = DecisionMode.SHADOW,
    policy: AutonomyPolicy | None = None,
    critical_risk: bool = False,
    requires_human_approval: bool = False,
    authorized: bool = True,
    policy_version: str = POLICY_VERSION,
) -> ShadowDecision:
    """Classify an intended action without performing the action."""
    active_policy = policy or AutonomyPolicy()
    tier = active_policy.classify(
        confidence,
        critical_risk=critical_risk,
        requires_human_approval=requires_human_approval,
        authorized=authorized,
    )
    reason = _reason(
        tier,
        confidence=confidence,
        critical_risk=critical_risk,
        requires_human_approval=requires_human_approval,
        authorized=authorized,
        policy=active_policy,
    )
    return ShadowDecision(
        decision_id=decision_id,
        tenant_id=tenant_id,
        action=action,
        confidence=confidence,
        tier=tier,
        mode=mode,
        policy_version=policy_version,
        classification_reason=reason,
        created_at=datetime.now(timezone.utc),
    )


def _reason(
    tier: ApprovalTier,
    *,
    confidence: float,
    critical_risk: bool,
    requires_human_approval: bool,
    authorized: bool,
    policy: AutonomyPolicy,
) -> str:
    if not authorized:
        return "BLOCK: action is not authorized"
    if critical_risk:
        return "BLOCK: critical risk overrides confidence"
    if requires_human_approval:
        return "REVIEW: explicit human approval is required"
    if tier is ApprovalTier.AUTO:
        return f"AUTO: confidence {confidence:.4f} >= auto threshold {policy.auto_confidence:.4f}"
    if tier is ApprovalTier.REVIEW:
        return f"REVIEW: confidence {confidence:.4f} is within review band"
    return f"HIGH_RISK: confidence {confidence:.4f} < review threshold {policy.review_confidence:.4f}"
