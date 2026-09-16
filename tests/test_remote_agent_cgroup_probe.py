"""Regression coverage for the read-only remote-agent cgroup capability probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).parents[1]
PROBE_PATH = ROOT / "deploy" / "remote-agent" / "cgroup_probe.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("logistics_remote_agent_cgroup_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_is_read_only_and_reports_missing_cgroup_v2(monkeypatch):
    probe = _load_probe()
    fake_root = ROOT / "does-not-exist-cgroup"
    monkeypatch.setattr(probe, "CGROUP_ROOT", fake_root)
    monkeypatch.setattr(probe.Path, "read_text", lambda self, **kwargs: "")
    monkeypatch.setattr(probe.shutil, "which", lambda command: None)

    result = probe.probe()

    assert result["cgroup_v2_mount"] is False
    assert result["self_cgroup"] is None
    assert result["cgroup_kill_available"] is False
    assert result["cgroup_kill_writable"] is False
    assert result["cgroup_procs_writable"] is False
    assert result["subtree_control_writable"] is False
    assert result["task_cgroup_parent_writable"] is False
    assert result["systemd_run_available"] is False
    assert result["target_host_readiness"] == "UNSUPPORTED"
    assert result["target_host_profile"] is None
    assert result["task_scope_backend_candidate"] is None
    assert result["task_cgroup_creation_ready"] is False


def test_probe_reports_v2_files_and_permissions_without_writing(monkeypatch, tmp_path):
    probe = _load_probe()
    root = tmp_path / "cgroup"
    root.mkdir()
    (root / "cgroup.controllers").write_text("cpu memory pids", encoding="utf-8")
    own = root / "agent"
    own.mkdir()
    (own / "cgroup.kill").write_text("", encoding="utf-8")
    (own / "cgroup.procs").write_text("123", encoding="utf-8")
    (own / "cgroup.subtree_control").write_text("cpu", encoding="utf-8")

    monkeypatch.setattr(probe, "CGROUP_ROOT", root)
    monkeypatch.setattr(probe, "_self_cgroup_path", lambda: own)
    monkeypatch.setattr(probe.os, "access", lambda path, mode: mode & probe.os.W_OK != 0)
    monkeypatch.setattr(probe.shutil, "which", lambda command: "/usr/bin/systemd-run" if command == "systemd-run" else "/usr/bin/systemctl")
    monkeypatch.setattr(probe, "_command_version", lambda command: "systemd 256" if command == "systemctl" else None)

    result = probe.probe()

    assert result["cgroup_v2_mount"] is True
    assert result["self_cgroup"] == str(own)
    assert result["cgroup_kill_available"] is True
    assert result["cgroup_kill_writable"] is True
    assert result["cgroup_procs_available"] is True
    assert result["subtree_control_available"] is True
    assert result["subtree_control_writable"] is True
    assert result["cgroup_procs_writable"] is True
    assert result["task_cgroup_parent_writable"] is True
    assert result["task_cgroup_creation_ready"] is True
    assert result["systemd_run_available"] is True
    assert result["systemd_run_path"] == "/usr/bin/systemd-run"
    assert result["systemd_version"] == "systemd 256"
    assert result["target_host_readiness"] == "READY"
    assert result["target_host_profile"] == "linux_cgroup_v2_systemd"
    assert result["task_scope_backend_candidate"] == "systemd-run-scope"
    assert result["controllers"] == ["cpu", "memory", "pids"]
    assert result["enabled_subtree_controllers"] == ["cpu"]


def test_probe_marks_existing_but_undelegated_host_blocked(monkeypatch, tmp_path):
    probe = _load_probe()
    root = tmp_path / "cgroup"
    root.mkdir()
    (root / "cgroup.controllers").write_text("cpu memory pids", encoding="utf-8")
    own = root / "agent"
    own.mkdir()
    (own / "cgroup.kill").write_text("", encoding="utf-8")
    (own / "cgroup.procs").write_text("123", encoding="utf-8")
    (own / "cgroup.subtree_control").write_text("cpu", encoding="utf-8")

    monkeypatch.setattr(probe, "CGROUP_ROOT", root)
    monkeypatch.setattr(probe, "_self_cgroup_path", lambda: own)
    monkeypatch.setattr(probe.os, "access", lambda path, mode: path != own or mode == probe.os.W_OK)
    monkeypatch.setattr(probe.shutil, "which", lambda command: "/usr/bin/systemd-run" if command == "systemd-run" else "/usr/bin/systemctl")
    monkeypatch.setattr(probe, "_command_version", lambda command: "systemd 256")

    result = probe.probe()

    assert result["cgroup_procs_writable"] is True
    assert result["cgroup_kill_writable"] is True
    assert result["task_cgroup_parent_writable"] is False
    assert result["task_cgroup_creation_ready"] is False
    assert result["target_host_readiness"] == "BLOCKED"
    assert result["target_host_profile"] == "linux_cgroup_v2_systemd"


def test_probe_marks_non_writable_cgroup_kill_blocked(monkeypatch, tmp_path):
    probe = _load_probe()
    root = tmp_path / "cgroup"
    root.mkdir()
    (root / "cgroup.controllers").write_text("cpu memory pids", encoding="utf-8")
    own = root / "agent"
    own.mkdir()
    kill = own / "cgroup.kill"
    kill.write_text("", encoding="utf-8")
    (own / "cgroup.procs").write_text("123", encoding="utf-8")
    (own / "cgroup.subtree_control").write_text("cpu", encoding="utf-8")

    monkeypatch.setattr(probe, "CGROUP_ROOT", root)
    monkeypatch.setattr(probe, "_self_cgroup_path", lambda: own)
    monkeypatch.setattr(probe.os, "access", lambda path, mode: path != kill)
    monkeypatch.setattr(probe.shutil, "which", lambda command: "/usr/bin/systemd-run" if command == "systemd-run" else "/usr/bin/systemctl")
    monkeypatch.setattr(probe, "_command_version", lambda command: "systemd 256")

    result = probe.probe()

    assert result["cgroup_kill_available"] is True
    assert result["cgroup_kill_writable"] is False
    assert result["cgroup_procs_writable"] is True
    assert result["task_cgroup_parent_writable"] is True
    assert result["task_cgroup_creation_ready"] is False
    assert result["target_host_readiness"] == "BLOCKED"


def test_probe_does_not_invoke_systemd_actions(monkeypatch, tmp_path):
    probe = _load_probe()
    root = tmp_path / "cgroup"
    root.mkdir()
    (root / "cgroup.controllers").write_text("cpu", encoding="utf-8")
    own = root / "agent"
    own.mkdir()
    for name in ("cgroup.kill", "cgroup.procs", "cgroup.subtree_control"):
        (own / name).write_text("", encoding="utf-8")

    monkeypatch.setattr(probe, "CGROUP_ROOT", root)
    monkeypatch.setattr(probe, "_self_cgroup_path", lambda: own)
    monkeypatch.setattr(probe.os, "access", lambda path, mode: True)
    monkeypatch.setattr(probe.shutil, "which", lambda command: "/usr/bin/systemd-run" if command == "systemd-run" else "/usr/bin/systemctl")
    monkeypatch.setattr(probe, "_command_version", lambda command: "systemd 256")
    calls = []
    monkeypatch.setattr(probe.subprocess, "run", lambda *args, **kwargs: calls.append(args) or None)

    probe.probe()

    assert calls == []
