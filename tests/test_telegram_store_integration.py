from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import psycopg
import pytest

from logistics.telegram import ParsedLoadAd, TelegramSourceMessage
from logistics.telegram_store import TelegramIngestionStore


@pytest.fixture
def db_dsn() -> str:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


@pytest.fixture
def tenant_id(db_dsn: str):
    tenant_id = uuid4()
    with psycopg.connect(db_dsn) as conn:
        conn.execute("INSERT INTO tenants(id, name) VALUES (%s, %s)", (tenant_id, "telegram-test"))
        conn.commit()
    return tenant_id


def make_message(message_id: int = 1) -> TelegramSourceMessage:
    return TelegramSourceMessage(
        chat="https://t.me/example",
        message_id=message_id,
        message_url=f"https://t.me/example/{message_id}",
        published_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        text="Київ → Львів 20 т зерно ставка: 1200 EUR",
    )


def make_ad(message_id: int = 1, *, price: str = "1200") -> ParsedLoadAd:
    return ParsedLoadAd(
        source_chat="https://t.me/example",
        source_message_id=message_id,
        published_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        raw_text="Київ → Львів 20 т зерно ставка: 1200 EUR",
        origin="Київ",
        destination="Львів",
        cargo_type="зерно",
        weight_kg=20_000,
        price=Decimal(price),
        currency="EUR",
        confidence=1.0,
    )


def query_counts(dsn: str, tenant_id, source_message_id):
    with psycopg.connect(dsn) as conn:
        return (
            conn.execute("SELECT count(*) FROM loads WHERE tenant_id=%s", (tenant_id,)).fetchone()[0],
            conn.execute("SELECT count(*) FROM load_stops ls JOIN loads l ON l.id=ls.load_id WHERE l.tenant_id=%s", (tenant_id,)).fetchone()[0],
            conn.execute("SELECT count(*) FROM outbox_events WHERE tenant_id=%s", (tenant_id,)).fetchone()[0],
            conn.execute("SELECT count(*) FROM outbox_events WHERE tenant_id=%s AND payload->>'source_message_id'=%s", (tenant_id, str(source_message_id))).fetchone()[0],
        )


def test_accepted_ad_creates_canonical_load_stops_and_found_event(db_dsn, tenant_id):
    store = TelegramIngestionStore(db_dsn)
    result = store.ingest_message(tenant_id, make_message(), make_ad())

    assert result.accepted is True
    assert result.event_type == "LOAD_FOUND"
    assert result.load_id is not None
    assert query_counts(db_dsn, tenant_id, result.source_message_id) == (1, 2, 1, 1)


def test_duplicate_message_is_idempotent(db_dsn, tenant_id):
    store = TelegramIngestionStore(db_dsn)
    first = store.ingest_message(tenant_id, make_message(), make_ad())
    second = store.ingest_message(tenant_id, make_message(), make_ad())

    assert first.load_id == second.load_id
    assert second.duplicate is True
    assert second.event_type is None
    assert query_counts(db_dsn, tenant_id, first.source_message_id) == (1, 2, 1, 1)


def test_changed_ad_updates_same_load_and_emits_update_event(db_dsn, tenant_id):
    store = TelegramIngestionStore(db_dsn)
    first = store.ingest_message(tenant_id, make_message(), make_ad(price="1200"))
    second = store.ingest_message(tenant_id, make_message(), make_ad(price="1300"))

    assert first.load_id == second.load_id
    assert second.event_type == "LOAD_UPDATED"
    with psycopg.connect(db_dsn) as conn:
        assert conn.execute("SELECT offered_price FROM loads WHERE id=%s", (first.load_id,)).fetchone()[0] == Decimal("1300.00")
        assert conn.execute("SELECT count(*) FROM outbox_events WHERE aggregate_id=%s", (first.load_id,)).fetchone()[0] == 2


def test_rejected_ad_does_not_create_canonical_state(db_dsn, tenant_id):
    store = TelegramIngestionStore(db_dsn)
    message = make_message(2)
    rejected = make_ad(2)
    rejected.price = None

    result = store.ingest_message(tenant_id, message, rejected)

    assert result.accepted is False
    assert result.load_id is None
    assert result.event_type is None
    assert query_counts(db_dsn, tenant_id, result.source_message_id) == (0, 0, 0, 0)
