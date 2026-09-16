#!/usr/bin/env python3
"""Report Linux cgroup-v2 capabilities relevant to per-task fencing.

The probe is deliberately read-only. It never creates, moves, or kills
processes and never changes cgroup configuration.
"""
from __future__ import annotations

import json
import os
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


def probe() -> dict[str, object]:
    root = CGROUP_ROOT
    own = _self_cgroup_path()
    own_exists = bool(own and own.is_dir())
    result: dict[str, object] = {
        "linux": os.name == "posix" and Path("/proc/version").exists(),
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "gid": os.getgid(),
        "egid": os.getegid(),
        "cgroup_root": str(root),
        "cgroup_v2_mount": (root / "cgroup.controllers").is_file(),
        "self_cgroup": str(own) if own else None,
        "self_cgroup_exists": own_exists,
        "cgroup_kill_available": bool(own and (own / "cgroup.kill").is_file()),
        "cgroup_procs_available": bool(own and (own / "cgroup.procs").is_file()),
        "subtree_control_available": bool(own and (own / "cgroup.subtree_control").is_file()),
        "subtree_control_writable": bool(own and os.access(own / "cgroup.subtree_control", os.W_OK)),
        "cgroup_procs_writable": bool(own and os.access(own / "cgroup.procs", os.W_OK)),
        "task_cgroup_parent_writable": bool(own and os.access(own, os.W_OK | os.X_OK)),
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

    result["task_cgroup_creation_ready"] = all(
        (
            result["linux"],
            result["cgroup_v2_mount"],
            result["self_cgroup_exists"],
            result["cgroup_kill_available"],
            result["cgroup_procs_available"],
            result["task_cgroup_parent_writable"],
        )
    )
    return result


def main() -> int:
    print(json.dumps(probe(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
