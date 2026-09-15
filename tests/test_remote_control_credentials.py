"""Credential lifecycle regression tests for the bounded remote control plane."""
from __future__ import annotations

import os
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi import HTTPException

from logistics.remote_control import (
    AgentHeartbeat,
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


def test_operator_can_revoke_agent_credential_and_old_token_stops_working(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    agent = control_heartbeat(
        AgentHeartbeat(name=name, metadata={"source": "credential-test"}),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    agent_id = UUID(str(agent["agent_id"]))
    old_token = agent["control_token"]

    assert control_revoke_agent_credential(
        agent_id,
        authorization=f"Bearer {OPERATOR_TOKEN}",
    )["status"] == "credential_revoked"

    with pytest.raises(HTTPException) as excinfo:
        control_next_task(agent_id, authorization=f"Bearer {old_token}")
    assert excinfo.value.status_code == 401

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        row = conn.execute(
            "SELECT credential_hash,credential_revoked_at,status FROM remote_agents WHERE id=%s",
            (agent_id,),
        ).fetchone()
    assert row[0] is None
    assert row[1] is not None
    assert row[2] == "offline"


def test_revoked_agent_can_bootstrap_again_and_get_new_credential(configured):
    name = f"pytest-agent-{uuid4().hex[:12]}"
    first = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    agent_id = UUID(str(first["agent_id"]))
    old_token = first["control_token"]
    control_revoke_agent_credential(agent_id, authorization=f"Bearer {OPERATOR_TOKEN}")

    second = control_heartbeat(
        AgentHeartbeat(name=name),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    assert UUID(str(second["agent_id"])) == agent_id
    assert second["control_token"] != old_token
    assert second["credential_mode"] == "per_agent"
    assert control_next_task(agent_id, authorization=f"Bearer {second['control_token']}")["task"] is None


def test_credential_revoke_requires_operator_authentication(configured):
    agent = control_heartbeat(
        AgentHeartbeat(name=f"pytest-agent-{uuid4().hex[:12]}"),
        authorization=f"Bearer {BOOTSTRAP_TOKEN}",
    )
    with pytest.raises(HTTPException) as excinfo:
        control_revoke_agent_credential(
            UUID(str(agent["agent_id"])),
            authorization=f"Bearer {BOOTSTRAP_TOKEN}",
        )
    assert excinfo.value.status_code == 401
