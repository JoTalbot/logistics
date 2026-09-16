"""Regression coverage for the remote-agent systemd process boundary."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
INSTALL = ROOT / "deploy" / "remote-agent" / "install.sh"
README = ROOT / "deploy" / "remote-agent" / "README.md"


def test_remote_agent_service_delegates_and_contains_process_tree() -> None:
    text = INSTALL.read_text(encoding="utf-8")

    assert "User=logistics-agent" in text
    assert "NoNewPrivileges=true" in text
    assert "ProtectSystem=strict" in text
    assert "ProtectHome=true" in text
    assert "KillMode=control-group" in text
    assert "Delegate=yes" in text
    assert "TasksMax=512" in text


def test_remote_agent_service_does_not_expose_public_listener() -> None:
    text = INSTALL.read_text(encoding="utf-8")

    assert "--host 127.0.0.1" in text
    assert "--port 8787" in text


def test_documentation_does_not_overclaim_per_task_cgroup_isolation() -> None:
    text = README.read_text(encoding="utf-8")

    assert "future per-task supervisor" in text
    assert "true per-task cgroup containment remains a separate hardening step" in text
    assert "Do not claim lease fencing as an absolute guarantee" in text
