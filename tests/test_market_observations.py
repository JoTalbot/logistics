from datetime import datetime, timezone

from logistics.market_observations import (
    MarketObservation,
    extract_verified_fields,
    normalize_lardi_response,
    stable_external_ref,
)
from logistics.price_intelligence import summarize_prices


def test_normalization_preserves_provider_payload_and_id():
    observed = datetime(2026, 9, 10, tzinfo=timezone.utc)
    result = normalize_lardi_response({"items": [{"id": 42, "price": 1500, "currency": "EUR"}]}, observed_at=observed)
    assert len(result) == 1
    assert result[0].source == "lardi-trans"
    assert result[0].external_ref == "42"
    assert result[0].observed_at == observed
    assert result[0].payload["price"] == 1500


def test_normalization_hashes_items_without_provider_id():
    item = {"cargo": "general", "weight": 10000}
    first = normalize_lardi_response([item], observed_at=datetime(2026, 9, 10, tzinfo=timezone.utc))[0]
    second = normalize_lardi_response([item], observed_at=datetime(2026, 9, 11, tzinfo=timezone.utc))[0]
    assert first.external_ref == second.external_ref
    assert len(first.external_ref) == 64
    assert first.external_ref == stable_external_ref(item, source="lardi-trans")


def test_verified_field_extraction_never_invents_fields():
    item = {"origin": "Kyiv", "destination": "Lviv", "weight": 10000, "secret": "ignore"}
    assert extract_verified_fields(item, verified_fields={"origin", "destination", "price"}) == {
        "origin": "Kyiv", "destination": "Lviv"
    }


def test_price_summary_is_deterministic():
    observations = [
        MarketObservation("lardi-trans", "1", datetime.now(timezone.utc), {"price": "1000", "currency": "EUR"}),
        MarketObservation("lardi-trans", "2", datetime.now(timezone.utc), {"offered_price": 1500, "currency": "EUR"}),
        MarketObservation("lardi-trans", "3", datetime.now(timezone.utc), {"price": {"amount": "2000", "currency": "EUR"}}),
    ]
    snapshot = summarize_prices(observations)
    assert snapshot.count == 3
    assert snapshot.currency == "EUR"
    assert snapshot.median_price == 1500
    assert snapshot.minimum_price == 1000
    assert snapshot.maximum_price == 2000
