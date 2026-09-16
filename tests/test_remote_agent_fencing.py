"""Regression coverage for stale lifecycle writes after local lease fencing."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
AGENT_PATH = ROOT / "deploy" / "remote-agent" / "agent.py"


def _load_agent():
    spec = importlib.util.spec_from_file_location("logistics_remote_agent_fencing", AGENT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_lease_loss_skips_stale_event_and_completion_writes(monkeypatch):
    agent = _load_agent()
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    async def fenced_run_leased_command(item):
        return {
            "ok": False,
            "returncode": -9,
            "stdout": "partial-output",
            "stderr": "task lease lost; local process terminated",
            "command": item["command"],
            "cwd": item["cwd"],
            "lease_lost": True,
        }

    def fake_control_request(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
        calls.append((path, method, payload))
        return {"status": "accepted"}

    monkeypatch.setattr(agent, "run_leased_command", fenced_run_leased_command)
    monkeypatch.setattr(agent, "control_request", fake_control_request)

    asyncio.run(agent.execute_control_task({"id": "task-1", "command": "pwd", "cwd": str(ROOT)}))

    assert calls == []
