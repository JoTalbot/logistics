"""Concurrency regression coverage for task idempotency."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest

from logistics.remote_control import AgentHeartbeat, TaskRequest, control_create_task, control_heartbeat

BOOTSTRAP_TOKEN = "pytest-remote-agent-token"
OPERATOR_TOKEN = "pytest-operator-token"


@pytest.fixture
def configured(monkeypatch):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    monkeypatch.setenv("REMOTE_AGENT_TOKEN", BOOTSTRAP_TOKEN)
    monkeypatch.setenv("CONTROL_PLANE_OPERATOR_TOKEN", OPERATOR_TOKEN)


def test_concurrent_idempotent_task_creation_returns_one_task(configured):
    """Concurrent retries with one agent/key must converge on the same task."""
    name = f"pytest-agent-{uuid4().hex[:12]}"
    agent = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    agent_id = UUID(str(agent["agent_id"]))
    key = f"race-{uuid4().hex}"

    def create() -> dict[str, object]:
        return control_create_task(
            TaskRequest(agent_id=agent_id, command="pwd", idempotency_key=key),
            authorization=f"Bearer {OPERATOR_TOKEN}",
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.map(lambda _: create(), range(2))

    assert first["task_id"] == second["task_id"]
    assert sorted([first["idempotent_replay"], second["idempotent_replay"]]) == [False, True]
