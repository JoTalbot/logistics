from decimal import Decimal

from logistics.commercial_replay import ReplayCase, evaluate_replay
from scripts.v20_baseline import load_baseline


def test_v20_baseline_fixture_is_deterministic():
    baseline = load_baseline()
    cases = [
        ReplayCase(
            case_id=item["case_id"],
            expected_minimum_price=Decimal(item["expected_minimum_price"]),
            observed_price=Decimal(item["observed_price"]),
            outcome=item["outcome"],
        )
        for item in baseline["replay_cases"]
    ]

    report = evaluate_replay(cases)

    assert report.cases == 5
    assert report.profitable_cases == 2
    assert report.loss_cases == 2
    assert report.unknown_cases == 1
    assert report.profitable_rate == 0.4


def test_v20_baseline_contains_non_sensitive_kpi_contract():
    baseline = load_baseline()
    assert baseline["tenant_id"] == "00000000-0000-0000-0000-000000000020"
    assert baseline["kpi_baseline"]["ingestion_volume"] == 120
    assert baseline["kpi_baseline"]["provider_errors"] == 2
