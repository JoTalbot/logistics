"""Integration tests for the remote control plane (Vercel <-> Ubuntu agent).

These cover the heartbeat/task lifecycle against a real PostgreSQL instance.
They are skipped when DATABASE_URL is not configured, matching the existing
integration test convention in this repository.
"""
from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from logistics import remote_control  # noqa: F401  (registers control routes)
from logistics.remote_control import (
    AgentHeartbeat,
    CompleteRequest,
    TaskRequest,
    control_agents,
    control_complete,
    control_create_task,
    control_heartbeat,
    control_next_task,
)

AGENT_TOKEN = "pytest-remote-agent-token"
OPERATOR_TOKEN = "pytest-operator-token"


@pytest.fixture
def configured(monkeypatch):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    monkeypatch.setenv("REMOTE_AGENT_TOKEN", AGENT_TOKEN)
    monkeypatch.setenv("CONTROL_PLANE_OPERATOR_TOKEN", OPERATOR_TOKEN)
    return True


def _agent(name: str) -> dict[str, object]:
    return control_heartbeat(
        AgentHeartbeat(name=name, metadata={"hostname": name, "source": "pytest"}),
        authorization=f"Bearer {AGENT_TOKEN}",
    )


def test_heartbeat_accepts_json_metadata(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    first = _agent(name)
    assert first["status"] == "online"
    agent_id = UUID(str(first["agent_id"]))

    second = control_heartbeat(
        AgentHeartbeat(name=name, agent_id=agent_id, metadata={"hostname": name, "source": "pytest", "nested": {"ok": True}}),
        authorization=f"Bearer {AGENT_TOKEN}",
    )
    assert second["agent_id"] == str(agent_id)


def test_operator_lists_registered_agent(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    _agent(name)
    agents = control_agents(authorization=f"Bearer {OPERATOR_TOKEN}")
    match = [a for a in agents if a["name"] == name]
    assert match and match[0]["status"] == "online"


def test_operator_authentication_is_enforced(configured):
    with pytest.raises(HTTPException) as excinfo:
        control_agents(authorization=None)
    assert excinfo.value.status_code == 401

    with pytest.raises(HTTPException) as excinfo:
        control_agents(authorization="Bearer wrong-token")
    assert excinfo.value.status_code == 401


def test_safe_task_lifecycle(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    agent_id = UUID(str(_agent(name)["agent_id"]))

    created = control_create_task(
        TaskRequest(agent_id=agent_id, command="uname -a"),
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )
    assert created["approval"] == "AUTO"
    assert created["status"] == "queued"

    next_task = control_next_task(agent_id, authorization=f"Bearer {AGENT_TOKEN}")
    assert next_task["task"] is not None
    assert next_task["task"]["command"] == "uname -a"

    completed = control_complete(
        UUID(str(next_task["task"]["id"])),
        CompleteRequest(returncode=0, stdout="Linux arm-server-01", stderr=""),
        authorization=f"Bearer {AGENT_TOKEN}",
    )
    assert completed["status"] == "succeeded"


def test_high_risk_task_is_not_auto_dispatched(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    agent_id = UUID(str(_agent(name)["agent_id"]))

    created = control_create_task(
        TaskRequest(agent_id=agent_id, command="rm -rf /tmp/pytest-example"),
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )
    assert created["approval"] == "REVIEW"

    next_task = control_next_task(agent_id, authorization=f"Bearer {AGENT_TOKEN}")
    assert next_task["task"] is None
