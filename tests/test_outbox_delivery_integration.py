import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from logistics.outbox_delivery import PostgresOutboxDelivery


@pytest.fixture
def db_dsn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


def seed_event(dsn):
    tenant_id = uuid4()
    event_id = uuid4()
    aggregate_id = uuid4()
    with psycopg.connect(dsn) as conn:
        conn.execute("INSERT INTO tenants(id, name) VALUES (%s, %s)", (tenant_id, "outbox-test"))
        conn.execute(
            """
            INSERT INTO outbox_events(
                event_id, tenant_id, event_type, aggregate_type, aggregate_id,
                occurred_at, correlation_id, payload, idempotency_key
            ) VALUES (%s,%s,'TEST_EVENT','load',%s,%s,%s,%s,%s)
            """,
            (event_id, tenant_id, aggregate_id, datetime.now(timezone.utc), uuid4(), '{"ok":true}', str(event_id)),
        )
        conn.commit()
    return event_id


def test_claim_ack_marks_event_published(db_dsn):
    event_id = seed_event(db_dsn)
    worker = PostgresOutboxDelivery(db_dsn, "test-worker")

    claimed = worker.claim(limit=1)
    assert len(claimed) == 1
    assert str(claimed[0]["event_id"]) == str(event_id)
    assert claimed[0]["attempt_count"] == 1

    worker.ack(str(event_id))

    with psycopg.connect(db_dsn) as conn:
        row = conn.execute("SELECT published_at, locked_by FROM outbox_events WHERE event_id=%s", (event_id,)).fetchone()
    assert row[0] is not None
    assert row[1] is None


def test_failed_delivery_is_delayed(db_dsn):
    event_id = seed_event(db_dsn)
    worker = PostgresOutboxDelivery(db_dsn, "test-worker")
    claimed = worker.claim(limit=1)
    worker.fail(str(event_id), claimed[0]["attempt_count"], "temporary failure")

    with psycopg.connect(db_dsn) as conn:
        available_at, locked_by, error = conn.execute(
            "SELECT available_at, locked_by, last_error FROM outbox_events WHERE event_id=%s", (event_id,)
        ).fetchone()
    assert available_at > datetime.now(timezone.utc)
    assert locked_by is None
    assert error == "temporary failure"
