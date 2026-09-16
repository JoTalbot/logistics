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


def terminate_process(proc: asyncio.subprocess.Process) -> None:
    """Terminate the task's process group so spawned children cannot outlive the lease."""
    if os.name == "posix" and proc.pid:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
        except OSError:
            pass
    try:
        proc.kill()
    except ProcessLookupError:
        pass


# ...

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


# ...
