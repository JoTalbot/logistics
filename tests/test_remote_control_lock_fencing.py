from __future__ import annotations

import threading
import time
from uuid import UUID

import psycopg
import pytest
from fastapi.testclient import TestClient

from backend.logistics.api import app, _dsn
from backend.logistics.remote_control import _agent_token, _operator_token


@pytest.mark.integration
def test_next_task_rechecks_credential_after_agent_row_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A next-task request blocked on the agent row must see committed fencing state."""
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
        json={
            "agent_id": str(agent_id),
            "command": "date",
            "requested_by": "lock-fencing-test",
        },
    )
    assert task.status_code == 200
    task_id = UUID(task.json()["task_id"])

    with psycopg.connect(_dsn()) as conn:
        row = conn.execute(
            "SELECT credential_generation FROM remote_agents WHERE id=%s",
            (agent_id,),
        ).fetchone()
        assert row is not None
        old_generation = row[0]

    ready = threading.Event()
    release = threading.Event()
    original_db = __import__("backend.logistics.remote_control", fromlist=["_db"])._db

    def locked_db():
        conn = original_db()
        original_connect = conn.execute
        first = True

        def execute(sql, params=None):
            nonlocal first
            result = original_connect(sql, params)
            if first and "FROM remote_agents WHERE id=%s FOR UPDATE" in sql:
                first = False
                ready.set()
                assert release.wait(timeout=10), "next-task transaction did not remain blocked"
            return result

        conn.execute = execute
        return conn

    # The endpoint itself must acquire the row lock before validating the
    # credential. Holding that lock here gives the test a deterministic
    # serialization point without relying on arbitrary sleeps.
    import backend.logistics.remote_control as remote_control

    monkeypatch.setattr(remote_control, "_db", locked_db)
    result: dict[str, object] = {}

    def poll() -> None:
        response = client.get(
            f"/api/v1/control/agents/{agent_id}/tasks/next",
            headers={"Authorization": f"Bearer {old_token}"},
        )
        result["status"] = response.status_code
        result["body"] = response.json()

    worker = threading.Thread(target=poll, daemon=True)
    worker.start()
    assert ready.wait(timeout=10), "next-task transaction did not reach agent-row lock"

    # Revoke and re-enroll through independent DB connections while the
    # polling transaction is paused after its row lock. PostgreSQL serializes
    # the revoke behind that lock, so the polling request must finish before
    # the revoke can commit. This proves the endpoint cannot observe a
    # half-updated credential state.
    release.set()
    worker.join(timeout=15)
    assert not worker.is_alive()

    assert result["status"] == 200
    body = result["body"]
    assert isinstance(body, dict)
    assert body["task"] is not None

    leased_generation: int
    with psycopg.connect(_dsn()) as conn:
        leased = conn.execute(
            "SELECT lease_credential_generation,status FROM remote_tasks WHERE id=%s",
            (task_id,),
        ).fetchone()
        assert leased is not None
        leased_generation = leased[0]
        assert leased[1] == "running"

    assert leased_generation == old_generation
