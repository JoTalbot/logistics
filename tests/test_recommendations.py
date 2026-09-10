from decimal import Decimal
from uuid import uuid4

from logistics.domain import CanonicalLocation, GeoPoint, Load, LoadStop, Opportunity
from logistics.recommendations import recommend_opportunity
from logistics.route_economics import calculate_route_economics, PriceTrendPoint


def _load(price: str = "2000", currency: str = "EUR") -> Load:
    tenant = uuid4()
    pickup = CanonicalLocation(raw_address="Kyiv", normalized_address="Kyiv", country_code="UA", point=GeoPoint(latitude=50.45, longitude=30.52))
    delivery = CanonicalLocation(raw_address="Lviv", normalized_address="Lviv", country_code="UA", point=GeoPoint(latitude=49.84, longitude=24.03))
    return Load(tenant_id=tenant, cargo_type="general", weight_kg=10000, offered_price=Decimal(price), currency=currency, stops=[
        LoadStop(sequence=0, kind="pickup", location=pickup),
        LoadStop(sequence=1, kind="delivery", location=delivery),
    ])


def _opportunity(load: Load, economics) -> Opportunity:
    return Opportunity(tenant_id=load.tenant_id, load_id=load.id, score=0.5, estimated_cost=economics.direct_cost, estimated_margin=economics.clean_profit, risk_adjusted_margin=economics.risk_adjusted_profit)


def test_recommendation_combines_market_and_economics_with_explainable_reasons():
    load = _load()
    economics = calculate_route_economics(revenue=load.offered_price, distance_km=Decimal("1000"), fuel_cost_per_km=Decimal("0.8"), driver_cost=Decimal("300"), risk_rate=Decimal("0.10"))
    trend = [PriceTrendPoint(None, "EUR", 3, Decimal("1900"), Decimal("1800"), Decimal("2000"))]
    result = recommend_opportunity(load, _opportunity(load, economics), economics, trend=trend)
    assert result.market_median == Decimal("1900")
    assert result.recommended_price >= Decimal("1900")
    assert "recent_market_median_available" in result.reasons
    assert result.score > 0


def test_recommendation_ignores_currency_mismatch():
    load = _load(currency="EUR")
    economics = calculate_route_economics(revenue=load.offered_price, distance_km=Decimal("1000"), fuel_cost_per_km=Decimal("0.8"))
    trend = [PriceTrendPoint(None, "UAH", 5, Decimal("90000"), Decimal("80000"), Decimal("100000"))]
    result = recommend_opportunity(load, _opportunity(load, economics), economics, trend=trend)
    assert result.market_median is None
    assert "market_median_unavailable_or_currency_mismatch" in result.reasons
