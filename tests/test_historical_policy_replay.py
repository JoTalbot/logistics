from datetime import datetime, timezone
from uuid import UUID

import pytest

from logistics.historical_policy_replay import aggregate_historical_policy_replay, load_historical_policy_cases


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.sql = ""
        self.params = None

    def execute(self, sql, params):
        self.sql = sql
        self.params = params
        return FakeCursor(self.rows)


def _rows():
    created = datetime(2026, 9, 11, tzinfo=timezone.utc)
    return [
        ("v21.1", "AUTO", "SUCCESS", "ignored", created),
        ("v21.1", "AUTO", "FAILURE", "ignored", created),
        ("v21.2", "REVIEW", "UNKNOWN", "ignored", created),
    ]


def test_load_historical_policy_cases_is_tenant_scoped_and_read_only():
    tenant_id = UUID("11111111-1111-1111-1111-111111111111")
    conn = FakeConnection(_rows())

    cases = load_historical_policy_cases(conn, tenant_id=tenant_id, limit=50)

    assert len(cases) == 3
    assert cases[0][0] == "v21.1"
    assert cases[0][1].outcome.value == "SUCCESS"
    assert "WHERE d.tenant_id = %s" in conn.sql
    assert conn.params == (tenant_id, 50)
    assert "INSERT" not in conn.sql.upper()
    assert "UPDATE" not in conn.sql.upper()
    assert "DELETE" not in conn.sql.upper()


def test_aggregate_historical_policy_replay_groups_by_policy_version():
    tenant_id = UUID("11111111-1111-1111-1111-111111111111")
    result = aggregate_historical_policy_replay(FakeConnection(_rows()), tenant_id=tenant_id)

    assert result.tenant_id == tenant_id
    assert [report.policy_version for report in result.reports] == ["v21.1", "v21.2"]
    assert result.reports[0].report.cases == 2
    assert result.reports[0].report.failed_auto_cases == 1
    assert result.reports[0].report.auto_failure_rate == 0.5
    assert result.reports[1].report.review_or_higher_cases == 1


def test_historical_policy_replay_limit_is_bounded():
    with pytest.raises(ValueError):
        load_historical_policy_cases(
            FakeConnection([]),
            tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
            limit=100001,
        )
