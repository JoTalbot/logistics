from datetime import datetime, timezone

import pytest

from logistics.recurring_demand_health import finish_run, scheduler_health, start_run


class FakeResult:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConn:
    def __init__(self):
        self.calls = []
        self.next_row = ("run-1",)
        self.health_row = None

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if "RETURNING id" in sql:
            return FakeResult(self.next_row)
        if "ORDER BY started_at DESC" in sql:
            return FakeResult(self.health_row)
        return FakeResult(None)


def test_start_run_persists_running_state():
    conn = FakeConn()
    run_id = start_run(conn, started_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert run_id == "run-1"
    assert "recurring_demand_runs" in conn.calls[0][0]
    assert "running" in conn.calls[0][0]


def test_finish_run_validates_status_and_counts():
    conn = FakeConn()
    finish_run(conn, run_id="run-1", completed_at=datetime.now(timezone.utc), status="succeeded", tenant_count=2, pattern_count=4)
    assert "UPDATE recurring_demand_runs" in conn.calls[0][0]


def test_scheduler_health_is_never_run_when_empty():
    conn = FakeConn()
    result = scheduler_health(conn)
    assert result["status"] == "never_run"
    assert result["operational_status"] == "critical"
    assert result["last_run"] is None


def test_scheduler_health_returns_healthy_run():
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    completed = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)
    conn = FakeConn()
    conn.health_row = ("run-1", started, completed, "succeeded", 2, 4, None)
    result = scheduler_health(conn, now=datetime(2026, 1, 1, 6, tzinfo=timezone.utc))
    assert result["status"] == "succeeded"
    assert result["operational_status"] == "healthy"
    assert result["last_run"]["tenant_count"] == 2
    assert result["last_run"]["pattern_count"] == 4
    assert result["last_run"]["age_seconds"] == 21600


def test_scheduler_health_marks_old_success_stale():
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    conn = FakeConn()
    conn.health_row = ("run-1", started, started, "succeeded", 1, 2, None)
    result = scheduler_health(conn, now=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    assert result["operational_status"] == "stale"


def test_scheduler_health_marks_long_running_stale():
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    conn = FakeConn()
    conn.health_row = ("run-1", started, None, "running", 1, 0, None)
    result = scheduler_health(conn, now=datetime(2026, 1, 1, 2, tzinfo=timezone.utc))
    assert result["operational_status"] == "stale"


def test_scheduler_health_marks_failed_run_failed():
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    conn = FakeConn()
    conn.health_row = ("run-1", started, started, "failed", 1, 0, "boom")
    result = scheduler_health(conn, now=datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc))
    assert result["operational_status"] == "failed"


def test_scheduler_health_rejects_invalid_thresholds():
    with pytest.raises(ValueError):
        scheduler_health(FakeConn(), stale_after_hours=0)
    with pytest.raises(ValueError):
        scheduler_health(FakeConn(), running_timeout_hours=0)
