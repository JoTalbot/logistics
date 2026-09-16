"""Regression coverage for the opt-in target-host cgroup rehearsal."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
REHEARSAL = ROOT / "deploy" / "remote-agent" / "cgroup_rehearsal.py"
EVIDENCE = ROOT / "docs" / "REMOTE_AGENT_CGROUP_EVIDENCE.md"


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


def test_rehearsal_refuses_root_identity(monkeypatch):
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


def test_base_evidence_matches_contract():
    rehearsal = _load_rehearsal()
    evidence = rehearsal._base_evidence()
    required = {
        "schema_version", "timestamp_utc", "host", "execution_identity",
        "uid", "euid", "gid", "egid", "kernel", "cgroup_v2_mount",
        "systemd_run", "readiness", "scope", "task_pid",
        "detached_descendant_pid", "task_cgroup", "detached_descendant_cgroup",
        "same_cgroup_before_fence", "cgroup_kill_write",
        "task_alive_before_fence", "detached_descendant_alive_before_fence",
        "task_alive_after_fence", "detached_descendant_alive_after_fence",
        "cleanup", "result",
    }
    assert required <= set(evidence)
    assert evidence["schema_version"] == "1"
    assert evidence["result"] == "NOT_STARTED"


def test_evidence_writer_is_json_and_does_not_write_without_path(monkeypatch, tmp_path):
    rehearsal = _load_rehearsal()
    evidence = rehearsal._base_evidence()
    monkeypatch.delenv(rehearsal.EVIDENCE_PATH, raising=False)
    rehearsal._write_evidence(evidence)
    assert list(tmp_path.iterdir()) == []

    destination = tmp_path / "nested" / "evidence.json"
    monkeypatch.setenv(rehearsal.EVIDENCE_PATH, str(destination))
    rehearsal._write_evidence(evidence)
    loaded = json.loads(destination.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "1"
    assert loaded["result"] == "NOT_STARTED"


def test_evidence_contract_documents_machine_readable_fields():
    text = EVIDENCE.read_text(encoding="utf-8")
    for field in (
        "schema_version", "timestamp_utc", "readiness", "scope",
        "same_cgroup_before_fence", "cgroup_kill_write", "cleanup", "result",
    ):
        assert f"`{field}`" in text
    assert "READY without a successful destructive rehearsal is not sufficient evidence" in text
