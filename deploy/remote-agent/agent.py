#!/usr/bin/env python3
"""Ubuntu logistics agent with local API and outbound Vercel control channel."""
from __future__ import annotations

import asyncio
import hmac
import json
import os
import shlex
import signal
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

APP = FastAPI(title="Logistics Remote Agent", version="0.3.0")
TOKEN = os.environ.get("AGENT_AUTH_TOKEN", "")
WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", "/opt/logistics"))
GATEWAY_URL = os.environ.get("AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1")
GATEWAY_KEY = os.environ.get("AI_GATEWAY_API_KEY", "")
MODEL_RAW = os.environ.get("AI_MODEL", "openai/gpt-6-astra")
MODEL_PREFERRED = [m.strip() for m in os.environ.get("AI_MODEL_PREFERRED", "openai/gpt-6-astra").split(",") if m.strip()]
MODEL_CANDIDATES = [m.strip() for m in os.environ.get("AI_MODEL_CANDIDATES", "").split(",") if m.strip()]
MODEL_CACHE_SECONDS = int(os.environ.get("AI_MODEL_CACHE_SECONDS", "900"))
MAX_SECONDS = int(os.environ.get("AGENT_COMMAND_TIMEOUT", "120"))
CONTROL_URL = os.environ.get("CONTROL_PLANE_URL", "").rstrip("/")
CONTROL_TOKEN = os.environ.get("CONTROL_PLANE_TOKEN", "")
CONTROL_AGENT_TOKEN = os.environ.get("CONTROL_AGENT_TOKEN", "")
VERCEL_BYPASS_SECRET = os.environ.get("VERCEL_AUTOMATION_BYPASS_SECRET", "")
AGENT_NAME = os.environ.get("AGENT_NAME", os.uname().nodename)
HEARTBEAT_SECONDS = int(os.environ.get("AGENT_HEARTBEAT_SECONDS", "30"))

ALLOWED = {
    "pwd", "ls", "git", "docker", "docker-compose", "python", "pytest",
    "systemctl", "journalctl", "df", "free", "uptime", "uname", "whoami", "date",
}

MODEL_CACHE: dict[str, Any] = {}

SYSTEM_PROMPT = (
    "You are the operations brain for an Ubuntu logistics server agent. "
    "Propose safe, explicit actions. Never assume secrets."
)


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


def candidate_models() -> list[str]:
    """Ordered list of models to try: the preferred one first, then fallbacks."""
    if MODEL_RAW.strip().lower() == "auto":
        preferred = MODEL_PREFERRED
    else:
        preferred = [MODEL_RAW]
    ordered: list[str] = []
    for model in preferred + MODEL_CANDIDATES:
        if model and model not in ordered:
            ordered.append(model)
    return ordered


