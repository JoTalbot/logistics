from datetime import datetime
from uuid import UUID

import pytest

import logistics.review_extensions as extensions


class FakeConn:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        assert "autonomy_decisions" in sql
        assert "tenant_id=%s" in sql
        assert params[0] == UUID("11111111-1111-1111-1111-111111111111")
        return self

    def fetchall(self):
        return self.rows


def test_autonomy_exception_route_is_registered():
    routes = {
        route.path
        for route in extensions.app.routes
        if hasattr(route, "methods") and "GET" in route.methods
    }
    assert "/api/v1/review/autonomy-exceptions" in routes


def test_autonomy_exception_endpoint_is_authenticated_and_tenant_scoped(monkeypatch):
    calls = []
    monkeypatch.setattr(extensions, "_operator_auth", lambda token: calls.append(token))
    monkeypatch.setattr(
        extensions.psycopg,
        "connect",
        lambda dsn: FakeConn([
            (
                "d-1", "corr-1", "publish_listing", 0.82, "REVIEW", "SHADOW",
                "v21.1", "needs review", datetime(2026, 9, 11),
            )
        ]),
    )

    result = extensions.review_autonomy_exceptions(
        tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
        limit=10,
        x_operator_token="secret",
    )

    assert calls == ["secret"]
    assert result[0]["decision_id"] == "d-1"
    assert result[0]["tier"] == "REVIEW"


def test_autonomy_exception_endpoint_rejects_invalid_limit(monkeypatch):
    monkeypatch.setattr(extensions, "_operator_auth", lambda token: None)
    with pytest.raises(extensions.HTTPException) as exc:
        extensions.review_autonomy_exceptions(
            tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
            limit=0,
            x_operator_token="secret",
        )
    assert exc.value.status_code == 422
