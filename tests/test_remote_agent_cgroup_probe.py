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

    result = probe.probe()

    assert result["cgroup_v2_mount"] is False
    assert result["self_cgroup"] is None
    assert result["cgroup_kill_available"] is False
    assert result["cgroup_procs_writable"] is False
    assert result["subtree_control_writable"] is False


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
    monkeypatch.setattr(probe.os, "access", lambda path, mode: mode == probe.os.W_OK)

    result = probe.probe()

    assert result["cgroup_v2_mount"] is True
    assert result["self_cgroup"] == str(own)
    assert result["cgroup_kill_available"] is True
    assert result["cgroup_procs_available"] is True
    assert result["subtree_control_available"] is True
    assert result["subtree_control_writable"] is True
    assert result["cgroup_procs_writable"] is True
    assert result["controllers"] == ["cpu", "memory", "pids"]
    assert result["enabled_subtree_controllers"] == ["cpu"]
