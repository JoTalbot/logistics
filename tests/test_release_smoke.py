import pytest

from logistics.readiness import GateStatus, ReadinessGate
from scripts.release_smoke import readiness_evidence


def test_readiness_evidence_is_machine_readable_and_fail_closed():
    evidence = readiness_evidence(
        [ReadinessGate("api", GateStatus.READY, "health ok")]
    )

    assert evidence["schema"] == "logistics.release-readiness.v1"
    assert evidence["report"]["release_ready"] is True
    assert evidence["report"]["required_unready"] == ()
    assert evidence["gates"] == [
        {"name": "api", "status": "ready", "evidence": "health ok", "required": True}
    ]


def test_required_pending_gate_fails_closed():
    with pytest.raises(RuntimeError, match="release readiness blocked"):
        readiness_evidence(
            [ReadinessGate("provider", GateStatus.PENDING, "verification pending")]
        )
