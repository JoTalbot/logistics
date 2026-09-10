from datetime import datetime, timezone
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
