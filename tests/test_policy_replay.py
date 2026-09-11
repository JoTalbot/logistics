from logistics.autonomy_policy import ApprovalTier
from logistics.policy_replay import HistoricalOutcome, PolicyReplayCase, evaluate_policy_replay


def test_policy_replay_reports_tiers_and_auto_failure_rate():
    report = evaluate_policy_replay(
        [
            PolicyReplayCase(ApprovalTier.AUTO, HistoricalOutcome.SUCCESS),
            PolicyReplayCase(ApprovalTier.AUTO, HistoricalOutcome.FAILURE),
            PolicyReplayCase(ApprovalTier.REVIEW, HistoricalOutcome.SUCCESS),
            PolicyReplayCase(ApprovalTier.HIGH_RISK, HistoricalOutcome.UNKNOWN),
            PolicyReplayCase(ApprovalTier.BLOCK, HistoricalOutcome.FAILURE),
        ]
    )
    assert report.cases == 5
    assert report.by_tier == {"AUTO": 2, "REVIEW": 1, "HIGH_RISK": 1, "BLOCK": 1}
    assert report.successful_auto_cases == 1
    assert report.failed_auto_cases == 1
    assert report.auto_failure_rate == 0.5
    assert report.review_or_higher_cases == 3


def test_policy_replay_is_zero_safe_without_auto_cases():
    report = evaluate_policy_replay(
        [PolicyReplayCase(ApprovalTier.BLOCK, HistoricalOutcome.UNKNOWN)]
    )
    assert report.auto_failure_rate == 0.0
