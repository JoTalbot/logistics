from __future__ import annotations

import hashlib
import threading
import time
from uuid import UUID

import psycopg
import pytest
from fastapi.testclient import TestClient

from backend.logistics.api import app, _dsn


@pytest.mark.integration
def test_next_task_rechecks_credential_after_agent_row_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A stale credential cannot acquire a lease after a committed generation change."""
    monkeypatch.setenv("REMOTE_AGENT_TOKEN", "bootstrap-test-token")
    monkeypatch.setenv("CONTROL_PLANE_OPERATOR_TOKEN", "operator-test-token")

    client = TestClient(app)
    agent_name = "lock-fencing-test-agent"
    enrolled = client.post(
        "/api/v1/control/agents/heartbeat",
        headers={"Authorization": "Bearer bootstrap-test-token"},
        json={"name": agent_name},
    )
    assert enrolled.status_code == 200
    enrollment = enrolled.json()
    agent_id = UUID(enrollment["agent_id"])
    old_token = enrollment["control_token"]

    task = client.post(
        "/api/v1/control/tasks",
        headers={"Authorization": "Bearer operator-test-token"},
        json={"agent_id": str(agent_id), "command": "date"},
    )
    assert task.status_code == 200
    task_id = UUID(task.json()["task_id"])

    with psycopg.connect(_dsn()) as blocker:
        blocker.execute("SELECT id FROM remote_agents WHERE id=%s FOR UPDATE", (agent_id,))

        result: dict[str, object] = {}
        started = threading.Event()

        def poll() -> None:
            started.set()
            response = client.get(
                f"/api/v1/control/agents/{agent_id}/tasks/next",
                headers={"Authorization": f"Bearer {old_token}"},
            )
            result["status"] = response.status_code
            result["body"] = response.json()

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
                        WHERE query ILIKE '%FROM remote_agents WHERE id=% FOR UPDATE%'
                          AND wait_event_type = 'Lock'
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

    assert result["status"] == 401
    assert result["body"] == {"detail": "agent credential invalid"}

    with psycopg.connect(_dsn()) as verify:
        row = verify.execute(
            "SELECT status,lease_credential_generation,credential_generation FROM remote_tasks t JOIN remote_agents a ON a.id=t.agent_id WHERE t.id=%s",
            (task_id,),
        ).fetchone()
        assert row is not None
        assert row[0] == "queued"
        assert row[1] is None
        assert row[2] > 1
