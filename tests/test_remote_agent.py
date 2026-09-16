"""Unit tests for the remote agent control-task execution boundary."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

from fastapi import HTTPException

_AGENT_PATH = Path(__file__).parents[1] / "deploy" / "remote-agent" / "agent.py"
_SPEC = importlib.util.spec_from_file_location("logistics_remote_agent_test", _AGENT_PATH)
assert _SPEC and _SPEC.loader
agent = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(agent)


def test_execution_error_is_reported_and_task_is_completed(monkeypatch):
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    async def fail_run_leased_command(item):
        raise HTTPException(status_code=403, detail="command not allowed")

    def fake_control_request(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
        calls.append((path, method, payload))
        return {"status": "accepted"}

    monkeypatch.setattr(agent, "run_leased_command", fail_run_leased_command)
    monkeypatch.setattr(agent, "control_request", fake_control_request)

    asyncio.run(agent.execute_control_task({"id": "task-1", "command": "forbidden", "cwd": "/opt/logistics"}))

    assert any(path.endswith("/events") and payload and payload["stream"] == "stderr" for path, _, payload in calls)
    completion = next(payload for path, _, payload in calls if path.endswith("/complete"))
    assert completion == {
        "returncode": 403,
        "stdout": "",
        "stderr": "command not allowed",
    }


def test_remote_agent_does_not_configure_vercel_protection_bypass():
    text = _AGENT_PATH.read_text(encoding="utf-8")

    assert "VERCEL_AUTOMATION_BYPASS_SECRET" not in text
    assert "x-vercel-protection-bypass" not in text
