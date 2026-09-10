from decimal import Decimal
from uuid import uuid4

import pytest

from logistics.domain import CanonicalLocation, Load, LoadStop, Vehicle
from logistics.market_ops import NegotiationPolicy, PricingInput, estimate_price, match_carriers, next_counteroffer, score_opportunity


def load():
    return Load(
        tenant_id=uuid4(), cargo_type="general", weight_kg=10000, offered_price=Decimal("1000"), currency="EUR",
        stops=[LoadStop(sequence=0, kind="pickup", location=CanonicalLocation(raw_address="Kyiv", normalized_address="Kyiv")),
               LoadStop(sequence=1, kind="delivery", location=CanonicalLocation(raw_address="Lviv", normalized_address="Lviv"))],
    )


def test_price_and_opportunity_are_deterministic():
    estimate = estimate_price(load(), PricingInput(distance_km=Decimal("500"), fuel_cost_per_km=Decimal("0.8"), driver_cost=Decimal("100")))
    assert estimate.cost == Decimal("500")
    opportunity = score_opportunity(load(), estimate)
    assert opportunity.estimated_margin == Decimal("500")
    assert opportunity.risk_adjusted_margin == Decimal("500")
    assert 0 <= opportunity.score <= 1


def test_pricing_rejects_invalid_margin_and_negative_cost_inputs():
    with pytest.raises(ValueError):
        estimate_price(load(), PricingInput(distance_km=Decimal("1"), target_margin_rate=Decimal("1")))
    with pytest.raises(ValueError):
        estimate_price(load(), PricingInput(distance_km=Decimal("1"), fuel_cost_per_km=Decimal("-0.1")))


def test_matching_rejects_insufficient_capacity():
    carrier = Vehicle(tenant_id=uuid4(), carrier_party_id=uuid4(), capacity_kg=9000)
    assert match_carriers(load(), [carrier]) == []


def test_negotiation_stops_at_policy_floor():
    policy = NegotiationPolicy(min_price=Decimal("900"), target_price=Decimal("1000"))
    price, stop = next_counteroffer(Decimal("950"), policy, 1)
    assert price == Decimal("950")
    assert stop


def test_negotiation_rejects_invalid_round_and_policy():
    with pytest.raises(ValueError):
        next_counteroffer(Decimal("1100"), NegotiationPolicy(min_price=Decimal("0"), target_price=Decimal("0")), -1)
    with pytest.raises(ValueError):
        next_counteroffer(Decimal("1100"), NegotiationPolicy(min_price=Decimal("0"), target_price=Decimal("0"), max_discount_rate=Decimal("1.1")), 1)


def test_critical_negotiation_escalates():
    policy = NegotiationPolicy(min_price=Decimal("900"), target_price=Decimal("1000"))
    _, stop = next_counteroffer(Decimal("1100"), policy, 1, "critical")
    assert stop
