from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from logistics.telegram import ParsedLoadAd
from logistics.telegram_pipeline import parsed_ad_to_load, validate_parsed_ad


def make_ad(**overrides):
    data = dict(
        source_chat="https://t.me/example",
        source_message_id=42,
        published_at=datetime.now(timezone.utc),
        raw_text="Київ → Львів 20 т 1200 EUR зерно",
        origin="Київ",
        destination="Львів",
        cargo_type="зерно",
        weight_kg=20_000,
        price=Decimal("1200"),
        currency="EUR",
        confidence=1.0,
    )
    data.update(overrides)
    return ParsedLoadAd(**data)


def test_valid_ad_becomes_canonical_load():
    load = parsed_ad_to_load(make_ad(), tenant_id=uuid4())
    assert load.status.value == "normalized"
    assert len(load.stops) == 2
    assert load.weight_kg == 20_000
    assert load.offered_price == Decimal("1200")


def test_incomplete_ad_is_rejected():
    validation = validate_parsed_ad(make_ad(price=None), min_confidence=0.6)
    assert not validation.accepted
    assert "missing_price" in validation.reasons


def test_low_confidence_is_rejected():
    validation = validate_parsed_ad(make_ad(confidence=0.4))
    assert not validation.accepted
    assert "low_confidence" in validation.reasons


def test_conversion_raises_for_invalid_ad():
    with pytest.raises(ValueError, match="missing_destination"):
        parsed_ad_to_load(make_ad(destination=None), tenant_id=uuid4())
