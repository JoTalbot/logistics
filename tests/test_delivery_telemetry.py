from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from logistics.delivery_telemetry import finish_attempt, record_attempt


def test_record_attempt_is_idempotent():
    conn = MagicMock()
    started = datetime(2026, 9, 10, tzinfo=timezone.utc)
    record_attempt(
        conn,
        event_id="event-1",
        tenant_id="tenant-1",
        attempt_number=2,
        worker_id="worker-1",
        started_at=started,
    )
    sql, params = conn.execute.call_args.args
    assert "ON CONFLICT (event_id, attempt_number) DO NOTHING" in sql
    assert params == ("event-1", "tenant-1", 2, "worker-1", started)


def test_record_attempt_rejects_invalid_attempt():
    with pytest.raises(ValueError, match="positive"):
        record_attempt(MagicMock(), event_id="e", tenant_id="t", attempt_number=0, worker_id="w")


def test_finish_attempt_records_success():
    conn = MagicMock()
    finished = datetime(2026, 9, 10, 1, tzinfo=timezone.utc)
    finish_attempt(conn, event_id="event-1", attempt_number=1, outcome="succeeded", finished_at=finished)
    sql, params = conn.execute.call_args.args
    assert "UPDATE outbox_delivery_attempts" in sql
    assert params == (finished, "succeeded", None, "event-1", 1)


def test_finish_attempt_truncates_error_and_rejects_running():
    conn = MagicMock()
    finish_attempt(conn, event_id="e", attempt_number=1, outcome="failed", error_text="x" * 5000)
    assert len(conn.execute.call_args.args[1][2]) == 4000
    with pytest.raises(ValueError, match="succeeded or failed"):
        finish_attempt(conn, event_id="e", attempt_number=1, outcome="running")
