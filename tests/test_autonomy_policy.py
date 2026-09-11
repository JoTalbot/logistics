import pytest

from logistics.autonomy_policy import ApprovalTier, AutonomyPolicy


def test_default_confidence_bands_are_deterministic():
    policy = AutonomyPolicy()

    assert policy.classify(0.95) is ApprovalTier.AUTO
    assert policy.classify(0.90) is ApprovalTier.AUTO
    assert policy.classify(0.89) is ApprovalTier.REVIEW
    assert policy.classify(0.70) is ApprovalTier.REVIEW
    assert policy.classify(0.69) is ApprovalTier.HIGH_RISK


def test_critical_risk_and_unauthorized_actions_always_block():
    policy = AutonomyPolicy()

    assert policy.classify(1.0, critical_risk=True) is ApprovalTier.BLOCK
    assert policy.classify(1.0, authorized=False) is ApprovalTier.BLOCK


def test_explicit_human_approval_overrides_high_confidence():
    policy = AutonomyPolicy()

    assert policy.classify(0.99, requires_human_approval=True) is ApprovalTier.REVIEW


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_confidence_is_bounded(confidence):
    with pytest.raises(ValueError):
        AutonomyPolicy().classify(confidence)


def test_threshold_configuration_is_bounded():
    with pytest.raises(ValueError):
        AutonomyPolicy(auto_confidence=0.60, review_confidence=0.70)
