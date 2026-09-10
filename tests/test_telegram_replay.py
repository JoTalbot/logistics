from __future__ import annotations

import json
from pathlib import Path

from logistics.telegram import TelegramSourceMessage, parse_load_ad
from logistics.telegram_pipeline import parsed_ad_to_load, validate_parsed_ad


FIXTURE = Path(__file__).parent / "fixtures" / "telegram" / "replay_messages.json"


def test_telegram_replay_fixture_is_deterministic():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    messages = [TelegramSourceMessage.model_validate(item) for item in raw]
    parsed = [parse_load_ad(message) for message in messages]

    first = parsed[0]
    assert first.origin == "Київ"
    assert first.destination == "Львів"
    assert first.weight_kg == 20_000
    assert str(first.price) == "1200"
    assert first.currency == "EUR"
    assert first.confidence == 1.0

    second = parsed[1]
    assert second.origin == "Одеса"
    assert second.destination == "Краків"
    assert second.weight_kg == 22_000
    assert str(second.price) == "1800"

    third = parsed[2]
    assert not validate_parsed_ad(third).accepted


def test_telegram_replay_fixture_canonical_shape_is_stable():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    message = TelegramSourceMessage.model_validate(raw[0])
    parsed = parse_load_ad(message)
    load = parsed_ad_to_load(parsed, tenant_id="00000000-0000-0000-0000-000000000001")

    assert load.external_ref == "telegram:https://t.me/example:1001"
    assert load.status.value == "normalized"
    assert [(stop.sequence, stop.kind, stop.location.normalized_address) for stop in load.stops] == [
        (0, "pickup", "Київ"),
        (1, "delivery", "Львів"),
    ]
