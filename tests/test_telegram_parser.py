from datetime import datetime, timezone
from decimal import Decimal

from logistics.telegram import TelegramSourceMessage, parse_load_ad


def message(text: str) -> TelegramSourceMessage:
    return TelegramSourceMessage(
        chat="https://t.me/truck_world",
        message_id=123,
        message_url="https://t.me/truck_world/123",
        published_at=datetime.now(timezone.utc),
        text=text,
    )


def test_parses_ukrainian_route_weight_price_and_phone():
    parsed = parse_load_ad(message("Киев → Варшава\nтент 20 т\nставка 1200 €\n+380 67 123 45 67"))
    assert parsed.origin == "Киев"
    assert parsed.destination == "Варшава"
    assert parsed.weight_kg == 20_000
    assert parsed.price == Decimal("1200")
    assert parsed.currency == "EUR"
    assert parsed.phone_numbers
    assert parsed.confidence >= 0.8


def test_parses_volume_and_ua_currency():
    parsed = parse_load_ad(message("Львов → Краков\n22 м3\n850 грн"))
    assert parsed.origin == "Львов"
    assert parsed.destination == "Краков"
    assert parsed.volume_m3 == 22
    assert parsed.currency == "UAH"


def test_keeps_raw_message_when_fields_are_missing():
    parsed = parse_load_ad(message("Нужна машина завтра, подробности в ЛС"))
    assert parsed.raw_text.startswith("Нужна машина")
    assert parsed.origin is None
    assert parsed.destination is None
    assert parsed.confidence == 0.2
