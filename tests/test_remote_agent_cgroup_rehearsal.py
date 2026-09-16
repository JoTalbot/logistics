"""Regression coverage for the opt-in target-host cgroup rehearsal."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
REHEARSAL = ROOT / "deploy" / "remote-agent" / "cgroup_rehearsal.py"


def _load_rehearsal():
    spec = importlib.util.spec_from_file_location("logistics_remote_agent_cgroup_rehearsal", REHEARSAL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rehearsal_is_disabled_without_explicit_opt_in(monkeypatch, capsys):
    rehearsal = _load_rehearsal()
    monkeypatch.delenv(rehearsal.ENABLE, raising=False)

    assert rehearsal.main() == 2
    assert rehearsal.ENABLE in capsys.readouterr().err


def test_rehearsal_refuses_root_identity(monkeypatch, tmp_path):
    rehearsal = _load_rehearsal()
    monkeypatch.setenv(rehearsal.ENABLE, "1")
    monkeypatch.setattr(rehearsal.os, "name", "posix")
    monkeypatch.setattr(rehearsal.Path, "exists", lambda self: True)
    monkeypatch.setattr(rehearsal.Path, "is_file", lambda self: True)
    monkeypatch.setattr(rehearsal.os, "geteuid", lambda: 0)

    assert rehearsal.main() == 3


def test_rehearsal_rejects_post_spawn_pid_move_design():
    text = REHEARSAL.read_text(encoding="utf-8")

    assert "post-spawn PID moves" in text
    assert "pre-membership race" in text
    assert "systemd-run" in text
    assert "cgroup.kill" in text
    assert "setsid" in text
