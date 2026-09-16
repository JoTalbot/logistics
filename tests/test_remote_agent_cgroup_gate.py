"""Regression coverage for the target-host cgroup rehearsal gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
GATE_PATH = ROOT / "deploy" / "remote-agent" / "cgroup_gate.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("logistics_remote_agent_cgroup_gate", GATE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gate_requires_explicit_opt_in(monkeypatch, capsys):
    gate = _load_gate()
    monkeypatch.delenv("LOGISTICS_CGROUP_REHEARSAL", raising=False)

    assert gate.main() == gate.EXIT_NOT_OPTED_IN
    assert "destructive rehearsal" in capsys.readouterr().err


def test_gate_refuses_root_even_with_opt_in(monkeypatch, capsys):
    gate = _load_gate()
    monkeypatch.setenv("LOGISTICS_CGROUP_REHEARSAL", "1")
    monkeypatch.setattr(gate.os, "geteuid", lambda: 0)

    assert gate.main() == gate.EXIT_NOT_READY
    assert "non-root logistics-agent" in capsys.readouterr().err


def test_gate_refuses_blocked_readiness_without_running_rehearsal(monkeypatch, capsys):
    gate = _load_gate()
    monkeypatch.setenv("LOGISTICS_CGROUP_REHEARSAL", "1")
    monkeypatch.setattr(gate.os, "geteuid", lambda: 1001)
    monkeypatch.setattr(gate, "_load_probe", lambda: type("Probe", (), {"probe": staticmethod(lambda: {"target_host_readiness": "BLOCKED"})})())
    calls = []
    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: calls.append(args))

    assert gate.main() == gate.EXIT_NOT_READY
    assert calls == []
    assert "target_host_readiness='BLOCKED'" in capsys.readouterr().err


def test_gate_runs_rehearsal_only_after_ready(monkeypatch, capsys):
    gate = _load_gate()
    monkeypatch.setenv("LOGISTICS_CGROUP_REHEARSAL", "1")
    monkeypatch.setattr(gate.os, "geteuid", lambda: 1001)
    monkeypatch.setattr(
        gate,
        "_load_probe",
        lambda: type("Probe", (), {"probe": staticmethod(lambda: {"target_host_readiness": "READY"})})(),
    )
    calls = []

    class Completed:
        returncode = 0

    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)) or Completed())

    assert gate.main() == gate.EXIT_PASS
    assert len(calls) == 1
    assert calls[0][0][0][0] == gate.sys.executable
    assert str(gate.REHEARSAL_PATH) in calls[0][0][0]
    assert "PASS: target-host cgroup rehearsal completed" in capsys.readouterr().out


def test_gate_normalizes_rehearsal_failure(monkeypatch, capsys):
    gate = _load_gate()
    monkeypatch.setenv("LOGISTICS_CGROUP_REHEARSAL", "1")
    monkeypatch.setattr(gate.os, "geteuid", lambda: 1001)
    monkeypatch.setattr(
        gate,
        "_load_probe",
        lambda: type("Probe", (), {"probe": staticmethod(lambda: {"target_host_readiness": "READY"})})(),
    )

    class Completed:
        returncode = 9

    monkeypatch.setattr(gate.subprocess, "run", lambda *args, **kwargs: Completed())

    assert gate.main() == gate.EXIT_REHEARSAL_FAILED
    assert "exited with status 9" in capsys.readouterr().err
