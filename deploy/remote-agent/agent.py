#!/usr/bin/env python3
"""Minimal production-oriented Ubuntu agent.

The agent executes only explicitly allowed commands in registered workspaces and
uses Vercel AI Gateway for model calls. It is intentionally local-only by default;
put a TLS/authenticated reverse proxy or private network in front of it if remote
Android access is required.
"""
from __future__ import annotations

import asyncio
import hmac
import json
import os
import shlex
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

APP = FastAPI(title="Logistics Remote Agent", version="0.1.1")
TOKEN = os.environ.get("AGENT_AUTH_TOKEN", "")
WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", "/opt/logistics"))
GATEWAY_URL = os.environ.get("AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1")
GATEWAY_KEY = os.environ.get("AI_GATEWAY_API_KEY", "")
MODEL = os.environ.get("AI_MODEL", "openai/gpt-6-astra")
MAX_SECONDS = int(os.environ.get("AGENT_COMMAND_TIMEOUT", "120"))

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
    # Prevent obvious shell composition. The agent is not a browser-controlled root shell.
    if any(x in command for x in ("&&", "||", ";", "|", ">", "<", "`", "$(")):
        raise HTTPException(status_code=403, detail="shell composition is disabled")
    return argv


@APP.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "workspace": str(WORKSPACE), "model": MODEL}


@APP.post("/v1/exec")
async def execute(req: ExecRequest, authorization: str | None = Header(default=None)) -> JSONResponse:
    auth(authorization)
    cwd = safe_cwd(req.cwd)
    argv = validate_command(req.command)
    if not cwd.exists():
        raise HTTPException(status_code=404, detail="cwd does not exist")
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(Path.home())},
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=MAX_SECONDS)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(status_code=408, detail="command timed out")
    return JSONResponse({
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
        "command": req.command,
        "cwd": str(cwd),
    })


@APP.post("/v1/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> JSONResponse:
    auth(authorization)
    if not GATEWAY_KEY:
        raise HTTPException(status_code=503, detail="AI_GATEWAY_API_KEY is not configured")
    try:
        import urllib.request
        payload = json.dumps({
            "model": req.model or MODEL,
            "messages": [
                {"role": "system", "content": "You are the operations brain for an Ubuntu logistics server agent. Propose safe, explicit actions. Never assume secrets."},
                {"role": "user", "content": req.prompt},
            ],
        }).encode()
        request = urllib.request.Request(
            f"{GATEWAY_URL.rstrip('/')}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"},
            method="POST",
        )
        loop = asyncio.get_running_loop()
        raw = await loop.run_in_executor(None, lambda: urllib.request.urlopen(request, timeout=120).read())
        data = json.loads(raw)
        return JSONResponse({"model": req.model or MODEL, "response": data})
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI Gateway request failed: {exc}")
