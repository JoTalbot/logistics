from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from logistics.market_observations import MarketObservation, observation_is_fresh
from logistics.route_economics import calculate_route_economics, price_trend, recommended_price


def test_route_economics_calculates_risk_adjusted_profit():
    economics = calculate_route_economics(
        revenue=Decimal("2000"), distance_km=Decimal("1000"), fuel_cost_per_km=Decimal("0.8"),
        tolls=Decimal("100"), driver_cost=Decimal("300"), overhead=Decimal("50"), risk_rate=Decimal("0.10"),
    )
    assert economics.direct_cost == Decimal("1250")
    assert economics.risk_reserve == Decimal("125.0")
    assert economics.clean_profit == Decimal("750")
    assert economics.risk_adjusted_profit == Decimal("625.0")


def test_recommended_price_respects_market_and_margin_floor():
    economics = calculate_route_economics(
        revenue=Decimal("1000"), distance_km=Decimal("500"), fuel_cost_per_km=Decimal("1"),
    )
    assert recommended_price(market_median=Decimal("550"), economics=economics) == Decimal("568.18")
    assert recommended_price(market_median=Decimal("800"), economics=economics) == Decimal("800.00")


def test_price_trend_groups_only_recent_route_observations():
    now = datetime(2026, 9, 10, 12, tzinfo=timezone.utc)
    observations = [
        MarketObservation("lardi-trans", "1", now - timedelta(days=2), {"route_key": "UA-KYIV-UA-LVIV", "price": 1000, "currency": "EUR"}),
        MarketObservation("lardi-trans", "2", now - timedelta(days=5), {"route_key": "UA-KYIV-UA-LVIV", "price": 1200, "currency": "EUR"}),
        MarketObservation("lardi-trans", "3", now - timedelta(days=40), {"route_key": "UA-KYIV-UA-LVIV", "price": 9999, "currency": "EUR"}),
        MarketObservation("lardi-trans", "4", now - timedelta(days=2), {"route_key": "UA-LVIV-UA-KYIV", "price": 700, "currency": "EUR"}),
    ]
    trend = price_trend(observations, route_key="UA-KYIV-UA-LVIV", now=now, window_days=30, bucket_days=7)
    assert sum(point.count for point in trend) == 2
    assert min(point.minimum_price for point in trend) == 1000


def test_freshness_rejects_stale_observation():
    now = datetime.now(timezone.utc)
    assert observation_is_fresh(now - timedelta(hours=1), now=now, max_age_seconds=3600)
    assert not observation_is_fresh(now - timedelta(hours=1, seconds=1), now=now, max_age_seconds=3600)
    with pytest.raises(ValueError):
        observation_is_fresh(now, now=now, max_age_seconds=-1)
