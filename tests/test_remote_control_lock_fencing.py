from __future__ import annotations

import hashlib
import threading
import time
from uuid import UUID

import psycopg
import pytest

from backend.logistics.remote_control import AgentHeartbeat, TaskRequest, _dsn
from backend.logistics.remote_control import control_create_task, control_heartbeat, control_next_task


@pytest.mark.integration
def test_next_task_rechecks_credential_after_agent_row_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale credential cannot acquire a lease after a committed generation change."""
    monkeypatch.setenv("REMOTE_AGENT_TOKEN", "bootstrap-test-token")
    monkeypatch.setenv("CONTROL_PLANE_OPERATOR_TOKEN", "operator-test-token")

    enrolled = control_heartbeat(
        AgentHeartbeat(name="lock-fencing-test-agent"),
        "Bearer bootstrap-test-token",
    )
    agent_id = UUID(enrolled["agent_id"])
    old_token = enrolled["control_token"]

    task = control_create_task(
        TaskRequest(agent_id=agent_id, command="date"),
        "Bearer operator-test-token",
    )
    task_id = UUID(task["task_id"])

    with psycopg.connect(_dsn()) as blocker:
        blocker.execute("SELECT id FROM remote_agents WHERE id=%s FOR UPDATE", (agent_id,))

        result: dict[str, object] = {}
        started = threading.Event()

        def poll() -> None:
            started.set()
            try:
                result["value"] = control_next_task(agent_id, f"Bearer {old_token}")
            except Exception as exc:
                result["error"] = exc

        worker = threading.Thread(target=poll, daemon=True)
        worker.start()
        assert started.wait(timeout=5)

        deadline = time.monotonic() + 5
        waiting = False
        while time.monotonic() < deadline:
            with psycopg.connect(_dsn()) as probe:
                row = probe.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM pg_stat_activity
                        WHERE wait_event_type = 'Lock'
                          AND query ILIKE '%FROM remote_agents%'
                          AND query ILIKE '%FOR UPDATE%'
                    )
                    """
                ).fetchone()
            if row and row[0]:
                waiting = True
                break
            time.sleep(0.02)
        assert waiting, "next-task transaction did not wait on the agent row lock"

        new_token = "new-generation-token"
        new_hash = hashlib.sha256(new_token.encode()).hexdigest()
        blocker.execute(
            "UPDATE remote_agents SET credential_hash=%s, credential_generation=credential_generation+1 WHERE id=%s",
            (new_hash, agent_id),
        )
        blocker.commit()

        worker.join(timeout=10)
        assert not worker.is_alive(), "next-task request remained blocked after commit"

    error = result.get("error")
    assert getattr(error, "status_code", None) == 401
    assert getattr(error, "detail", None) == "agent credential invalid"
    assert "value" not in result

    with psycopg.connect(_dsn()) as verify:
        row = verify.execute(
            "SELECT status,lease_credential_generation,credential_generation FROM remote_tasks t JOIN remote_agents a ON a.id=t.agent_id WHERE t.id=%s",
            (task_id,),
        ).fetchone()
        assert row is not None
        assert row[0] == "queued"
        assert row[1] is None
        assert row[2] > 1
