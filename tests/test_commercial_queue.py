from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest

import logistics.commercial_queue as queue

TENANT = UUID("11111111-1111-1111-1111-111111111111")


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConn:
    def __init__(self, rows):
        self.rows = rows
        self.sql = ""
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        self.sql = sql
        self.params = params
        return FakeResult(self.rows)


class FakePsycopg:
    def __init__(self, conn):
        self.conn = conn

    def connect(self, dsn):
        return self.conn


def _row(priority: float, load_id: str):
    return (
        UUID(load_id),
        UUID(load_id),
        "ext-1",
        "general cargo",
        1000,
        "150000.00",
        "UAH",
        0.82,
        "100000.00",
        "50000.00",
        "45000.00",
        ["positive_risk_adjusted_margin"],
        priority,
        ["carrier_match_available"],
        "candidate",
        datetime(2026, 9, 12, tzinfo=timezone.utc),
    )


def test_queue_is_authenticated_tenant_scoped_and_ordered(monkeypatch):
    calls = []
    conn = FakeConn([
        _row(0.95, "22222222-2222-2222-2222-222222222222"),
        _row(0.80, "33333333-3333-3333-3333-333333333333"),
    ])
    monkeypatch.setattr(queue, "_operator_auth", lambda token: calls.append(token))
    monkeypatch.setattr(queue, "_dsn", lambda: "postgresql://test")
    monkeypatch.setattr(queue, "psycopg", FakePsycopg(conn))

    result = queue.review_commercial_opportunities(
        tenant_id=TENANT,
        status="candidate",
        min_priority=0.8,
        limit=10,
        x_operator_token="secret",
    )

    assert calls == ["secret"]
    assert conn.params == (TENANT, "candidate", 0.8, 10)
    assert "o.tenant_id=%s" in conn.sql
    assert result[0]["priority_score"] == 0.95
    assert result[0]["estimated_margin"] == "50000.00"
    assert result[0]["risk_adjusted_margin"] == "45000.00"


def test_queue_validates_filters(monkeypatch):
    monkeypatch.setattr(queue, "_operator_auth", lambda token: None)
    with pytest.raises(queue.HTTPException) as exc:
        queue.review_commercial_opportunities(TENANT, status="bad")
    assert exc.value.status_code == 422

    with pytest.raises(queue.HTTPException) as exc:
        queue.review_commercial_opportunities(TENANT, min_priority=1.1)
    assert exc.value.status_code == 422

    with pytest.raises(queue.HTTPException) as exc:
        queue.review_commercial_opportunities(TENANT, limit=0)
    assert exc.value.status_code == 422


def test_queue_route_is_registered():
    routes = {route.path for route in queue.app.routes if hasattr(route, "methods") and "GET" in route.methods}
    assert "/api/v1/review/commercial-opportunities" in routes
