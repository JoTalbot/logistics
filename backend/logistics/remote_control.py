from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timezone
from uuid import UUID, uuid4

import psycopg
from fastapi import Header, HTTPException
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from .api import app, _dsn


def _agent_token() -> str:
    return os.getenv("REMOTE_AGENT_TOKEN", "")


def _operator_token() -> str:
    return os.getenv("CONTROL_PLANE_OPERATOR_TOKEN", "")


def _require(value: str | None, expected: str, detail: str) -> None:
    if not expected or not value or not hmac.compare_digest(value, f"Bearer {expected}"):
        raise HTTPException(status_code=401, detail=detail)


def _db():
    conn = psycopg.connect(_dsn())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS remote_agents (
            id uuid PRIMARY KEY,
            name text NOT NULL UNIQUE,
            last_seen timestamptz,
            status text NOT NULL DEFAULT 'offline',
            metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS remote_tasks (
            id uuid PRIMARY KEY,
            agent_id uuid NOT NULL REFERENCES remote_agents(id) ON DELETE CASCADE,
            command text NOT NULL,
            cwd text NOT NULL DEFAULT '/opt/logistics',
            status text NOT NULL DEFAULT 'queued',
            approval text NOT NULL DEFAULT 'AUTO',
            requested_by text NOT NULL,
            cancel_requested boolean NOT NULL DEFAULT false,
            returncode integer,
            stdout text NOT NULL DEFAULT '',
            stderr text NOT NULL DEFAULT '',
            created_at timestamptz NOT NULL DEFAULT now(),
            started_at timestamptz,
            finished_at timestamptz
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS remote_task_events (
            id bigserial PRIMARY KEY,
            task_id uuid NOT NULL REFERENCES remote_tasks(id) ON DELETE CASCADE,
            stream text NOT NULL,
            message text NOT NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    conn.commit()
    return conn


class AgentHeartbeat(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    agent_id: UUID | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    agent_id: UUID
    command: str = Field(min_length=1, max_length=4000)
    cwd: str = Field(default="/opt/logistics", max_length=1000)
    requested_by: str = Field(default="android", min_length=1, max_length=120)


class EventRequest(BaseModel):
    stream: str = Field(default="stdout", max_length=20)
    message: str = Field(max_length=20000)


class CompleteRequest(BaseModel):
    returncode: int
    stdout: str = Field(default="", max_length=200000)
    stderr: str = Field(default="", max_length=200000)


def _approval(command: str) -> str:
    blocked = ("rm -rf", "shutdown", "reboot", "mkfs", "dd if=", "docker system prune", "git push --force", "chmod 777", "chown -R")
    return "REVIEW" if any(x in command.lower() for x in blocked) else "AUTO"


@app.get("/api/v1/control/agents")
def control_agents(authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        rows = conn.execute("SELECT id,name,status,last_seen,metadata,created_at FROM remote_agents ORDER BY name").fetchall()
    now = datetime.now(timezone.utc)
    result = []
    for r in rows:
        online = bool(r[3] and (now - r[3]).total_seconds() < 90)
        result.append({"id": str(r[0]), "name": r[1], "status": "online" if online else "offline", "last_seen": r[3].isoformat() if r[3] else None, "metadata": r[4], "created_at": r[5].isoformat()})
    return result


@app.post("/api/v1/control/agents/heartbeat")
def control_heartbeat(req: AgentHeartbeat, authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require(authorization, _agent_token(), "agent unauthorized")
    with _db() as conn:
        if req.agent_id:
            row = conn.execute("SELECT id FROM remote_agents WHERE id=%s", (req.agent_id,)).fetchone()
        else:
            row = conn.execute("SELECT id FROM remote_agents WHERE name=%s", (req.name,)).fetchone()
        agent_id = row[0] if row else uuid4()
        conn.execute("""INSERT INTO remote_agents(id,name,last_seen,status,metadata) VALUES(%s,%s,now(),'online',%s)
                       ON CONFLICT(name) DO UPDATE SET last_seen=now(),status='online',metadata=EXCLUDED.metadata""", (agent_id, req.name, Jsonb(req.metadata)))
        conn.commit()
        if not row:
            agent_id = conn.execute("SELECT id FROM remote_agents WHERE name=%s", (req.name,)).fetchone()[0]
    return {"agent_id": str(agent_id), "status": "online", "server_time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/v1/control/tasks")
def control_create_task(req: TaskRequest, authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require(authorization, _operator_token(), "operator unauthorized")
    approval = _approval(req.command)
    with _db() as conn:
        if not conn.execute("SELECT 1 FROM remote_agents WHERE id=%s", (req.agent_id,)).fetchone():
            raise HTTPException(status_code=404, detail="agent not found")
        task_id = uuid4()
        conn.execute("INSERT INTO remote_tasks(id,agent_id,command,cwd,approval,requested_by) VALUES(%s,%s,%s,%s,%s,%s)", (task_id, req.agent_id, req.command, req.cwd, approval, req.requested_by))
        conn.commit()
    return {"task_id": str(task_id), "status": "queued", "approval": approval}


@app.get("/api/v1/control/agents/{agent_id}/tasks/next")
def control_next_task(agent_id: UUID, authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require(authorization, _agent_token(), "agent unauthorized")
    with _db() as conn:
        row = conn.execute("""SELECT id,command,cwd,approval FROM remote_tasks
                              WHERE agent_id=%s AND status='queued' AND approval='AUTO' AND NOT cancel_requested
                              ORDER BY created_at LIMIT 1 FOR UPDATE SKIP LOCKED""", (agent_id,)).fetchone()
        if not row:
            return {"task": None}
        conn.execute("UPDATE remote_tasks SET status='running',started_at=now() WHERE id=%s", (row[0],))
        conn.commit()
    return {"task": {"id": str(row[0]), "command": row[1], "cwd": row[2], "approval": row[3]}}


@app.post("/api/v1/control/tasks/{task_id}/events")
def control_event(task_id: UUID, req: EventRequest, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _require(authorization, _agent_token(), "agent unauthorized")
    with _db() as conn:
        conn.execute("INSERT INTO remote_task_events(task_id,stream,message) VALUES(%s,%s,%s)", (task_id, req.stream, req.message))
        conn.commit()
    return {"status": "accepted"}


@app.post("/api/v1/control/tasks/{task_id}/complete")
def control_complete(task_id: UUID, req: CompleteRequest, authorization: str | None = Header(default=None)) -> dict[str, object]:
    _require(authorization, _agent_token(), "agent unauthorized")
    status = "succeeded" if req.returncode == 0 else "failed"
    with _db() as conn:
        changed = conn.execute("UPDATE remote_tasks SET status=%s,returncode=%s,stdout=%s,stderr=%s,finished_at=now() WHERE id=%s AND status='running'", (status, req.returncode, req.stdout, req.stderr, task_id)).rowcount
        conn.commit()
    if not changed:
        raise HTTPException(status_code=404, detail="running task not found")
    return {"status": status, "task_id": str(task_id)}


@app.post("/api/v1/control/tasks/{task_id}/cancel")
def control_cancel(task_id: UUID, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        changed = conn.execute("UPDATE remote_tasks SET cancel_requested=true,status=CASE WHEN status='queued' THEN 'cancelled' ELSE status END WHERE id=%s AND status IN ('queued','running')", (task_id,)).rowcount
        conn.commit()
    if not changed:
        raise HTTPException(status_code=404, detail="task not found")
    return {"task_id": str(task_id), "status": "cancel_requested"}


@app.get("/api/v1/control/tasks")
def control_tasks(authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        rows = conn.execute("""SELECT id,agent_id,command,cwd,status,approval,requested_by,returncode,stdout,stderr,created_at,started_at,finished_at
                              FROM remote_tasks ORDER BY created_at DESC LIMIT 100""").fetchall()
    return [{"id": str(r[0]), "agent_id": str(r[1]), "command": r[2], "cwd": r[3], "status": r[4], "approval": r[5], "requested_by": r[6], "returncode": r[7], "stdout": r[8], "stderr": r[9], "created_at": r[10].isoformat(), "started_at": r[11].isoformat() if r[11] else None, "finished_at": r[12].isoformat() if r[12] else None} for r in rows]


@app.get("/api/v1/control/tasks/{task_id}/events")
def control_task_events(task_id: UUID, authorization: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require(authorization, _operator_token(), "operator unauthorized")
    with _db() as conn:
        rows = conn.execute("SELECT stream,message,created_at FROM remote_task_events WHERE task_id=%s ORDER BY id", (task_id,)).fetchall()
    return [{"stream": r[0], "message": r[1], "created_at": r[2].isoformat()} for r in rows]
