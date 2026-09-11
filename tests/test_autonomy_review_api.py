from uuid import UUID

from fastapi.testclient import TestClient

from logistics.api import app
import logistics.review_extensions  # noqa: F401


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


def test_autonomy_exception_endpoint_requires_operator(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    client = TestClient(app)
    response = client.get(
        "/api/v1/review/autonomy-exceptions",
        params={"tenant_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 401


def test_autonomy_exception_endpoint_is_authenticated_and_tenant_scoped(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    monkeypatch.setenv("DATABASE_URL", "postgresql://unused")
    import logistics.review_extensions as extensions

    monkeypatch.setattr(
        extensions.psycopg,
        "connect",
        lambda dsn: FakeConn([
            (
                "d-1", "corr-1", "publish_listing", 0.82, "REVIEW", "SHADOW",
                "v21.1", "needs review", __import__("datetime").datetime(2026, 9, 11),
            )
        ]),
    )
    client = TestClient(app)
    response = client.get(
        "/api/v1/review/autonomy-exceptions",
        params={"tenant_id": "11111111-1111-1111-1111-111111111111", "limit": 10},
        headers={"X-Operator-Token": "secret"},
    )
    assert response.status_code == 200
    assert response.json()[0]["decision_id"] == "d-1"
    assert response.json()[0]["tier"] == "REVIEW"


def test_autonomy_exception_endpoint_validates_limit(monkeypatch):
    monkeypatch.setenv("REVIEW_OPERATOR_TOKEN", "secret")
    client = TestClient(app)
    response = client.get(
        "/api/v1/review/autonomy-exceptions",
        params={"tenant_id": "11111111-1111-1111-1111-111111111111", "limit": 0},
        headers={"X-Operator-Token": "secret"},
    )
    assert response.status_code == 422
