from datetime import datetime, timedelta, timezone

import pytest

from logistics.customer_discovery import QualificationResult
from logistics.customer_opportunities import freshness_score, score_customer_opportunity
from logistics.demand import DemandSignal


def test_freshness_decays_to_zero_after_72_hours():
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    assert freshness_score(now, now=now) == 1.0
    assert freshness_score(now - timedelta(hours=72), now=now) == 0.0


def test_customer_opportunity_is_deterministic():
    now = datetime(2026, 9, 10, tzinfo=timezone.utc)
    item = score_customer_opportunity(
        customer_id="c1",
        load_id="l1",
        demand=DemandSignal("c1", 0.8, ("cargo_match", "price_match")),
        observed_at=now - timedelta(hours=12),
        commercial_score=0.9,
        now=now,
    )
    assert item.total_score == 0.835
    assert "fresh_signal" in item.reasons


def test_customer_opportunity_rejects_invalid_commercial_score():
    with pytest.raises(ValueError):
        score_customer_opportunity(
            customer_id="c1",
            load_id="l1",
            demand=DemandSignal("c1", 0.8, ()),
            observed_at=datetime.now(timezone.utc),
            commercial_score=1.1,
        )
