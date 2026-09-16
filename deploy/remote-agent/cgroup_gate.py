#!/usr/bin/env python3
"""Gate target-host cgroup rehearsal on the read-only capability contract.

This wrapper never mutates cgroups or systemd configuration. It only runs the
existing destructive rehearsal when the probe reports READY and the caller
explicitly opts in.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROBE_PATH = ROOT / "cgroup_probe.py"
REHEARSAL_PATH = ROOT / "cgroup_rehearsal.py"

EXIT_PASS = 0
EXIT_NOT_READY = 3
EXIT_NOT_OPTED_IN = 4
EXIT_REHEARSAL_FAILED = 5
EXIT_INTERNAL = 6


def _load_probe():
    spec = importlib.util.spec_from_file_location("logistics_remote_agent_cgroup_probe", PROBE_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load cgroup capability probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("LOGISTICS_CGROUP_REHEARSAL") != "1":
        print("BLOCKED: set LOGISTICS_CGROUP_REHEARSAL=1 to authorize the destructive rehearsal", file=sys.stderr)
        return EXIT_NOT_OPTED_IN

    if os.geteuid() == 0:
        print("BLOCKED: rehearsal must run as the non-root logistics-agent identity", file=sys.stderr)
        return EXIT_NOT_READY

    try:
        probe = _load_probe().probe()
    except Exception as exc:  # pragma: no cover - defensive operator-facing gate
        print(f"INTERNAL: capability probe failed: {exc}", file=sys.stderr)
        return EXIT_INTERNAL

    print(json.dumps(probe, indent=2, sort_keys=True))
    if probe.get("target_host_readiness") != "READY":
        print(
            f"BLOCKED: target_host_readiness={probe.get('target_host_readiness')!r}; "
            "refusing destructive rehearsal",
            file=sys.stderr,
        )
        return EXIT_NOT_READY

    try:
        completed = subprocess.run(
            [sys.executable, str(REHEARSAL_PATH)],
            check=False,
            env=os.environ.copy(),
        )
    except OSError as exc:
        print(f"INTERNAL: cannot start cgroup rehearsal: {exc}", file=sys.stderr)
        return EXIT_INTERNAL

    if completed.returncode != 0:
        print(
            f"FAILED: cgroup rehearsal exited with status {completed.returncode}",
            file=sys.stderr,
        )
        return EXIT_REHEARSAL_FAILED

    print("PASS: target-host cgroup rehearsal completed")
    return EXIT_PASS


if __name__ == "__main__":
    raise SystemExit(main())
