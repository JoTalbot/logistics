from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from logistics import api


class FakeCursor:
    def __init__(self, rows):
        self.rows = iter(rows)

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return next(self.rows)


class FakeConnection:
    def __init__(self, results):
        self.results = iter(results)
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return FakeCursor(next(self.results))


def test_recommendations_require_operator_token(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    with pytest.raises(Exception) as exc:
        api.review_recommendations(uuid4(), x_operator_token="wrong")
    assert getattr(exc.value, "status_code", None) == 401


def test_review_recommendations_expose_persisted_fields(monkeypatch):
    tenant_id = uuid4()
    opportunity_id = uuid4()
    load_id = uuid4()
    updated = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)
    created = datetime(2026, 9, 9, 10, 0, tzinfo=timezone.utc)
    conn = FakeConnection([
        [(
            opportunity_id,
            load_id,
            "candidate",
            0.91,
            800,
            400,
            350,
            1300,
            1250,
            ["risk_adjusted_profit", "market_median"],
            updated,
            created,
        )]
    ])
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    with patch("logistics.api.psycopg.connect", return_value=conn):
        result = api.review_recommendations(tenant_id, x_operator_token="secret")
    assert result[0]["id"] == str(opportunity_id)
    assert result[0]["recommended_price"] == 1300.0
    assert result[0]["recommendation_reasons"] == ["risk_adjusted_profit", "market_median"]


def test_audit_report_returns_decision_trend_and_queue_age(monkeypatch):
    tenant_id = uuid4()
    day = datetime(2026, 9, 10, tzinfo=timezone.utc)
    conn = FakeConnection([
        [("approve", 3), ("reject", 1)],
        [(day, "approve", 2), (day, "reject", 1)],
        [(4, 7200.0, 1800.0)],
    ])
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example")
    with patch("logistics.api.psycopg.connect", return_value=conn):
        result = api.review_audit_report(tenant_id, days=30, x_operator_token="secret")
    assert result["decisions"] == {"approve": 3, "reject": 1}
    assert result["daily_trend"] == [
        {"day": "2026-09-10", "decision": "approve", "count": 2},
        {"day": "2026-09-10", "decision": "reject", "count": 1},
    ]
    assert result["queue_age"] == {
        "pending_total": 4,
        "oldest_seconds": 7200,
        "average_age_seconds": 1800,
    }


def test_reporting_validates_bounds(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    with pytest.raises(Exception) as exc:
        api.review_audit_report(uuid4(), days=0, x_operator_token="secret")
    assert getattr(exc.value, "status_code", None) == 422
