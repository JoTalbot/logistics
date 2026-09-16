#!/usr/bin/env python3
"""Opt-in Linux rehearsal for a systemd-backed per-task cgroup boundary.

This script is intentionally not part of normal CI or remote-agent execution.
It requires an explicit environment flag and a systemd scope that the current
identity is authorized to create. It never falls back to post-spawn PID moves,
because that pattern has a pre-membership race and is not containment evidence.
"""
from __future__ import annotations

import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ENABLE = "LOGISTICS_CGROUP_REHEARSAL"
EVIDENCE_PATH = "LOGISTICS_CGROUP_EVIDENCE_PATH"
POLL_SECONDS = 0.1
EVIDENCE_SCHEMA_VERSION = "1"


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
    stat = Path(f"/proc/{pid}/stat")
    try:
        fields = stat.read_text(encoding="utf-8").split()
    except OSError:
        return False
    return len(fields) > 2 and fields[2] != "Z"


def _load_probe() -> object:
    path = Path(__file__).with_name("cgroup_probe.py")
    spec = importlib.util.spec_from_file_location("logistics_cgroup_probe", path)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load cgroup capability probe")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _readiness() -> dict[str, object]:
    try:
        return _load_probe().probe()  # type: ignore[attr-defined]
    except Exception as exc:
        return {"probe_error": str(exc), "target_host_readiness": "ERROR"}


