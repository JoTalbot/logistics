"""Regression coverage for revoke/re-enrollment lease-generation fencing."""
from __future__ import annotations

import os
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi import HTTPException

from logistics.remote_control import (
    AgentHeartbeat,
    CompleteRequest,
    TaskRequest,
    control_complete,
    control_create_task,
    control_heartbeat,
    control_next_task,
    control_revoke_agent_credential,
)

BOOTSTRAP_TOKEN = "pytest-remote-agent-token"
OPERATOR_TOKEN = "pytest-operator-token"


@pytest.fixture
def configured(monkeypatch):
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured")
    monkeypatch.setenv("REMOTE_AGENT_TOKEN", BOOTSTRAP_TOKEN)
    monkeypatch.setenv("CONTROL_PLANE_OPERATOR_TOKEN", OPERATOR_TOKEN)


def _auth(agent: dict[str, object]) -> str:
    return f"Bearer {agent['control_token']}"


def test_reenrollment_gets_new_lease_generation_after_revoke(configured):
    """The old lease stays fenced while the re-enrolled credential can lease a new task."""
    name = f"pytest-agent-{uuid4().hex[:12]}"
    first = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    agent_id = UUID(str(first["agent_id"]))

    old_created = control_create_task(
        TaskRequest(agent_id=agent_id, command="pwd"),
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )
    old_task = control_next_task(agent_id, authorization=_auth(first))["task"]
    assert old_task["id"] == old_created["task_id"]

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        old_generation = conn.execute(
            "SELECT credential_generation FROM remote_agents WHERE id=%s",
            (agent_id,),
        ).fetchone()[0]

    control_revoke_agent_credential(
        agent_id,
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )

    second = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    assert UUID(str(second["agent_id"])) == agent_id
    assert second["control_token"] != first["control_token"]

    new_created = control_create_task(
        TaskRequest(agent_id=agent_id, command="whoami"),
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )
    new_task = control_next_task(agent_id, authorization=_auth(second))["task"]
    assert new_task["id"] == new_created["task_id"]

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(
            "SELECT t.id,t.status,t.lease_credential_generation,a.credential_generation "
            "FROM remote_tasks t JOIN remote_agents a ON a.id=t.agent_id "
            "WHERE t.id IN (%s,%s) ORDER BY t.created_at",
            (UUID(str(old_task["id"])), UUID(str(new_task["id"]))),
        ).fetchall()

    assert len(rows) == 2
    assert rows[0][1] == "cancelled"
    assert rows[0][2] != rows[0][3]
    assert rows[1][1] == "running"
    assert rows[1][2] == rows[1][3]
    assert rows[1][2] > old_generation

    with pytest.raises(HTTPException) as excinfo:
        control_next_task(agent_id, authorization=_auth(first))
    assert excinfo.value.status_code == 401

    with pytest.raises(HTTPException) as excinfo:
        control_complete(
            UUID(str(old_task["id"])),
            CompleteRequest(returncode=0),
            authorization=_auth(first),
        )
    assert excinfo.value.status_code == 401

    assert control_complete(
        UUID(str(new_task["id"])),
        CompleteRequest(returncode=0),
        authorization=_auth(second),
    )["status"] == "succeeded"


def test_direct_reenrollment_cancels_active_lease(configured):
    """Credential rotation directly through bootstrap also terminates the old lease state."""
    name = f"pytest-agent-{uuid4().hex[:12]}"
    first = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    agent_id = UUID(str(first["agent_id"]))

    created = control_create_task(
        TaskRequest(agent_id=agent_id, command="pwd"),
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )
    leased = control_next_task(agent_id, authorization=_auth(first))["task"]
    assert leased["id"] == created["task_id"]

    second = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    assert second["control_token"] != first["control_token"]

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        row = conn.execute(
            "SELECT status,lease_credential_generation,"
            "(SELECT credential_generation FROM remote_agents WHERE id=%s) "
            "FROM remote_tasks WHERE id=%s",
            (agent_id, UUID(str(leased["id"]))),
        ).fetchone()

    assert row[0] == "cancelled"
    assert row[1] is not None
    assert row[1] != row[2]

    with pytest.raises(HTTPException) as excinfo:
        control_complete(
            UUID(str(leased["id"])),
            CompleteRequest(returncode=0),
            authorization=_auth(first),
        )
    assert excinfo.value.status_code == 401