def gateway_chat(model: str, messages: list[dict[str, str]], max_tokens: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "messages": messages}
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    request = urllib.request.Request(
        f"{GATEWAY_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read())


def probe_model(model: str) -> bool:
    """A one-token request proves the key may use this model right now."""
    try:
        gateway_chat(model, [{"role": "user", "content": "ping"}], max_tokens=1)
    except Exception:
        return False
    return True


def resolve_model() -> str:
    """Return the configured model, or the first usable one when AI_MODEL=auto."""
    candidates = candidate_models()
    if MODEL_RAW.strip().lower() != "auto":
        return candidates[0]
    now = time.monotonic()
    cached = MODEL_CACHE.get("model")
    if cached and now - float(MODEL_CACHE.get("at", 0.0)) < MODEL_CACHE_SECONDS:
        return str(cached)
    for model in candidates:
        if probe_model(model):
            MODEL_CACHE.update(model=model, at=now)
            return model
    raise HTTPException(status_code=502, detail="no AI Gateway model is available for the configured key")


@APP.on_event("startup")
async def start_control_channel() -> None:
    if CONTROL_URL and CONTROL_TOKEN:
        asyncio.create_task(control_loop())


@APP.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "workspace": str(WORKSPACE),
        "model": MODEL_RAW,
        "model_resolved": MODEL_CACHE.get("model") if MODEL_RAW.strip().lower() == "auto" else MODEL_RAW,
        "control_plane": bool(CONTROL_URL and CONTROL_TOKEN),
        "control_credential_mode": "per_agent" if CONTROL_AGENT_TOKEN else "bootstrap_pending",
        "vercel_bypass": bool(VERCEL_BYPASS_SECRET),
        "agent_name": AGENT_NAME,
    }


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
    proc: asyncio.subprocess.Process | None = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            cwd=str(target),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(Path.home())},
            start_new_session=(os.name == "posix"),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=MAX_SECONDS)
    except asyncio.TimeoutError:
        if proc is not None:
            terminate_process(proc)
            await proc.wait()
        raise HTTPException(status_code=408, detail="command timed out")
    return {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout": stdout.decode(errors="replace"), "stderr": stderr.decode(errors="replace"), "command": command, "cwd": str(target)}


def terminate_process(proc: asyncio.subprocess.Process) -> None:
    """Terminate the task process group so spawned children cannot outlive the lease."""
    pid = getattr(proc, "pid", None)
    if os.name == "posix" and pid:
        try:
            os.killpg(pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    try:
        proc.kill()
    except ProcessLookupError:
        pass


async def run_leased_command(item: dict[str, Any]) -> dict[str, Any]:
    """Execute a leased command with renewal, bounded runtime, and local process fencing."""
    target = safe_cwd(item.get("cwd"))
    argv = validate_command(item["command"])
    if not target.exists():
        raise HTTPException(status_code=404, detail="cwd does not exist")
    proc = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(target),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(Path.home())},
        start_new_session=(os.name == "posix"),
    )

    async def lease_watchdog() -> str | None:
        interval = max(5, min(HEARTBEAT_SECONDS, 30))
        while proc.returncode is None:
            await asyncio.sleep(interval)
            try:
                response = await asyncio.to_thread(
                    control_request,
                    f"/api/v1/control/tasks/{item['id']}/events",
                    "POST",
                    {"stream": "heartbeat", "message": ""},
                )
                if response.get("error") in (401, 409):
                    return "task lease lost; local process terminated"
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 409):
                    return "task lease lost; local process terminated"
                print(f"task lease heartbeat error: HTTP {exc.code}", flush=True)
            except Exception as exc:
                print(f"task lease heartbeat error: {type(exc).__name__}: {exc}", flush=True)
        return None

    communication = asyncio.create_task(proc.communicate())
    watchdog = asyncio.create_task(lease_watchdog())
    timeout = asyncio.create_task(asyncio.sleep(MAX_SECONDS))
    try:
        done, _ = await asyncio.wait(
            {communication, watchdog, timeout}, return_when=asyncio.FIRST_COMPLETED
        )
        if watchdog in done:
            reason = watchdog.result()
            if reason:
                terminate_process(proc)
                stdout, stderr = await communication
                return {
                    "ok": False,
                    "returncode": proc.returncode if proc.returncode is not None else -9,
                    "stdout": stdout.decode(errors="replace"),
                    "stderr": (stderr.decode(errors="replace") + "\n" + reason).strip(),
                    "command": item["command"],
                    "cwd": str(target),
                    "lease_lost": True,
                }
        if timeout in done and communication not in done:
            terminate_process(proc)
            stdout, stderr = await communication
            return {
                "ok": False,
                "returncode": 408,
                "stdout": stdout.decode(errors="replace"),
                "stderr": (stderr.decode(errors="replace") + "\ncommand timed out").strip(),
                "command": item["command"],
                "cwd": str(target),
                "lease_lost": False,
            }
        stdout, stderr = await communication
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "command": item["command"],
            "cwd": str(target),
            "lease_lost": False,
        }
    finally:
        if not watchdog.done():
            watchdog.cancel()
            await asyncio.gather(watchdog, return_exceptions=True)
        if not timeout.done():
            timeout.cancel()
            await asyncio.gather(timeout, return_exceptions=True)


