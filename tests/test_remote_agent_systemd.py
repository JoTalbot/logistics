"""Regression coverage for the remote-agent systemd process boundary."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
INSTALL = ROOT / "deploy" / "remote-agent" / "install.sh"


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
