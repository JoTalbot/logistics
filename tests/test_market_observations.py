from datetime import datetime, timezone

from logistics.market_observations import normalize_lardi_response


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