def _systemd_scope_exists(unit: str) -> bool:
    try:
        completed = subprocess.run(
            ["/usr/bin/systemctl", "show", unit, "-p", "LoadState", "--value"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0 and completed.stdout.strip() not in {"", "not-found"}


def _write_evidence(evidence: dict[str, object]) -> None:
    destination = os.environ.get(EVIDENCE_PATH)
    if not destination:
        return
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_evidence() -> dict[str, object]:
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": socket.gethostname(),
        "execution_identity": None,
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "gid": os.getgid(),
        "egid": os.getegid(),
        "kernel": None,
        "cgroup_v2_mount": False,
        "systemd_run": {"path": "/usr/bin/systemd-run", "available": False},
        "readiness": {},
        "scope": {"unit": None, "task_cgroup": None},
        "task_pid": None,
        "detached_descendant_pid": None,
        "task_cgroup": None,
        "detached_descendant_cgroup": None,
        "same_cgroup_before_fence": False,
        "cgroup_kill_write": False,
        "task_alive_before_fence": False,
        "detached_descendant_alive_before_fence": False,
        "task_alive_after_fence": None,
        "detached_descendant_alive_after_fence": None,
        "cleanup": False,
        "result": "NOT_STARTED",
    }


def main() -> int:
    evidence = _base_evidence()
    evidence["kernel"] = Path("/proc/version").read_text(encoding="utf-8", errors="replace").strip() if Path("/proc/version").exists() else None
    evidence["execution_identity"] = _readiness().get("execution_identity")

    if os.name != "posix" or not Path("/proc/version").exists():
        evidence["result"] = "UNSUPPORTED_LINUX"
        _write_evidence(evidence)
        print("SKIP: Linux host required", file=sys.stderr)
        return 2
    if os.environ.get(ENABLE) != "1":
        evidence["result"] = "NOT_OPTED_IN"
        _write_evidence(evidence)
        print(f"SKIP: set {ENABLE}=1 to run the destructive rehearsal", file=sys.stderr)
        return 2
    if os.geteuid() == 0:
        evidence["result"] = "ROOT_REFUSED"
        _write_evidence(evidence)
        print("REFUSE: run as the dedicated non-root logistics-agent identity", file=sys.stderr)
        return 3
    if not Path("/sys/fs/cgroup/cgroup.controllers").is_file():
        evidence["result"] = "CGROUP_V2_UNAVAILABLE"
        _write_evidence(evidence)
        print("REFUSE: cgroup v2 is not mounted", file=sys.stderr)
        return 3

    systemd_run = Path("/usr/bin/systemd-run")
    evidence["cgroup_v2_mount"] = True
    evidence["systemd_run"] = {"path": str(systemd_run), "available": systemd_run.is_file()}
    readiness = _readiness()
    evidence["readiness"] = readiness
    evidence["execution_identity"] = readiness.get("execution_identity")
    if not systemd_run.is_file():
        evidence["result"] = "SYSTEMD_RUN_UNAVAILABLE"
        _write_evidence(evidence)
        print("REFUSE: /usr/bin/systemd-run is unavailable", file=sys.stderr)
        return 3
    if readiness.get("target_host_readiness") != "READY":
        evidence["result"] = "READINESS_BLOCKED"
        _write_evidence(evidence)
        print(f"REFUSE: target_host_readiness={readiness.get('target_host_readiness')!r}", file=sys.stderr)
        return 3

    with tempfile.TemporaryDirectory(prefix="logistics-cgroup-rehearsal-") as tmp:
        root = Path(tmp)
        ready = root / "ready"
        task_pid_file = root / "task.pid"
        child_pid_file = root / "child.pid"
        unit = f"logistics-cgroup-rehearsal-{uuid.uuid4().hex[:12]}"
        evidence["scope"]["unit"] = unit
        code = (
            "import os,time; "
            f"open({str(ready)!r}, 'w').close(); "
            f"open({str(task_pid_file)!r}, 'w').write(str(os.getpid())); "
            f"pid=os.fork(); "
            f"(os.setsid(), open({str(child_pid_file)!r}, 'w').write(str(os.getpid())), time.sleep(30)) "
            "if pid == 0 else time.sleep(30)"
        )
        command = [str(systemd_run), "--scope", "--unit", unit, "--collect", "/usr/bin/python3", "-c", code]

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError as exc:
            evidence["result"] = "SCOPE_START_FAILED"
            _write_evidence(evidence)
            print(f"REFUSE: could not start systemd scope: {exc}", file=sys.stderr)
            return 3

        try:
            if not _wait_for_file(ready, 5):
                evidence["result"] = "SCOPE_NOT_READY"
                _, stderr = process.communicate(timeout=2)
                print(f"REFUSE: scope did not become ready; stderr={stderr.strip()!r}", file=sys.stderr)
                return 3
            if not _wait_for_file(task_pid_file, 3) or not _wait_for_file(child_pid_file, 3):
                evidence["result"] = "PID_MARKER_MISSING"
                print("REFUSE: task or detached descendant marker was not created", file=sys.stderr)
                return 3
            try:
                task_pid = int(task_pid_file.read_text(encoding="utf-8"))
                detached = int(child_pid_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                evidence["result"] = "PID_MARKER_INVALID"
                print("REFUSE: invalid task/descendant PID marker", file=sys.stderr)
                return 3

            evidence["task_pid"] = task_pid
            evidence["detached_descendant_pid"] = detached
            task_before = _alive(task_pid)
            detached_before = _alive(detached)
            evidence["task_alive_before_fence"] = task_before
            evidence["detached_descendant_alive_before_fence"] = detached_before
            if not task_before or not detached_before:
                evidence["result"] = "PROCESS_EXITED_EARLY"
                print("REFUSE: task or detached descendant exited before fencing", file=sys.stderr)
                return 3

            task_cgroup = _read_cgroup(task_pid)
            detached_cgroup = _read_cgroup(detached)
            evidence["task_cgroup"] = str(task_cgroup) if task_cgroup else None
            evidence["detached_descendant_cgroup"] = str(detached_cgroup) if detached_cgroup else None
            evidence["scope"]["task_cgroup"] = str(task_cgroup) if task_cgroup else None
            if task_cgroup is None or not task_cgroup.is_dir():
                evidence["result"] = "TASK_CGROUP_UNRESOLVED"
                print("REFUSE: task cgroup could not be resolved", file=sys.stderr)
                return 3
            if detached_cgroup != task_cgroup:
                evidence["result"] = "DESCENDANT_ESCAPED"
                print("REFUSE: detached descendant escaped task cgroup", file=sys.stderr)
                return 4
            evidence["same_cgroup_before_fence"] = True
            kill_file = task_cgroup / "cgroup.kill"
            if not kill_file.is_file():
                evidence["result"] = "CGROUP_KILL_UNAVAILABLE"
                print("REFUSE: task cgroup.kill is unavailable", file=sys.stderr)
                return 3

            try:
                kill_file.write_text("1", encoding="utf-8")
                evidence["cgroup_kill_write"] = True
            except OSError as exc:
                evidence["result"] = "CGROUP_KILL_NOT_WRITABLE"
                print(f"REFUSE: task cgroup.kill is not writable by this identity: {exc}", file=sys.stderr)
                return 4

            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and (_alive(task_pid) or _alive(detached)):
                time.sleep(POLL_SECONDS)
            evidence["task_alive_after_fence"] = _alive(task_pid)
            evidence["detached_descendant_alive_after_fence"] = _alive(detached)
            if evidence["detached_descendant_alive_after_fence"]:
                evidence["result"] = "DETACHED_DESCENDANT_SURVIVED"
                print("FAIL: detached descendant survived cgroup.kill", file=sys.stderr)
                return 5
            if evidence["task_alive_after_fence"]:
                evidence["result"] = "TASK_SURVIVED"
                print("FAIL: task process survived cgroup.kill", file=sys.stderr)
                return 5

            print(f"PASS: detached descendant fenced in {task_cgroup}")
            evidence["result"] = "PASS"
            return 0
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            process.communicate()
            evidence["cleanup"] = not _systemd_scope_exists(unit)
            if evidence["result"] == "PASS" and not evidence["cleanup"]:
                evidence["result"] = "CLEANUP_INCOMPLETE"
                print("FAIL: transient systemd scope was not confirmed collected", file=sys.stderr)
            _write_evidence(evidence)


if __name__ == "__main__":
    raise SystemExit(main())
