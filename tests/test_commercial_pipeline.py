from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from logistics.commercial_pipeline import build_commercial_candidates
from logistics.domain import CanonicalLocation, Load, LoadStop, Vehicle
from logistics.market_ops import PricingInput


def make_load(tenant_id, created_at, price="1000"):
    return Load(
        tenant_id=tenant_id,
        cargo_type="food",
        weight_kg=5000,
        offered_price=Decimal(price),
        currency="EUR",
        created_at=created_at,
        stops=[
            LoadStop(sequence=0, kind="pickup", location=CanonicalLocation(raw_address="UA", normalized_address="UA", country_code="UA")),
            LoadStop(sequence=1, kind="delivery", location=CanonicalLocation(raw_address="PL", normalized_address="PL", country_code="PL")),
        ],
    )


def test_pipeline_prioritizes_economic_and_recurring_candidates():
    tenant = uuid4()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)
    loads = [make_load(tenant, now - timedelta(days=14)), make_load(tenant, now - timedelta(days=7)), make_load(tenant, now)]
    carriers = [Vehicle(carrier_party_id=uuid4(), capacity_kg=10000)]
    result = build_commercial_candidates(
        loads,
        carriers,
        PricingInput(distance_km=Decimal("500"), fuel_cost_per_km=Decimal("0.5"), driver_cost=Decimal("100")),
        now=now,
    )
    assert len(result) == 3
    assert all(item.carrier_matches for item in result)
    assert all(item.recurring_pattern_key for item in result)
    assert result[0].priority_score >= result[-1].priority_score


def test_pipeline_marks_unmatched_carrier():
    tenant = uuid4()
    now = datetime(2026, 1, 20, tzinfo=timezone.utc)
    load = make_load(tenant, now)
    carrier = Vehicle(carrier_party_id=uuid4(), capacity_kg=100)
    result = build_commercial_candidates(
        [load],
        [carrier],
        PricingInput(distance_km=Decimal("100"), fuel_cost_per_km=Decimal("0.5")),
        now=now,
    )
    assert not result[0].carrier_matches
    assert "no_carrier_match" in result[0].reasons