@APP.post("/v1/chat")
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> JSONResponse:
    auth(authorization)
    if not GATEWAY_KEY:
        raise HTTPException(status_code=503, detail="AI_GATEWAY_API_KEY is not configured")
    try:
        model = req.model or await asyncio.to_thread(resolve_model)
        payload = await asyncio.to_thread(
            gateway_chat,
            model,
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": req.prompt}],
        )
        return JSONResponse({"model": model, "response": payload})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI Gateway request failed: {exc}")


def control_request(
    path: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    *,
    bootstrap: bool = False,
) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    token = CONTROL_TOKEN if bootstrap else (CONTROL_AGENT_TOKEN or CONTROL_TOKEN)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "logistics-remote-agent/0.3.0",
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


async def execute_control_task(item: dict[str, Any]) -> None:
    """Run a leased task and always attempt to move it to a terminal state."""
    try:
        result = await run_leased_command(item)
    except HTTPException as exc:
        result = {
            "returncode": exc.status_code or 1,
            "stdout": "",
            "stderr": str(exc.detail),
        }
    except Exception as exc:
        result = {
            "returncode": 1,
            "stdout": "",
            "stderr": f"agent execution error: {type(exc).__name__}: {exc}",
        }

    try:
        await asyncio.to_thread(control_request, f"/api/v1/control/tasks/{item['id']}/events", "POST", {"stream": "stdout", "message": result.get("stdout", "")})
        if result.get("stderr"):
            await asyncio.to_thread(control_request, f"/api/v1/control/tasks/{item['id']}/events", "POST", {"stream": "stderr", "message": result["stderr"]})
    except Exception as exc:
        print(f"task event reporting error: {type(exc).__name__}: {exc}", flush=True)

    try:
        await asyncio.to_thread(control_request, f"/api/v1/control/tasks/{item['id']}/complete", "POST", {"returncode": result["returncode"], "stdout": result["stdout"], "stderr": result["stderr"]})
    except Exception as exc:
        print(f"task completion error: {type(exc).__name__}: {exc}", flush=True)


async def control_loop() -> None:
    global CONTROL_AGENT_TOKEN
    agent_id: str | None = None
    tenant_id: str | None = None
    while True:
        try:
            bootstrapping = agent_id is None
            heartbeat_payload: dict[str, Any] = {
                "name": AGENT_NAME,
                "metadata": {"hostname": os.uname().nodename, "workspace": str(WORKSPACE), "model": MODEL_RAW},
            }
            if agent_id:
                heartbeat_payload["agent_id"] = agent_id
                heartbeat_payload["tenant_id"] = tenant_id
            heartbeat = await asyncio.to_thread(
                control_request,
                "/api/v1/control/agents/heartbeat",
                "POST",
                heartbeat_payload,
                bootstrap=bootstrapping,
            )
            agent_id = heartbeat.get("agent_id") or agent_id
            tenant_id = heartbeat.get("tenant_id") if "tenant_id" in heartbeat else tenant_id
            issued = heartbeat.get("control_token")
            if issued:
                CONTROL_AGENT_TOKEN = str(issued)
            if agent_id and CONTROL_AGENT_TOKEN:
                task = await asyncio.to_thread(control_request, f"/api/v1/control/agents/{agent_id}/tasks/next")
                item = task.get("task")
                if item:
                    await execute_control_task(item)
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                print("control credential rejected; resetting enrollment state", flush=True)
                agent_id = None
                tenant_id = None
                CONTROL_AGENT_TOKEN = ""
            else:
                print(f"control channel error: HTTP {exc.code}", flush=True)
        except Exception as exc:
            print(f"control channel error: {type(exc).__name__}: {exc}", flush=True)
        await asyncio.sleep(HEARTBEAT_SECONDS)
