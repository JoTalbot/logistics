#!/usr/bin/env python3
"""Opt-in Linux rehearsal for a systemd-backed per-task cgroup boundary.

This script is intentionally not part of normal CI or remote-agent execution.
It requires an explicit environment flag and a systemd scope that the current
identity is authorized to create. It never falls back to post-spawn PID moves,
because that pattern has a pre-membership race and is not containment evidence.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ENABLE = "LOGISTICS_CGROUP_REHEARSAL"
POLL_SECONDS = 0.1


def _read_cgroup(pid: int) -> Path | None:
    try:
        lines = Path(f"/proc/{pid}/cgroup").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0" and parts[1] == "":
            return Path("/sys/fs/cgroup") / parts[2].lstrip("/")
    return None


def _wait_for_file(path: Path, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return True
        time.sleep(POLL_SECONDS)
    return path.is_file()


def _alive(pid: int) -> bool:
    return Path(f"/proc/{pid}").exists()


def main() -> int:
    if os.name != "posix" or not Path("/proc/version").exists():
        print("SKIP: Linux host required", file=sys.stderr)
        return 2
    if os.environ.get(ENABLE) != "1":
        print(f"SKIP: set {ENABLE}=1 to run the destructive rehearsal", file=sys.stderr)
        return 2
    if os.geteuid() == 0:
        print("REFUSE: run as the dedicated non-root logistics-agent identity", file=sys.stderr)
        return 3
    if not Path("/sys/fs/cgroup/cgroup.controllers").is_file():
        print("REFUSE: cgroup v2 is not mounted", file=sys.stderr)
        return 3

    systemd_run = Path("/usr/bin/systemd-run")
    if not systemd_run.is_file():
        print("REFUSE: /usr/bin/systemd-run is unavailable", file=sys.stderr)
        return 3

    with tempfile.TemporaryDirectory(prefix="logistics-cgroup-rehearsal-") as tmp:
        root = Path(tmp)
        ready = root / "ready"
        task_pid_file = root / "task.pid"
        child_pid_file = root / "child.pid"
        unit = f"logistics-cgroup-rehearsal-{uuid.uuid4().hex[:12]}"
        code = (
            "import os,time; "
            f"open({str(ready)!r}, 'w').close(); "
            f"open({str(task_pid_file)!r}, 'w').write(str(os.getpid())); "
            f"pid=os.fork(); "
            f"(os.setsid(), open({str(child_pid_file)!r}, 'w').write(str(os.getpid())), time.sleep(30)) "
            "if pid == 0 else time.sleep(30)"
        )
        command = [
            str(systemd_run),
            "--scope",
            "--unit",
            unit,
            "--collect",
            "/usr/bin/python3",
            "-c",
            code,
        ]

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            print(f"REFUSE: could not start systemd scope: {exc}", file=sys.stderr)
            return 3

        try:
            if not _wait_for_file(ready, 5):
                _, stderr = process.communicate(timeout=2)
                print(f"REFUSE: scope did not become ready; stderr={stderr.strip()!r}", file=sys.stderr)
                return 3

            if not _wait_for_file(task_pid_file, 3) or not _wait_for_file(child_pid_file, 3):
                print("REFUSE: task or detached descendant marker was not created", file=sys.stderr)
                return 3
            try:
                task_pid = int(task_pid_file.read_text(encoding="utf-8"))
                detached = int(child_pid_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                print("REFUSE: invalid task/descendant PID marker", file=sys.stderr)
                return 3

            if not _alive(task_pid) or not _alive(detached):
                print("REFUSE: task or detached descendant exited before fencing", file=sys.stderr)
                return 3

            task_cgroup = _read_cgroup(task_pid)
            detached_cgroup = _read_cgroup(detached)
            if task_cgroup is None or not task_cgroup.is_dir():
                print("REFUSE: task cgroup could not be resolved", file=sys.stderr)
                return 3
            if detached_cgroup != task_cgroup:
                print("REFUSE: detached descendant escaped task cgroup", file=sys.stderr)
                return 4
            if not (task_cgroup / "cgroup.kill").is_file():
                print("REFUSE: task cgroup.kill is unavailable", file=sys.stderr)
                return 3

            try:
                (task_cgroup / "cgroup.kill").write_text("1", encoding="utf-8")
            except OSError as exc:
                print(f"REFUSE: task cgroup.kill is not writable by this identity: {exc}", file=sys.stderr)
                return 4

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and (_alive(task_pid) or _alive(detached)):
                time.sleep(POLL_SECONDS)
            if _alive(detached):
                print("FAIL: detached descendant survived cgroup.kill", file=sys.stderr)
                return 5
            if _alive(task_pid):
                print("FAIL: task process survived cgroup.kill", file=sys.stderr)
                return 5

            print(f"PASS: detached descendant fenced in {task_cgroup}")
            return 0
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            _, stderr = process.communicate()
            if stderr.strip() and process.returncode not in (0, None):
                print(stderr.strip(), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
