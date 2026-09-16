"""Unit coverage for remote-agent lease-loss process fencing."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

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

    async def wait(self):
        return self.returncode

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9
        self._finished.set()


def test_terminate_process_kills_posix_process_group(monkeypatch):
    agent = _load_agent()
    process = _FakeProcess()
    process.pid = 4242
    calls: list[tuple[int, int]] = []

    def fake_killpg(pid, sig):
        calls.append((pid, sig))

    monkeypatch.setattr(agent.os, "killpg", fake_killpg)
    monkeypatch.setattr(agent.os, "name", "posix")

    agent.terminate_process(process)

    assert calls == [(4242, agent.signal.SIGKILL)]
    assert process.killed is False


def test_run_leased_command_kills_process_when_lease_is_fenced(monkeypatch):
    agent = _load_agent()
    process = _FakeProcess()
    real_sleep = asyncio.sleep

    async def fake_create(*args, **kwargs):
        return process

    async def immediate_sleep(_seconds):
        await real_sleep(0)

    monkeypatch.setattr(agent.asyncio, "create_subprocess_exec", fake_create)
    monkeypatch.setattr(agent.asyncio, "sleep", immediate_sleep)
    monkeypatch.setattr(agent, "safe_cwd", lambda value: ROOT)
    monkeypatch.setattr(agent, "validate_command", lambda command: ["pwd"])
    monkeypatch.setattr(agent, "control_request", lambda *args, **kwargs: {"error": 409})

    result = asyncio.run(agent.run_leased_command({"id": "task-1", "command": "pwd", "cwd": str(ROOT)}))

    assert process.killed is True
    assert result["lease_lost"] is True
    assert result["returncode"] == -9
    assert "task lease lost" in result["stderr"]


def test_run_command_kills_process_tree_on_timeout(monkeypatch):
    agent = _load_agent()
    process = _FakeProcess()

    async def fake_create(*args, **kwargs):
        assert kwargs["start_new_session"] is True
        return process

    async def timeout_wait(awaitable, timeout):
        awaitable.close()
        assert timeout == agent.MAX_SECONDS
        raise asyncio.TimeoutError

    monkeypatch.setattr(agent.asyncio, "create_subprocess_exec", fake_create)
    monkeypatch.setattr(agent.asyncio, "wait_for", timeout_wait)
    monkeypatch.setattr(agent, "safe_cwd", lambda value: ROOT)
    monkeypatch.setattr(agent, "validate_command", lambda command: ["pwd"])

    try:
        asyncio.run(agent.run_command("pwd", str(ROOT)))
    except agent.HTTPException as exc:
        assert exc.status_code == 408
        assert exc.detail == "command timed out"
    else:
        raise AssertionError("run_command must reject a timed-out process")

    assert process.killed is True


def test_lifespan_cancels_control_task(monkeypatch):
    agent = _load_agent()
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def fake_control_loop():
        started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(agent, "CONTROL_URL", "https://control.example")
    monkeypatch.setattr(agent, "CONTROL_TOKEN", "bootstrap-token")
    monkeypatch.setattr(agent, "control_loop", fake_control_loop)

    async def exercise():
        async with agent.lifespan(agent.APP):
            await asyncio.wait_for(started.wait(), timeout=1)
        assert cancelled.is_set()

    asyncio.run(exercise())
