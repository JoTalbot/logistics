from decimal import Decimal
from uuid import uuid4
from logistics.domain import Load, LoadStop, CanonicalLocation, Vehicle
from logistics.opportunities import price_load, match_vehicle


def make_load(weight=10000):
    return Load(tenant_id=uuid4(), cargo_type='cargo', weight_kg=weight, offered_price=Decimal('1000'), currency='EUR', stops=[LoadStop(sequence=0, kind='pickup', location=CanonicalLocation(raw_address='A', normalized_address='A', confidence=1)), LoadStop(sequence=1, kind='delivery', location=CanonicalLocation(raw_address='B', normalized_address='B', confidence=1))])


def test_price_load_calculates_risk_adjusted_margin():
    result = price_load(make_load(), cost=Decimal('700'), risk=Decimal('0.2'))
    assert result.margin == Decimal('300')
    assert result.risk_adjusted_margin == Decimal('240.0')


def test_vehicle_match_respects_capacity():
    load = make_load()
    vehicle = Vehicle(tenant_id=load.tenant_id, carrier_party_id=uuid4(), capacity_kg=12000)
    score, reasons = match_vehicle(load, vehicle)
    assert score == 1.0
    assert 'capacity_fit' in reasons
