from datetime import datetime, timedelta, timezone
from uuid import uuid4
from decimal import Decimal

from logistics.domain import CanonicalLocation, GeoPoint, Load, LoadStop
from logistics.recurring_demand import detect_recurring_demand, demand_pattern_key, pattern_freshness


def make_load(day: int, cargo: str = "food") -> Load:
    location_a = CanonicalLocation(raw_address="A", normalized_address="A", country_code="UA")
    location_b = CanonicalLocation(raw_address="B", normalized_address="B", country_code="PL")
    return Load(
        tenant_id=uuid4(), cargo_type=cargo, weight_kg=1000, offered_price=1000,
        currency="EUR", created_at=datetime(2026, 9, 1, tzinfo=timezone.utc) + timedelta(days=day),
        stops=[LoadStop(sequence=0, kind="pickup", location=location_a), LoadStop(sequence=1, kind="delivery", location=location_b)],
    )


def test_pattern_key_is_deterministic():
    assert demand_pattern_key(make_load(0)) == "UA>PL|food|eur"


def test_detects_regular_recurring_pattern():
    result = detect_recurring_demand([make_load(0), make_load(7), make_load(14)])
    assert len(result) == 1
    assert result[0].observations == 3
    assert result[0].median_interval_hours == 168
    assert result[0].regularity_score == 1.0
    assert "regular_intervals" in result[0].reasons


def test_ignores_insufficient_history():
    assert detect_recurring_demand([make_load(0), make_load(7)]) == []


def test_pattern_freshness_decays():
    pattern = detect_recurring_demand([make_load(0), make_load(7), make_load(14)])[0]
    now = pattern.last_seen + timedelta(days=15)
    assert pattern_freshness(pattern, now=now) == 0.5
