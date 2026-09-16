#!/usr/bin/env python3
"""Report Linux cgroup-v2/systemd capabilities relevant to per-task fencing.

The probe is deliberately read-only. It never creates, moves, or kills
processes, starts transient units, or changes cgroup/systemd configuration.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

CGROUP_ROOT = Path("/sys/fs/cgroup")


def _self_cgroup_path() -> Path | None:
    try:
        lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0" and parts[1] == "":
            return CGROUP_ROOT / parts[2].lstrip("/")
    return None


def _command_version(command: str) -> str | None:
    """Return a command's version string without invoking a service action."""
    executable = shutil.which(command)
    if not executable:
        return None
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0] if output else None


def _execution_identity() -> str | None:
    try:
        import pwd

        return pwd.getpwuid(os.geteuid()).pw_name
    except (ImportError, KeyError, OSError):
        return None


def probe() -> dict[str, object]:
    root = CGROUP_ROOT
    own = _self_cgroup_path()
    own_exists = bool(own and own.is_dir())
    systemd_run = shutil.which("systemd-run")
    systemd_version = _command_version("systemctl")
    cgroup_kill = bool(own and (own / "cgroup.kill").is_file())
    cgroup_kill_writable = bool(own and os.access(own / "cgroup.kill", os.W_OK))
    cgroup_procs = bool(own and (own / "cgroup.procs").is_file())
    cgroup_procs_writable = bool(own and os.access(own / "cgroup.procs", os.W_OK))
    parent_writable = bool(own and os.access(own, os.W_OK | os.X_OK))
    cgroup_ready = all(
        (
            os.name == "posix" and Path("/proc/version").exists(),
            (root / "cgroup.controllers").is_file(),
            own_exists,
            cgroup_kill,
            cgroup_kill_writable,
            cgroup_procs,
            parent_writable,
        )
    )
    result: dict[str, object] = {
        "linux": os.name == "posix" and Path("/proc/version").exists(),
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "gid": os.getgid(),
        "egid": os.getegid(),
        "execution_identity": _execution_identity(),
        "cgroup_root": str(root),
        "cgroup_v2_mount": (root / "cgroup.controllers").is_file(),
        "self_cgroup": str(own) if own else None,
        "self_cgroup_exists": own_exists,
        "cgroup_kill_available": cgroup_kill,
        "cgroup_kill_writable": cgroup_kill_writable,
        "cgroup_procs_available": cgroup_procs,
        "subtree_control_available": bool(own and (own / "cgroup.subtree_control").is_file()),
        "subtree_control_writable": bool(own and os.access(own / "cgroup.subtree_control", os.W_OK)),
        "cgroup_procs_writable": cgroup_procs_writable,
        "task_cgroup_parent_writable": parent_writable,
        "systemd_run_available": bool(systemd_run),
        "systemd_run_path": systemd_run,
        "systemd_version": systemd_version,
        "task_cgroup_creation_ready": cgroup_ready,
    }
    if own_exists:
        try:
            result["controllers"] = (root / "cgroup.controllers").read_text(encoding="utf-8").split()
            result["enabled_subtree_controllers"] = (own / "cgroup.subtree_control").read_text(encoding="utf-8").split()
        except OSError:
            result["controllers"] = []
            result["enabled_subtree_controllers"] = []
    else:
        result["controllers"] = []
        result["enabled_subtree_controllers"] = []

    if not result["linux"] or not result["cgroup_v2_mount"] or not result["systemd_run_available"]:
        result["target_host_readiness"] = "UNSUPPORTED"
    elif not result["task_cgroup_creation_ready"]:
        result["target_host_readiness"] = "BLOCKED"
    else:
        result["target_host_readiness"] = "READY"

    result["target_host_profile"] = (
        "linux_cgroup_v2_systemd" if result["linux"] and result["cgroup_v2_mount"] and result["systemd_run_available"] else None
    )
    result["task_scope_backend_candidate"] = (
        "systemd-run-scope" if result["systemd_run_available"] else None
    )
    return result


def main() -> int:
    print(json.dumps(probe(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
