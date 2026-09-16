"""Regression coverage for the per-task cgroup design invariants."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
DESIGN = ROOT / "docs" / "REMOTE_AGENT_CGROUP_DESIGN.md"


def test_direct_post_spawn_pid_move_is_not_treated_as_containment() -> None:
    text = DESIGN.read_text(encoding="utf-8")

    assert "naive `fork/exec -> write PID to cgroup.procs` sequence" in text
    assert "pre-membership window" in text
    assert "A post-spawn PID move alone is insufficient evidence of containment." in text


def test_cgroup_design_requires_fail_closed_and_detached_descendant_rehearsal() -> None:
    text = DESIGN.read_text(encoding="utf-8")

    assert "**Fail closed.**" in text
    assert "detached-session child termination" in text
    assert "real descendant process" in text
