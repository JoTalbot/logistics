"""Static safety coverage for the destructive cgroup rehearsal."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
REHEARSAL = ROOT / "deploy" / "remote-agent" / "cgroup_rehearsal.py"


def test_rehearsal_enforces_dedicated_identity_before_scope_start() -> None:
    text = REHEARSAL.read_text(encoding="utf-8")

    identity_guard = 'if evidence["execution_identity"] != EXPECTED_IDENTITY:'
    expected_identity = 'EXPECTED_IDENTITY = "logistics-agent"'
    readiness_guard = 'readiness.get("target_host_readiness") != "READY"'
    scope_start = "subprocess.Popen(command"

    assert identity_guard in text
    assert expected_identity in text
    assert readiness_guard in text
    assert text.index(identity_guard) < text.index(scope_start)
    assert text.index(readiness_guard) < text.index(scope_start)


def test_rehearsal_has_no_post_spawn_cgroup_migration_path() -> None:
    text = REHEARSAL.read_text(encoding="utf-8")

    assert "cgroup.procs" not in text
    assert "post-spawn" in text
    assert "PID moves" in text


def test_rehearsal_requires_cgroup_kill_and_verifies_both_processes() -> None:
    text = REHEARSAL.read_text(encoding="utf-8")

    assert 'kill_file = task_cgroup / "cgroup.kill"' in text
    assert 'kill_file.write_text("1"' in text
    assert 'evidence["task_alive_after_fence"]' in text
    assert 'evidence["detached_descendant_alive_after_fence"]' in text
    assert "CLEANUP_INCOMPLETE" in text
