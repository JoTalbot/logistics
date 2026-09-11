#!/usr/bin/env python3
"""Ubuntu logistics agent with local API and outbound Vercel control channel."""
from __future__ import annotations

import asyncio
import hmac
import json
import os
import shlex
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

APP = FastAPI(title="Logistics Remote Agent", version="0.2.1")
TOKEN = os.environ.get("AGENT_AUTH_TOKEN", "")
WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", "/opt/logistics"))
GATEWAY_URL = os.environ.get("AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1")
GATEWAY_KEY = os.environ.get("AI_GATEWAY_API_KEY", "")
MODEL = os.environ.get("AI_MODEL", "openai/gpt-6-astra")
MAX_SECONDS = int(os.environ.get("AGENT_COMMAND_TIMEOUT", "120"))
CONTROL_URL = os.environ.get("CONTROL_PLANE_URL", "").rstrip("/")
CONTROL_TOKEN = os.environ.get("CONTROL_PLANE_TOKEN", "")
VERCEL_BYPASS_SECRET = os.environ.get("VERCEL_AUTOMATION_BYPASS_SECRET", "")
AGENT_NAME = os.environ.get("AGENT_NAME", os.uname().nodename)
HEARTBEAT_SECONDS = int(os.environ.get("AGENT_HEARTBEAT_SECONDS", "30"))

ALLOWED = {
    "pwd", "ls", "git", "docker", "docker-compose", "python", "pytest",
    "systemctl", "journalctl", "df", "free", "uptime", "uname", "whoami",
}

class ExecRequest(BaseModel):
    command: str = Field(min_length=1, max_length=4000)
    cwd: str | None = None

class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    model: str | None = None


def auth(value: str | None) -> None:
    if not TOKEN or not value or not hmac.compare_digest(value, f"Bearer {TOKEN}"):
        raise HTTPException(status_code=401, detail="unauthorized")


def safe_cwd(value: str | None) -> Path:
    path = Path(value or WORKSPACE).resolve()
    root = WORKSPACE.resolve()
    if path != root and root not in path.parents:
        raise HTTPException(status_code=403, detail="cwd outside workspace")
    return path


def validate_command(command: str) -> list[str]:
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid command: {exc}")
    if not argv or argv[0] not in ALLOWED:
        raise HTTPException(status_code=403, detail=f"command not allowed: {argv[0] if argv else ''}")
    if any(x in command for x in ("&&", "||", ";", "|", ">", "<", "`", "$(")):
        raise HTTPException(status_code=403, detail="shell composition is disabled")
    return argv


@APP.on_event("startup")
async def start_control_channel() -> None:
    if CONTROL_URL and CONTROL_TOKEN:
        asyncio.create_task(control_loop())


@APP.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "workspace": str(WORKSPACE), "model": MODEL, "control_plane": bool(CONTROL_URL and CONTROL_TOKEN), "vercel_bypass": bool(VERCEL_BYPASS_SECRET), "agent_name": AGENT_NAME}


@APP.post("/v1/exec")
async def execute(req: ExecRequest, authorization: str | None = Header(default=None)) -> JSONResponse:
    auth(authorization)
    result = await run_command(req.command, req.cwd)
    return JSONResponse(result)


async def run_command(command: str, cwd: str | None = None) -> dict[str, Any]:
    target = safe_cwd(cwd)
    argv = validate_command(command)
    if not target.exists():
        raise HTTPException(status_code=404, detail="cwd does not exist")
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=str(target),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(Path.home())},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=MAX_SECONDS)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(status_code=408, detail="command timed out")
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace"), "command": command, "cwd": str(target)}


@APP.post("/v1/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> JSONResponse:
    auth(authorization)
    if not GATEWAY_KEY:
        raise HTTPException(status_code=503, detail="AI_GATEWAY_API_KEY is not configured")
    try:
        payload = json.dumps({"model": req.model or MODEL, "messages": [{"role": "system", "content": "You are the operations brain for an Ubuntu logistics server agent. Propose safe, explicit actions. Never assume secrets."}, {"role": "user", "content": req.prompt}]}).encode()
        request = urllib.request.Request(f"{GATEWAY_URL.rstrip('/')}/chat/completions", data=payload, headers={"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"}, method="POST")
        loop = asyncio.get_running_loop()
        raw = await loop.run_in_executor(None, lambda: urllib.request.urlopen(request, timeout=120).read())
        return JSONResponse({"model": req.model or MODEL, "response": json.loads(raw)})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI Gateway request failed: {exc}")


def control_request(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Authorization": f"Bearer {CONTROL_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "logistics-remote-agent/0.2.1",
    }
    if VERCEL_BYPASS_SECRET:
        headers["x-vercel-protection-bypass"] = VERCEL_BYPASS_SECRET
    req = urllib.request.Request(f"{CONTROL_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 409):
            return {"error": exc.code}
        raise


async def control_loop() -> None:
    agent_id: str | None = None
    while True:
        try:
            heartbeat = await asyncio.to_thread(control_request, "/api/v1/control/agents/heartbeat", "POST", {"name": AGENT_NAME, "agent_id": agent_id, "metadata": {"hostname": os.uname().nodename, "workspace": str(WORKSPACE), "model": MODEL}})
            agent_id = heartbeat.get("agent_id") or agent_id
            if agent_id:
                task = await asyncio.to_thread(control_request, f"/api/v1/control/agents/{agent_id}/tasks/next")
                item = task.get("task")
                if item:
                    result = await run_command(item["command"], item.get("cwd"))
                    await asyncio.to_thread(control_request, f"/api/v1/control/tasks/{item['id']}/events", "POST", {"stream": "stdout", "message": result.get("stdout", "")})
                    if result.get("stderr"):
                        await asyncio.to_thread(control_request, f"/api/v1/control/tasks/{item['id']}/events", "POST", {"stream": "stderr", "message": result["stderr"]})
                    await asyncio.to_thread(control_request, f"/api/v1/control/tasks/{item['id']}/complete", "POST", {"returncode": result["returncode"], "stdout": result["stdout"], "stderr": result["stderr"]})
        except Exception as exc:
            print(f"control channel error: {type(exc).__name__}: {exc}", flush=True)
        await asyncio.sleep(HEARTBEAT_SECONDS)
