from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import shlex
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import psycopg
from fastapi import Header, HTTPException
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from .api import app, _dsn

LEASE_SECONDS = 120


def _agent_token() -> str:
    return os.getenv("REMOTE_AGENT_TOKEN", "")


def _operator_token() -> str:
    return os.getenv("CONTROL_PLANE_OPERATOR_TOKEN", "")


def _require(value: str | None, expected: str, detail: str) -> None:
    if not expected or not value or not hmac.compare_digest(value, f"Bearer {expected}"):
        raise HTTPException(status_code=401, detail=detail)


def _require_hash(value: str | None, credential_hash: str | None) -> None:
    if not value or not credential_hash:
        raise HTTPException(status_code=401, detail="agent credential required")
    presented = value.removeprefix("Bearer ")
    if not hmac.compare_digest(hashlib.sha256(presented.encode()).hexdigest(), credential_hash):
        raise HTTPException(status_code=401, detail="agent credential invalid")


def _new_credential() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, hashlib.sha256(token.encode()).hexdigest()


def _db():
    return psycopg.connect(_dsn())


class AgentHeartbeat(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    agent_id: UUID | None = None
    tenant_id: UUID | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    agent_id: UUID
    tenant_id: UUID | None = None
    command: str = Field(min_length=1, max_length=4000)
    cwd: str = Field(default="/opt/logistics", max_length=1000)
    requested_by: str = Field(default="operator", min_length=1, max_length=120)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=200)


class EventRequest(BaseModel):
    stream: str = Field(default="stdout", min_length=1, max_length=20)
    message: str = Field(max_length=20000)


class CompleteRequest(BaseModel):
    returncode: int
    stdout: str = Field(default="", max_length=200000)
    stderr: str = Field(default="", max_length=200000)


def _approval(command: str) -> str:
    """Classify commands conservatively using parsed argv, not string prefixes."""
    if any(token in command for token in ("&&", "||", ";", "|", ">", "<", "`", "$(")):
        return "REVIEW"
    try:
        argv = shlex.split(command)
    except ValueError:
        return "REVIEW"
    if not argv:
        return "REVIEW"
    blocked = {
        "rm -rf", "shutdown", "reboot", "mkfs", "dd if=", "docker system prune",
        "git push --force", "chmod 777", "chown -r", "curl |", "wget |",
    }
    normalized = command.strip().lower()
    if any(token in normalized for token in blocked):
        return "BLOCK"
    if argv in (["pwd"], ["whoami"], ["date"], ["uname"], ["uname", "-a"]):
        return "AUTO"
    if argv in (["git", "status"], ["git", "diff"], ["git", "log"]):
        return "AUTO"
    if len(argv) >= 3 and argv[:3] in (["python", "-m", "pytest"], ["python", "-m", "compileall"]):
        return "AUTO"
    return "REVIEW"


