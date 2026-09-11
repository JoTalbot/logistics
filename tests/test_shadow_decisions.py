from datetime import timezone

import pytest

from logistics.autonomy_policy import ApprovalTier, AutonomyPolicy
from logistics.shadow_decisions import DecisionMode, classify_shadow_decision


@pytest.mark.parametrize(
    ("confidence", "expected"),
    [(0.95, ApprovalTier.AUTO), (0.80, ApprovalTier.REVIEW), (0.40, ApprovalTier.HIGH_RISK)],
)
def test_shadow_record_uses_policy(confidence, expected):
    record = classify_shadow_decision(
        decision_id="d-1",
        tenant_id="tenant-a",
        action="publish_load",
        confidence=confidence,
    )
    assert record.tier is expected
    assert record.mode is DecisionMode.SHADOW
    assert record.policy_version == "v21.1"
    assert record.classification_reason
    assert record.created_at.tzinfo is timezone.utc


def test_shadow_record_fails_closed_for_unauthorized_and_critical_risk():
    unauthorized = classify_shadow_decision(
        decision_id="d-2", tenant_id="tenant-a", action="publish_load", confidence=0.99, authorized=False
    )
    critical = classify_shadow_decision(
        decision_id="d-3", tenant_id="tenant-a", action="publish_load", confidence=0.99, critical_risk=True
    )
    assert unauthorized.tier is ApprovalTier.BLOCK
    assert "not authorized" in unauthorized.classification_reason
    assert critical.tier is ApprovalTier.BLOCK
    assert "critical risk" in critical.classification_reason


def test_explicit_approval_overrides_auto_band():
    record = classify_shadow_decision(
        decision_id="d-4",
        tenant_id="tenant-a",
        action="publish_load",
        confidence=0.99,
        requires_human_approval=True,
    )
    assert record.tier is ApprovalTier.REVIEW


def test_simulation_mode_is_explicit_and_policy_is_configurable():
    policy = AutonomyPolicy(auto_confidence=0.95, review_confidence=0.80)
    record = classify_shadow_decision(
        decision_id="d-5",
        tenant_id="tenant-a",
        action="quote_load",
        confidence=0.92,
        mode=DecisionMode.SIMULATION,
        policy=policy,
        policy_version="v21.2",
    )
    assert record.mode is DecisionMode.SIMULATION
    assert record.tier is ApprovalTier.REVIEW
    assert record.policy_version == "v21.2"


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_invalid_confidence_remains_rejected(confidence):
    with pytest.raises(ValueError):
        classify_shadow_decision(
            decision_id="bad", tenant_id="tenant-a", action="quote_load", confidence=confidence
        )
