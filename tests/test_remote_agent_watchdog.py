"""Unit coverage for remote-agent lease-loss process fencing."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
AGENT_PATH = ROOT / "deploy" / "remote-agent" / "agent.py"


def _load_agent():
    spec = importlib.util.spec_from_file_location("logistics_remote_agent", AGENT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeProcess:
    def __init__(self) -> None:
        self.returncode: int | None = None
        self._finished = asyncio.Event()
        self.killed = False

    async def communicate(self):
        await self._finished.wait()
        return b"partial-output", b""

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9
        self._finished.set()


@pytest.mark.asyncio
async def test_run_leased_command_kills_process_when_lease_is_fenced(monkeypatch):
    agent = _load_agent()
    process = _FakeProcess()

    async def fake_create(*args, **kwargs):
        return process

    async def immediate_sleep(_seconds):
        await asyncio.Event().wait()

    monkeypatch.setattr(agent.asyncio, "create_subprocess_exec", fake_create)
    monkeypatch.setattr(agent.asyncio, "sleep", immediate_sleep)
    monkeypatch.setattr(agent, "safe_cwd", lambda value: ROOT)
    monkeypatch.setattr(agent, "validate_command", lambda command: ["pwd"])
    monkeypatch.setattr(agent, "control_request", lambda *args, **kwargs: {"error": 409})

    watchdog_sleep = asyncio.create_task(asyncio.sleep(0))
    watchdog_sleep.cancel()
    await asyncio.gather(watchdog_sleep, return_exceptions=True)

    async def trigger_watchdog(_seconds):
        raise asyncio.CancelledError

    monkeypatch.setattr(agent.asyncio, "sleep", trigger_watchdog)

    with pytest.raises(asyncio.CancelledError):
        await agent.run_leased_command({"id": "task-1", "command": "pwd", "cwd": str(ROOT)})
