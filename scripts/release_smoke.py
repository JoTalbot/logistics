"""Fail-closed release smoke checks using only local/fake dependencies."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import psycopg
from fastapi import HTTPException

from logistics import api


class _Cursor:
    def __init__(self, rows):
        self._rows = iter(rows)

    def fetchone(self):
        return next(self._rows)

    def fetchall(self):
        return list(self._rows)


class _Conn:
    def __init__(self):
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, *_args, **_kwargs):
        self.calls += 1
        if self.calls == 1:
            return _Cursor([("approve", 1)])
        if self.calls == 2:
            return _Cursor([(datetime.now(timezone.utc), "approve", 1)])
        return _Cursor([(0, 0.0, 0.0)])


def main() -> None:
    os.environ["REVIEW_OPERATOR_TOKEN"] = "smoke-secret"
    os.environ["DATABASE_URL"] = "postgresql://smoke"

    assert api.health()["status"] == "ok"

    with patch("logistics.api.psycopg.connect", side_effect=psycopg.OperationalError("database down")):
        try:
            api.readiness()
        except HTTPException as exc:
            assert exc.status_code == 503
        else:
            raise AssertionError("unexpected readiness success with broken database")

    try:
        api.review_metrics(uuid4(), x_operator_token="wrong")
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("invalid operator token was accepted")

    tenant_id = uuid4()
    conn = _Conn()
    with patch("logistics.api.psycopg.connect", return_value=conn):
        report = api.review_audit_report(tenant_id, days=30, x_operator_token="smoke-secret")
    assert report["tenant_id"] == str(tenant_id)
    assert report["decisions"] == {"approve": 1}
    assert report["queue_age"]["pending_total"] == 0

    print("release smoke: PASS")


if __name__ == "__main__":
    main()
