from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from logistics.outbox_delivery import PostgresOutboxDelivery


@pytest.fixture()
def db_conn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")
    dsn = dsn.replace("postgresql+psycopg://", "postgresql://", 1)
    try:
        conn = psycopg.connect(dsn)
    except psycopg.Error as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    try:
        yield conn
    finally:
        conn.close()


def _tenant(conn):
    return conn.execute(
        "INSERT INTO tenants(name) VALUES (%s) RETURNING id",
        (f"outbox-recovery-{uuid4()}",),
    ).fetchone()[0]


def _event(conn, tenant_id):
    event_id = uuid4()
    aggregate_id = uuid4()
    occurred_at = datetime.now(timezone.utc)
    conn.execute(
        """
        INSERT INTO outbox_events(
            event_id, tenant_id, event_type, aggregate_type, aggregate_id,
            schema_version, occurred_at, correlation_id, payload
        ) VALUES (%s,%s,'test.delivery','load',%s,1,%s,%s,'{}'::jsonb)
        """,
        (event_id, tenant_id, aggregate_id, occurred_at, uuid4()),
    )
    return event_id


def test_postgres_outbox_replay_records_distinct_attempts_and_preserves_event(db_conn):
    tenant = _tenant(db_conn)
    event_id = _event(db_conn, tenant)
    db_conn.commit()

    worker = PostgresOutboxDelivery(os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://"), "recovery-worker")

    first = worker.claim(limit=1)
    assert len(first) == 1
    assert str(first[0]["event_id"]) == str(event_id)
    assert first[0]["attempt_count"] == 1

    db_conn.execute(
        "UPDATE outbox_events SET locked_at = now() - interval '2 minutes' WHERE event_id=%s",
        (event_id,),
    )
    db_conn.commit()

    second = worker.claim(limit=1)
    assert len(second) == 1
    assert str(second[0]["event_id"]) == str(event_id)
    assert second[0]["attempt_count"] == 2

    attempts = db_conn.execute(
        """
        SELECT event_id, tenant_id, attempt_number, worker_id, outcome
        FROM outbox_delivery_attempts
        WHERE event_id=%s ORDER BY attempt_number
        """,
        (event_id,),
    ).fetchall()
    assert [(row[2], row[3], row[4]) for row in attempts] == [
        (1, "recovery-worker", "running"),
        (2, "recovery-worker", "running"),
    ]
    assert all(row[1] == tenant for row in attempts)

    worker.fail(str(event_id), 2, "temporary delivery failure")
    worker.claim(limit=1)  # no claim expected while the retry delay is active

    failed = db_conn.execute(
        "SELECT outcome, error_text FROM outbox_delivery_attempts WHERE event_id=%s AND attempt_number=2",
        (event_id,),
    ).fetchone()
    assert failed == ("failed", "temporary delivery failure")

    row = db_conn.execute(
        "SELECT event_id, tenant_id, attempt_count, published_at FROM outbox_events WHERE event_id=%s",
        (event_id,),
    ).fetchone()
    assert row[0] == event_id
    assert row[1] == tenant
    assert row[2] == 2
    assert row[3] is None

    db_conn.execute("DELETE FROM outbox_events WHERE event_id=%s", (event_id,))
    db_conn.commit()


def test_postgres_outbox_ack_finishes_attempt_without_creating_new_event(db_conn):
    tenant = _tenant(db_conn)
    event_id = _event(db_conn, tenant)
    db_conn.commit()

    dsn = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    worker = PostgresOutboxDelivery(dsn, "ack-worker")
    claimed = worker.claim(limit=1)
    assert claimed and claimed[0]["attempt_count"] == 1

    worker.ack(str(event_id), 1)

    event = db_conn.execute(
        "SELECT event_id, published_at, attempt_count FROM outbox_events WHERE event_id=%s",
        (event_id,),
    ).fetchone()
    attempt = db_conn.execute(
        "SELECT attempt_number, outcome, finished_at FROM outbox_delivery_attempts WHERE event_id=%s",
        (event_id,),
    ).fetchone()
    assert event[0] == event_id
    assert event[1] is not None
    assert event[2] == 1
    assert attempt[0] == 1
    assert attempt[1] == "succeeded"
    assert attempt[2] is not None

    db_conn.execute("DELETE FROM outbox_events WHERE event_id=%s", (event_id,))
    db_conn.commit()