@app.get("/api/v1/control/agents")
def control_agents(authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        rows = conn.execute("SELECT id,name,tenant_id,status,last_seen,metadata,created_at FROM remote_agents ORDER BY name").fetchall()
    now = datetime.now(timezone.utc)
    return [
        {"id": str(r[0]), "name": r[1], "tenant_id": str(r[2]) if r[2] else None,
         "status": "online" if r[4] and (now - r[4]).total_seconds() < 90 else "offline",
         "last_seen": r[4].isoformat() if r[4] else None, "metadata": r[5], "created_at": r[6].isoformat()}
        for r in rows
    ]


@app.post("/api/v1/control/agents/heartbeat")
def control_heartbeat(req: AgentHeartbeat, authorization: str | None = Header(default=None)) -> dict[str, object]:
    """Bootstrap with the global enrollment token, then require a per-agent token."""
    with _db() as conn:
        credential: str | None = None
        if req.agent_id:
            row = conn.execute("SELECT id,name,tenant_id,credential_hash FROM remote_agents WHERE id=%s", (req.agent_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="agent not found")
            _require_hash(authorization, row[3])
            if req.name != row[1]:
                raise HTTPException(status_code=403, detail="agent identity mismatch")
            if req.tenant_id != row[2]:
                raise HTTPException(status_code=403, detail="tenant mismatch")
            agent_id, tenant_id = row[0], row[2]
            conn.execute("UPDATE remote_agents SET last_seen=now(),status='online',metadata=%s WHERE id=%s", (Jsonb(req.metadata), agent_id))
        else:
            _require(authorization, _agent_token(), "agent bootstrap unauthorized")
            row = conn.execute("SELECT id,tenant_id FROM remote_agents WHERE name=%s", (req.name,)).fetchone()
            credential, credential_hash = _new_credential()
            if row:
                agent_id, existing_tenant = row[0], row[1]
                if req.tenant_id != existing_tenant:
                    raise HTTPException(status_code=403, detail="tenant mismatch")
                tenant_id = existing_tenant
                conn.execute("UPDATE remote_agents SET last_seen=now(),status='online',metadata=%s,credential_hash=%s,credential_created_at=now(),credential_revoked_at=NULL,credential_generation=credential_generation+1 WHERE id=%s", (Jsonb(req.metadata), credential_hash, agent_id))
            else:
                agent_id, tenant_id = uuid4(), req.tenant_id
                conn.execute("INSERT INTO remote_agents(id,name,tenant_id,last_seen,status,metadata,credential_hash,credential_created_at) VALUES(%s,%s,%s,now(),'online',%s,%s,now())", (agent_id, req.name, tenant_id, Jsonb(req.metadata), credential_hash))
        conn.commit()
    result = {"agent_id": str(agent_id), "tenant_id": str(tenant_id) if tenant_id else None, "status": "online", "server_time": datetime.now(timezone.utc).isoformat()}
    if credential:
        result["control_token"] = credential
        result["credential_mode"] = "per_agent"
    else:
        result["credential_mode"] = "per_agent"
    return result


@app.post("/api/v1/control/agents/{agent_id}/credential/revoke")
def control_revoke_agent_credential(agent_id: UUID, authorization: str | None = Header(default=None)) -> dict[str, str]:
    """Revoke an enrolled agent credential and fence its active leases."""
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        changed = conn.execute(
            "UPDATE remote_agents SET credential_hash=NULL,credential_revoked_at=now(),credential_generation=credential_generation+1,status='offline' WHERE id=%s AND credential_hash IS NOT NULL",
            (agent_id,),
        ).rowcount
        if changed:
            conn.execute(
                "UPDATE remote_tasks SET status='cancelled',cancel_requested=true,lease_expires_at=NULL,finished_at=COALESCE(finished_at,now()) WHERE agent_id=%s AND status='running'",
                (agent_id,),
            )
        conn.commit()
    if not changed:
        raise HTTPException(status_code=404, detail="active agent credential not found")
    return {"agent_id": str(agent_id), "status": "credential_revoked"}


def _require_task_agent(conn, task_id: UUID, authorization: str | None) -> int:
    row = conn.execute("SELECT a.credential_hash,a.credential_generation,t.lease_credential_generation FROM remote_tasks t JOIN remote_agents a ON a.id=t.agent_id WHERE t.id=%s", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="task not found")
    _require_hash(authorization, row[0])
    if row[2] is None or row[2] != row[1]:
        raise HTTPException(status_code=409, detail="task credential generation fenced")
    return row[1]


@app.post("/api/v1/control/tasks")
def control_create_task(req: TaskRequest, authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require(authorization, _operator_token(), "operator unauthorized")
    approval = _approval(req.command)
    with _db() as conn:
        agent = conn.execute("SELECT tenant_id FROM remote_agents WHERE id=%s", (req.agent_id,)).fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail="agent not found")
        if req.tenant_id != agent[0]:
            raise HTTPException(status_code=403, detail="tenant mismatch")
        tenant_id = agent[0]
        if req.idempotency_key:
            existing = conn.execute("SELECT id,status,approval FROM remote_tasks WHERE agent_id=%s AND idempotency_key=%s", (req.agent_id, req.idempotency_key)).fetchone()
            if existing:
                return {"task_id": str(existing[0]), "status": existing[1], "approval": existing[2], "idempotent_replay": True}
        task_id = uuid4()
        conn.execute("INSERT INTO remote_tasks(id,agent_id,tenant_id,command,cwd,approval,requested_by,idempotency_key) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", (task_id, req.agent_id, tenant_id, req.command, req.cwd, approval, req.requested_by, req.idempotency_key))
        conn.commit()
    return {"task_id": str(task_id), "status": "queued", "approval": approval, "idempotent_replay": False}


@app.get("/api/v1/control/agents/{agent_id}/tasks/next")
def control_next_task(agent_id: UUID, authorization: str | None = Header(default=None)) -> dict[str, object]:
    with _db() as conn:
        agent = conn.execute("SELECT credential_hash,credential_generation FROM remote_agents WHERE id=%s FOR UPDATE", (agent_id,)).fetchone()
        if not agent:
            raise HTTPException(status_code=404, detail="agent not found")
        _require_hash(authorization, agent[0])
        generation = agent[1]
        now = datetime.now(timezone.utc)
        conn.execute("UPDATE remote_tasks SET status='queued',lease_expires_at=NULL,lease_credential_generation=NULL WHERE agent_id=%s AND status='running' AND lease_expires_at < %s", (agent_id, now))
        row = conn.execute("SELECT id,command,cwd,approval,tenant_id FROM remote_tasks WHERE agent_id=%s AND status='queued' AND approval='AUTO' AND NOT cancel_requested ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED", (agent_id,)).fetchone()
        if not row:
            conn.commit()
            return {"task": None}
        expires = now + timedelta(seconds=LEASE_SECONDS)
        conn.execute("UPDATE remote_tasks SET status='running',started_at=COALESCE(started_at,now()),heartbeat_at=now(),lease_expires_at=%s,lease_credential_generation=%s WHERE id=%s", (expires, generation, row[0]))
        conn.commit()
    return {"task": {"id": str(row[0]), "command": row[1], "cwd": row[2], "approval": row[3], "tenant_id": str(row[4]) if row[4] else None, "lease_expires_at": expires.isoformat()}}


@app.post("/api/v1/control/tasks/{task_id}/events")
def control_event(task_id: UUID, req: EventRequest, authorization: str | None = Header(default=None)) -> dict[str, str]:
    with _db() as conn:
        _require_task_agent(conn, task_id, authorization)
        changed = conn.execute("UPDATE remote_tasks t SET heartbeat_at=now(),lease_expires_at=now()+interval '120 seconds' FROM remote_agents a WHERE t.id=%s AND t.agent_id=a.id AND t.status='running' AND t.lease_expires_at > now() AND t.lease_credential_generation=a.credential_generation", (task_id,)).rowcount
        if not changed:
            conn.rollback()
            raise HTTPException(status_code=404, detail="active task not found")
        conn.execute("INSERT INTO remote_task_events(task_id,stream,message) VALUES(%s,%s,%s)", (task_id, req.stream, req.message))
        conn.commit()
    return {"status": "accepted"}


@app.post("/api/v1/control/tasks/{task_id}/complete")
def control_complete(task_id: UUID, req: CompleteRequest, authorization: str | None = Header(default=None)) -> dict[str, object]:
    status = "succeeded" if req.returncode == 0 else "failed"
    with _db() as conn:
        _require_task_agent(conn, task_id, authorization)
        changed = conn.execute("UPDATE remote_tasks t SET status=%s,returncode=%s,stdout=%s,stderr=%s,finished_at=now(),lease_expires_at=NULL WHERE t.id=%s AND t.status='running' AND t.lease_expires_at > now() AND t.lease_credential_generation=(SELECT credential_generation FROM remote_agents WHERE id=t.agent_id)", (status, req.returncode, req.stdout, req.stderr, task_id)).rowcount
        conn.commit()
    if not changed:
        raise HTTPException(status_code=404, detail="active task not found")
    return {"status": status, "task_id": str(task_id)}


@app.post("/api/v1/control/tasks/{task_id}/cancel")
def control_cancel(task_id: UUID, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        changed = conn.execute("UPDATE remote_tasks SET cancel_requested=true,status='cancelled',lease_expires_at=NULL,finished_at=COALESCE(finished_at,now()) WHERE id=%s AND status IN ('queued','running')", (task_id,)).rowcount
        conn.commit()
    if not changed:
        raise HTTPException(status_code=404, detail="task not found")
    return {"task_id": str(task_id), "status": "cancelled"}


@app.get("/api/v1/control/tasks")
def control_tasks(authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        rows = conn.execute("SELECT id,agent_id,tenant_id,command,cwd,status,approval,requested_by,returncode,stdout,stderr,created_at,started_at,finished_at,lease_expires_at,heartbeat_at FROM remote_tasks ORDER BY created_at DESC LIMIT 100").fetchall()
    return [
        {"id": str(r[0]), "agent_id": str(r[1]), "tenant_id": str(r[2]) if r[2] else None, "command": r[3], "cwd": r[4], "status": r[5], "approval": r[6], "requested_by": r[7], "returncode": r[8], "stdout": r[9], "stderr": r[10], "created_at": r[11].isoformat(), "started_at": r[12].isoformat() if r[12] else None, "finished_at": r[13].isoformat() if r[13] else None, "lease_expires_at": r[14].isoformat() if r[14] else None, "heartbeat_at": r[15].isoformat() if r[15] else None}
        for r in rows
    ]


@app.get("/api/v1/control/tasks/{task_id}/events")
def control_task_events(task_id: UUID, authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        rows = conn.execute("SELECT stream,message,created_at FROM remote_task_events WHERE task_id=%s ORDER BY id", (task_id,)).fetchall()
    return [{"stream": r[0], "message": r[1], "created_at": r[2].isoformat()} for r in rows]
