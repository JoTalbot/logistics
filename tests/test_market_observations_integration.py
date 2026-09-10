import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import psycopg
import pytest

from logistics.market_observations import MarketObservation, upsert_market_observations


@pytest.fixture
def db_dsn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


def test_market_observation_history_is_idempotent_and_current_state_is_fresh(db_dsn):
    tenant_id = uuid4()
    newest = datetime.now(timezone.utc)
    older = newest - timedelta(hours=1)
    with psycopg.connect(db_dsn) as conn:
        conn.execute("INSERT INTO tenants(id, name) VALUES (%s, %s)", (tenant_id, "market-observation-test"))
        first = MarketObservation("lardi-trans", "proposal-1", newest, {"price": 1500, "currency": "EUR"})
        assert upsert_market_observations(conn, str(tenant_id), [first]) == 1
        assert upsert_market_observations(conn, str(tenant_id), [first]) == 1
        stale = MarketObservation("lardi-trans", "proposal-1", older, {"price": 900, "currency": "EUR"})
        assert upsert_market_observations(conn, str(tenant_id), [stale]) == 0
        conn.commit()
        current = conn.execute(
            "SELECT observed_at, payload->>'price' FROM market_observations WHERE tenant_id=%s AND external_ref='proposal-1'",
            (tenant_id,),
        ).fetchone()
        history_count = conn.execute(
            "SELECT count(*) FROM market_observation_history WHERE tenant_id=%s AND external_ref='proposal-1'",
            (tenant_id,),
        ).fetchone()[0]
    assert current[0] == newest
    assert current[1] == "1500"
    assert history_count == 2
