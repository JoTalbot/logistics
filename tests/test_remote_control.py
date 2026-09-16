"""Integration tests for the bounded remote control plane."""
from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi import HTTPException

from logistics import remote_control  # noqa: F401
from logistics.remote_control import (
    AgentHeartbeat,
    CompleteRequest,
    EventRequest,
    TaskRequest,
    _approval,
    control_agents,
    control_cancel,
    control_complete,
    control_create_task,
    control_event,
    control_heartbeat,
    control_next_task,
)

BOOTSTRAP_TOKEN = "pytest-remote-agent-token"
OPERATOR_TOKEN = "pytest-operator-token"

@pytest.fixture
def configured(monkeypatch):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    monkeypatch.setenv("REMOTE_AGENT_TOKEN", BOOTSTRAP_TOKEN)
    monkeypatch.setenv("CONTROL_PLANE_OPERATOR_TOKEN", OPERATOR_TOKEN)

def _tenant() -> UUID:
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        tenant_id = conn.execute("INSERT INTO tenants(name) VALUES (%s) RETURNING id", (f"pytest-remote-control-{uuid4().hex}",)).fetchone()[0]
        conn.commit()
    return UUID(str(tenant_id))

def _agent(name: str, tenant_id=None) -> dict[str, object]:
    return control_heartbeat(AgentHeartbeat(name=name, tenant_id=tenant_id, metadata={"hostname": name, "source": "pytest"}), authorization=f"Bearer {BOOTSTRAP_TOKEN}")

def _auth(agent: dict[str, object]) -> str:
    return f"Bearer {agent['control_token']}"

def _allowed() -> set[str]:
    source = Path(__file__).parents[1] / "deploy" / "remote-agent" / "agent.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ALLOWED" for t in n.targets))
    return set(ast.literal_eval(assignment.value))

