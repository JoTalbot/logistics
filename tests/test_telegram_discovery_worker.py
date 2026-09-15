import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from logistics.market_ops import PricingInput
from logistics.telegram import TelegramSourceMessage, parse_load_ad
from logistics.telegram_discovery_worker import run_ingestion_discovery_once
from logistics.telegram_store import IngestionResult


class FakeStore:
    def __init__(self):
        self.calls = []

    def get_checkpoints(self, tenant_id, chats):
        return {}

    def ingest_message(self, tenant_id, message, parsed, *, min_confidence=0.6):
        self.calls.append((tenant_id, message, parsed, min_confidence))
        return IngestionResult(
            source_message_id=uuid4(),
            load_id=uuid4(),
            accepted=True,
            duplicate=False,
            event_type="LOAD_FOUND",
        )


def test_ingestion_discovery_persists_messages_before_ranking(monkeypatch):
    message = TelegramSourceMessage(
        chat="https://t.me/test",
        message_id=101,
        published_at=datetime.now(timezone.utc),
        text="Киев → Львов\nГруз: мебель\n20 т\nСтавка: 500 EUR",
    )
    tenant_id = uuid4()
    store = FakeStore()

    async def fake_collect_messages(client, chats, *, limit, min_id_by_chat):
        assert chats == ("https://t.me/test",)
        assert limit == 10
        assert min_id_by_chat == {}
        yield message

    monkeypatch.setattr(
        "logistics.telegram_discovery_worker.collect_messages", fake_collect_messages
    )

    result = asyncio.run(
        run_ingestion_discovery_once(
            object(),
            store,
            tenant_id,
            ["https://t.me/test"],
            [],
            PricingInput(distance_km=Decimal("500")),
            limit=10,
            min_confidence=0.85,
        )
    )

    assert len(store.calls) == 1
    assert store.calls[0][0] == tenant_id
    assert store.calls[0][1] == message
    assert store.calls[0][2] == parse_load_ad(message)
    assert store.calls[0][3] == 0.85
    assert len(result.processed) == 1
    assert result.report.accepted_count == 1
    assert len(result.candidates) == 1
    assert result.candidates[0].load.external_ref == "telegram:https://t.me/test:101"


def test_ingestion_discovery_returns_empty_evidence_for_empty_batch(monkeypatch):
    async def empty_collect_messages(client, chats, *, limit, min_id_by_chat):
        if False:
            yield None

    monkeypatch.setattr(
        "logistics.telegram_discovery_worker.collect_messages", empty_collect_messages
    )

    result = asyncio.run(
        run_ingestion_discovery_once(
            object(),
            FakeStore(),
            uuid4(),
            ["https://t.me/test"],
            [],
            PricingInput(distance_km=Decimal("500")),
        )
    )

    assert result.processed == ()
    assert result.report.items == ()
    assert result.candidates == ()
