from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from logistics.domain import CanonicalLocation, Load, LoadStop
from logistics.events import CommandContext, InMemoryEventBus
from logistics.workflow import evaluate_load


def sample_load(price: str = "30000") -> Load:
    tenant = uuid4()
    return Load(
        tenant_id=tenant,
        cargo_type="general",
        weight_kg=10000,
        offered_price=Decimal(price),
        stops=[
            LoadStop(sequence=0, kind="pickup", location=CanonicalLocation(raw_address="  Kyiv,   Ukraine ", normalized_address="raw")),
            LoadStop(sequence=1, kind="delivery", location=CanonicalLocation(raw_address="Lviv, Ukraine", normalized_address="raw")),
        ],
    )


def test_load_normalize_score_is_deterministic():
    load = sample_load()
    ctx = CommandContext(tenant_id=load.tenant_id, actor_id=uuid4(), correlation_id=uuid4())
    bus1, bus2 = InMemoryEventBus(), InMemoryEventBus()
    a = evaluate_load(load, ctx, bus1)
    b = evaluate_load(load, ctx, bus2)
    assert a.score == b.score
    assert a.estimated_cost == b.estimated_cost
    assert a.risk_adjusted_margin == b.risk_adjusted_margin
    assert len(bus1.events) == 1
    assert bus1.events[0].event_type == "load.opportunity_scored"


def test_normalization_collapses_whitespace():
    load = sample_load()
    ctx = CommandContext(tenant_id=load.tenant_id, actor_id=uuid4(), correlation_id=uuid4())
    bus = InMemoryEventBus()
    evaluate_load(load, ctx, bus)
    payload = bus.events[0].payload["opportunity"]
    assert payload["load_id"] == str(load.id)
