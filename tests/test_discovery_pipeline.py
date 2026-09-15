from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from logistics.discovery_pipeline import build_discovery_report, candidate_digest
from logistics.market_ops import PricingInput
from logistics.telegram import TelegramSourceMessage


def test_discovery_report_normalizes_and_ranks_valid_ads():
    tenant_id = uuid4()
    messages = [
        TelegramSourceMessage(
            chat="https://t.me/test",
            message_id=1,
            published_at=datetime.now(timezone.utc),
            text="Киев → Львов\nГруз: мебель\n20 т\nСтавка: 500 EUR",
        )
    ]
    pricing = PricingInput(distance_km=Decimal("500"))

    report = build_discovery_report(messages, [], pricing, tenant_id=tenant_id)

    assert report.accepted_count == 1
    assert report.rejected_count == 0
    assert len(report.candidates) == 1
    candidate = report.candidates[0]
    digest = candidate_digest(candidate)
    assert digest["origin"] == "Киев"
    assert digest["destination"] == "Львов"
    assert digest["cargo_type"] == "мебель"
    assert digest["weight_kg"] == 20000
    assert digest["offered_price"] == "500"
    assert digest["currency"] == "EUR"
    assert digest["estimated_price"] == "0.00"
    assert "priority_score" in digest


def test_discovery_report_rejects_incomplete_ads_fail_closed():
    tenant_id = uuid4()
    message = TelegramSourceMessage(
        chat="https://t.me/test",
        message_id=2,
        published_at=datetime.now(timezone.utc),
        text="Киев → Львов\nГруз: мебель",
    )

    report = build_discovery_report(
        [message], [], PricingInput(distance_km=Decimal("500")), tenant_id=tenant_id
    )

    assert report.accepted_count == 0
    assert report.rejected_count == 1
    assert report.items[0].load is None
    assert "missing_weight" in report.items[0].validation.reasons
    assert "missing_price" in report.items[0].validation.reasons
