from pytest import raises

from logistics.readiness import GateStatus, ReadinessGate, evaluate_readiness, readiness_evidence


def test_all_required_ready_means_release_ready():
    report = evaluate_readiness(
        [
            ReadinessGate("ci", GateStatus.READY, "run-1"),
            ReadinessGate("backup", GateStatus.READY, "rehearsal-1"),
            ReadinessGate("provider", GateStatus.PENDING, "provider verification", required=False),
        ]
    )

    assert report.total == 3
    assert report.ready == 2
    assert report.pending == 1
    assert report.blocked == 0
    assert report.required_unready == ()
    assert report.release_ready is True


def test_required_pending_and_blocked_are_not_release_ready():
    report = evaluate_readiness(
        [
            ReadinessGate("backup", GateStatus.PENDING, "restore rehearsal pending"),
            ReadinessGate("provider", GateStatus.BLOCKED, "provider denied access"),
        ]
    )

    assert report.ready == 0
    assert report.pending == 1
    assert report.blocked == 1
    assert report.required_unready == ("backup", "provider")
    assert report.release_ready is False


def test_gate_names_must_be_unique():
    gate = ReadinessGate("ci", GateStatus.READY, "run-1")
    with raises(ValueError, match="unique"):
        evaluate_readiness([gate, gate])


def test_non_ready_gate_requires_evidence():
    with raises(ValueError, match="evidence"):
        ReadinessGate("backup", GateStatus.PENDING)


def test_readiness_evidence_has_deterministic_content_fingerprint():
    gates = [
        ReadinessGate("ci", GateStatus.READY, "run-1"),
        ReadinessGate("backup", GateStatus.READY, "rehearsal-1"),
    ]

    first = readiness_evidence(gates)
    second = readiness_evidence(tuple(gates))

    assert first == second
    assert first["schema"] == "logistics.release-readiness.v1"
    assert len(first["content_sha256"]) == 64
    assert first["content_sha256"] != ""


def test_readiness_evidence_fails_closed_before_fingerprinting_unready_gate():
    with raises(RuntimeError, match="release readiness blocked"):
        readiness_evidence([ReadinessGate("backup", GateStatus.PENDING, "restore pending")])