def test_heartbeat_accepts_json_metadata(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    agent = _agent(name)
    agent_id = UUID(str(agent["agent_id"]))
    second = control_heartbeat(AgentHeartbeat(agent_id=agent_id, name=name, metadata={"hostname": name, "source": "pytest-2"}), authorization=_auth(agent))
    assert second["agent_id"] == str(agent_id)
    assert second["credential_mode"] == "per_agent"

def test_heartbeat_cannot_change_enrolled_agent_name(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    agent = _agent(name)
    with pytest.raises(HTTPException) as excinfo:
        control_heartbeat(AgentHeartbeat(agent_id=UUID(str(agent["agent_id"])), name=f"other-{uuid4().hex[:12]}"), authorization=_auth(agent))
    assert excinfo.value.status_code == 403

def test_heartbeat_cannot_change_enrolled_agent_tenant(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    tenant_id = _tenant()
    agent = _agent(name, tenant_id=tenant_id)
    with pytest.raises(HTTPException) as excinfo:
        control_heartbeat(AgentHeartbeat(agent_id=UUID(str(agent["agent_id"])), name=name, tenant_id=_tenant()), authorization=_auth(agent))
    assert excinfo.value.status_code == 403

def test_bootstrap_cannot_change_enrolled_agent_tenant(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    tenant_id = _tenant()
    agent = _agent(name, tenant_id=tenant_id)
    with pytest.raises(HTTPException) as excinfo:
        control_heartbeat(AgentHeartbeat(name=name), authorization=f"Bearer {BOOTSTRAP_TOKEN}")
    assert excinfo.value.status_code == 403

def test_operator_authentication_is_enforced(configured):
    with pytest.raises(HTTPException) as excinfo:
        control_agents(authorization=None)
    assert excinfo.value.status_code == 401

def test_safe_task_lifecycle(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    agent_id = UUID(str(agent["agent_id"]))
    created = control_create_task(TaskRequest(agent_id=agent_id, command="uname -a", idempotency_key=f"k-{uuid4().hex}"), authorization=f"Bearer {OPERATOR_TOKEN}")
    task = control_next_task(agent_id, authorization=_auth(agent))["task"]
    assert task["id"] == created["task_id"]
    assert control_complete(UUID(str(task["id"])), CompleteRequest(returncode=0, stdout="Linux arm-server-01"), authorization=_auth(agent))["status"] == "succeeded"

def test_wrong_agent_credential_is_rejected(configured):
    first = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    second = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    with pytest.raises(HTTPException) as excinfo:
        control_next_task(UUID(str(first["agent_id"])), authorization=_auth(second))
    assert excinfo.value.status_code == 401

def test_global_token_cannot_operate_enrolled_agent(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    with pytest.raises(HTTPException) as excinfo:
        control_next_task(UUID(str(agent["agent_id"])), authorization=f"Bearer {BOOTSTRAP_TOKEN}")
    assert excinfo.value.status_code == 401

def test_unknown_and_destructive_commands_are_not_auto_dispatched(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    agent_id = UUID(str(agent["agent_id"]))
    review = control_create_task(TaskRequest(agent_id=agent_id, command="python -c 'print(1)'"), authorization=f"Bearer {OPERATOR_TOKEN}")
    blocked = control_create_task(TaskRequest(agent_id=agent_id, command="rm -rf /tmp/pytest-example"), authorization=f"Bearer {OPERATOR_TOKEN}")
    assert review["approval"] == "REVIEW"
    assert blocked["approval"] == "BLOCK"
    assert control_next_task(agent_id, authorization=_auth(agent))["task"] is None

def test_idempotency_returns_same_task(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    agent_id = UUID(str(agent["agent_id"]))
    key = f"idem-{uuid4().hex}"
    first = control_create_task(TaskRequest(agent_id=agent_id, command="pwd", idempotency_key=key), authorization=f"Bearer {OPERATOR_TOKEN}")
    second = control_create_task(TaskRequest(agent_id=agent_id, command="pwd", idempotency_key=key), authorization=f"Bearer {OPERATOR_TOKEN}")
    assert second["task_id"] == first["task_id"] and second["idempotent_replay"] is True

def test_idempotency_is_scoped_to_agent(configured):
    first = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    second = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    first_id = UUID(str(first["agent_id"]))
    second_id = UUID(str(second["agent_id"]))
    key = f"shared-{uuid4().hex}"
    first_created = control_create_task(TaskRequest(agent_id=first_id, command="pwd", idempotency_key=key), authorization=f"Bearer {OPERATOR_TOKEN}")
    second_created = control_create_task(TaskRequest(agent_id=second_id, command="pwd", idempotency_key=key), authorization=f"Bearer {OPERATOR_TOKEN}")
    assert second_created["task_id"] != first_created["task_id"]
    assert second_created["idempotent_replay"] is False
    first_replay = control_create_task(TaskRequest(agent_id=first_id, command="pwd", idempotency_key=key), authorization=f"Bearer {OPERATOR_TOKEN}")
    second_replay = control_create_task(TaskRequest(agent_id=second_id, command="pwd", idempotency_key=key), authorization=f"Bearer {OPERATOR_TOKEN}")
    assert first_replay["task_id"] == first_created["task_id"]
    assert second_replay["task_id"] == second_created["task_id"]
    assert first_replay["idempotent_replay"] is True
    assert second_replay["idempotent_replay"] is True

def test_operator_listing_reports_online(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    _agent(name)
    match = [a for a in control_agents(authorization=f"Bearer {OPERATOR_TOKEN}") if a["name"] == name]
    assert match and match[0]["status"] == "online"

def test_auto_policy_commands_are_supported_by_remote_agent():
    assert {"pwd", "whoami", "uname", "date", "git", "python"} <= _allowed()

def test_auto_policy_is_strict_about_shell_composition_and_arguments():
    assert _approval("git status") == "AUTO"
    assert _approval("uname -a") == "AUTO"
    assert _approval("git status; rm -rf /tmp/example") == "REVIEW"
    assert _approval("git status && whoami") == "REVIEW"
    assert _approval("git status --output=/tmp/task") == "REVIEW"
    assert _approval("python -c 'print(1)'") == "REVIEW"
    assert _approval("python -m pytest -q") == "AUTO"

def test_cancelling_running_task_finalizes_it(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    agent_id = UUID(str(agent["agent_id"]))
    created = control_create_task(TaskRequest(agent_id=agent_id, command="pwd"), authorization=f"Bearer {OPERATOR_TOKEN}")
    task = control_next_task(agent_id, authorization=_auth(agent))["task"]
    assert task["id"] == created["task_id"]
    assert control_cancel(UUID(str(task["id"])), authorization=f"Bearer {OPERATOR_TOKEN}")["status"] == "cancelled"
    with pytest.raises(HTTPException) as excinfo:
        control_complete(UUID(str(task["id"])), CompleteRequest(returncode=0), authorization=_auth(agent))
    assert excinfo.value.status_code == 404

def test_cancelled_task_rejects_late_events(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    agent_id = UUID(str(agent["agent_id"]))
    created = control_create_task(TaskRequest(agent_id=agent_id, command="pwd"), authorization=f"Bearer {OPERATOR_TOKEN}")
    task = control_next_task(agent_id, authorization=_auth(agent))["task"]
    control_cancel(UUID(str(created["task_id"])), authorization=f"Bearer {OPERATOR_TOKEN}")
    with pytest.raises(HTTPException) as excinfo:
        control_event(UUID(str(task["id"])), EventRequest(message="late"), authorization=_auth(agent))
    assert excinfo.value.status_code == 404

def test_task_tenant_must_match_agent_tenant(configured):
    tenant_id = _tenant()
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}", tenant_id=tenant_id)
    with pytest.raises(HTTPException) as excinfo:
        control_create_task(TaskRequest(agent_id=UUID(str(agent["agent_id"])), tenant_id=_tenant(), command="pwd"), authorization=f"Bearer {OPERATOR_TOKEN}")
    assert excinfo.value.status_code == 403

def test_unscoped_agent_cannot_receive_tenant_task(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    with pytest.raises(HTTPException) as excinfo:
        control_create_task(TaskRequest(agent_id=UUID(str(agent["agent_id"])), tenant_id=_tenant(), command="pwd"), authorization=f"Bearer {OPERATOR_TOKEN}")
    assert excinfo.value.status_code == 403

def test_credential_is_stored_as_hash_not_plaintext(configured):
    agent = _agent(f"pytest-agent-{uuid4().hex[:12]}")
    token = str(agent["control_token"])
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        row = conn.execute("SELECT credential_hash,credential_created_at FROM remote_agents WHERE id=%s", (UUID(str(agent["agent_id"])),)).fetchone()
    assert row[0] == hashlib.sha256(token.encode()).hexdigest()
    assert token not in row[0] and row[1] is not None
