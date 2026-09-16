"""Unit tests for the remote agent control-task execution boundary."""
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

import pytest
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


def test_execute_control_task_skips_completion_after_lifecycle_fence(monkeypatch):
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    async def fake_run_leased_command(item):
        return {
            "ok": True,
            "returncode": 0,
            "stdout": "output",
            "stderr": "",
            "lease_lost": False,
        }

    def fake_control_request(path: str, method: str = "GET", payload: dict[str, object] | None = None) -> dict[str, object]:
        calls.append((path, method, payload))
        if path.endswith("/events"):
            return {"error": 409}
        return {"status": "accepted"}

    monkeypatch.setattr(agent, "run_leased_command", fake_run_leased_command)
    monkeypatch.setattr(agent, "control_request", fake_control_request)

    asyncio.run(agent.execute_control_task({"id": "task-2", "command": "pwd", "cwd": "/opt/logistics"}))

    assert any(path.endswith("/events") for path, _, _ in calls)
    assert not any(path.endswith("/complete") for path, _, _ in calls)


def test_remote_agent_does_not_configure_vercel_protection_bypass():
    text = _AGENT_PATH.read_text(encoding="utf-8")

    assert "VERCEL_AUTOMATION_BYPASS_SECRET" not in text
    assert "x-vercel-protection-bypass" not in text


def test_control_request_requires_per_agent_credential(monkeypatch):
    monkeypatch.setattr(agent, "CONTROL_TOKEN", "bootstrap-secret")
    monkeypatch.setattr(agent, "CONTROL_AGENT_TOKEN", "")

    with pytest.raises(HTTPException) as exc:
        agent.control_request("/api/v1/control/agents/agent-1/tasks/next")

    assert exc.value.status_code == 503
    assert "per-agent" in str(exc.value.detail)


def test_control_request_uses_bootstrap_only_when_explicitly_requested(monkeypatch):
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.headers["Authorization"]
        captured["timeout"] = timeout
        captured["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setattr(agent, "CONTROL_URL", "https://control.example.test")
    monkeypatch.setattr(agent, "CONTROL_TOKEN", "bootstrap-secret")
    monkeypatch.setattr(agent, "CONTROL_AGENT_TOKEN", "agent-secret")
    monkeypatch.setattr(agent.urllib.request, "urlopen", fake_urlopen)

    agent.control_request("/api/v1/control/agents/heartbeat", method="POST", payload={}, bootstrap=True)
    assert captured["authorization"] == "Bearer bootstrap-secret"
    assert captured["url"] == "https://control.example.test/api/v1/control/agents/heartbeat"

    agent.control_request("/api/v1/control/agents/agent-1/tasks/next")
    assert captured["authorization"] == "Bearer agent-secret"
    assert captured["url"] == "https://control.example.test/api/v1/control/agents/agent-1/tasks/next"


def test_control_request_never_falls_back_to_bootstrap_for_lifecycle(monkeypatch):
    monkeypatch.setattr(agent, "CONTROL_TOKEN", "bootstrap-secret")
    monkeypatch.setattr(agent, "CONTROL_AGENT_TOKEN", "")

    with pytest.raises(HTTPException):
        agent.control_request("/api/v1/control/tasks/task-1/events", method="POST", payload={"stream": "heartbeat", "message": ""})

    with pytest.raises(HTTPException):
        agent.control_request("/api/v1/control/tasks/task-1/complete", method="POST", payload={"returncode": 0, "stdout": "", "stderr": ""})
