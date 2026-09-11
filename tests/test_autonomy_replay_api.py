from uuid import UUID

import pytest

import logistics.review_extensions as extensions


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
        return self

    def fetchall(self):
        return self.rows


def test_autonomy_replay_endpoint_is_authenticated_and_tenant_scoped(monkeypatch):
    calls = []
    tenant_id = UUID("11111111-1111-1111-1111-111111111111")
    monkeypatch.setattr(extensions, "_operator_auth", lambda token: calls.append(token))
    monkeypatch.setattr(
        extensions.psycopg,
        "connect",
        lambda dsn: FakeConn([
            ("v21.1", "AUTO", "SUCCESS"),
            ("v21.1", "AUTO", "FAILURE"),
        ]),
    )

    result = extensions.review_autonomy_replay(
        tenant_id=tenant_id,
        limit=25,
        x_operator_token="secret",
    )

    assert calls == ["secret"]
    assert result["tenant_id"] == str(tenant_id)
    assert result["reports"][0]["policy_version"] == "v21.1"
    assert result["reports"][0]["report"]["failed_auto_cases"] == 1
    assert result["reports"][0]["report"]["auto_failure_rate"] == 0.5


def test_autonomy_replay_endpoint_rejects_invalid_limit(monkeypatch):
    monkeypatch.setattr(extensions, "_operator_auth", lambda token: None)
    with pytest.raises(extensions.HTTPException) as exc:
        extensions.review_autonomy_replay(
            tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
            limit=100001,
            x_operator_token="secret",
        )
    assert exc.value.status_code == 422
