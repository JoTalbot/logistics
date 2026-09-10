from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest

from logistics.customer_opportunity_store import list_customer_opportunities
from logistics.prospect_store import list_prospects
from logistics.recurring_demand_store import list_patterns
from logistics.contact_outbox import list_contact_intents
from logistics.duplicate_loads import find_duplicate_load_groups


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
    return conn.execute("INSERT INTO tenants(name) VALUES (%s) RETURNING id", (f"integration-{uuid4()}",)).fetchone()[0]


def test_tenant_scoped_review_stores_do_not_cross_read(db_conn):
    tenant_a = _tenant(db_conn)
    tenant_b = _tenant(db_conn)
    db_conn.commit()

    assert list_prospects(db_conn, tenant_id=tenant_a, limit=100) == []
    assert list_prospects(db_conn, tenant_id=tenant_b, limit=100) == []
    assert list_customer_opportunities(db_conn, tenant_id=tenant_a, status="candidate", limit=100) == []
    assert list_customer_opportunities(db_conn, tenant_id=tenant_b, status="candidate", limit=100) == []
    assert list_patterns(db_conn, tenant_id=tenant_a, status="active", limit=100) == []
    assert list_patterns(db_conn, tenant_id=tenant_b, status="active", limit=100) == []
    assert list_contact_intents(db_conn, tenant_id=tenant_a, status="pending", limit=100) == []
    assert list_contact_intents(db_conn, tenant_id=tenant_b, status="pending", limit=100) == []


def test_duplicate_detection_is_tenant_scoped(db_conn):
    tenant_a = _tenant(db_conn)
    tenant_b = _tenant(db_conn)
    load_a = db_conn.execute(
        """INSERT INTO loads(tenant_id, cargo_type, weight_kg, offered_price, currency, status)
           VALUES (%s,'food',1000,1200,'EUR','new') RETURNING id""", (tenant_a,)
    ).fetchone()[0]
    load_b = db_conn.execute(
        """INSERT INTO loads(tenant_id, cargo_type, weight_kg, offered_price, currency, status)
           VALUES (%s,'food',1000,1300,'EUR','new') RETURNING id""", (tenant_b,)
    ).fetchone()[0]
    for load_id in (load_a, load_b):
        db_conn.execute(
            """INSERT INTO load_stops(load_id, sequence, kind, raw_address, normalized_address)
               VALUES (%s,0,'pickup','Kyiv','Kyiv'),(%s,1,'delivery','Warsaw','Warsaw')""",
            (load_id, load_id),
        )
    db_conn.commit()

    assert find_duplicate_load_groups(db_conn, tenant_id=tenant_a) == []
    assert find_duplicate_load_groups(db_conn, tenant_id=tenant_b) == []
    db_conn.execute("DELETE FROM loads WHERE id IN (%s,%s)", (load_a, load_b))
    db_conn.commit()
