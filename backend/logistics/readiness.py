"""Pure readiness gate aggregation for release evidence."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable


class GateStatus(StrEnum):
    READY = "ready"
    PENDING = "pending"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ReadinessGate:
    name: str
    status: GateStatus
    evidence: str = ""
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("gate name must not be empty")
        if self.status is not GateStatus.READY and not self.evidence.strip():
            raise ValueError("non-ready gate requires evidence")


@dataclass(frozen=True)
class ReadinessReport:
    total: int
    ready: int
    pending: int
    blocked: int
    required_unready: tuple[str, ...]
    release_ready: bool


def evaluate_readiness(gates: Iterable[ReadinessGate]) -> ReadinessReport:
    """Aggregate explicit gates without side effects or policy mutation."""
    items = tuple(gates)
    if len({gate.name for gate in items}) != len(items):
        raise ValueError("gate names must be unique")

    ready = sum(gate.status is GateStatus.READY for gate in items)
    pending = sum(gate.status is GateStatus.PENDING for gate in items)
    blocked = sum(gate.status is GateStatus.BLOCKED for gate in items)
    required_unready = tuple(
        gate.name
        for gate in items
        if gate.required and gate.status is not GateStatus.READY
    )
    return ReadinessReport(
        total=len(items),
        ready=ready,
        pending=pending,
        blocked=blocked,
        required_unready=required_unready,
        release_ready=not required_unready,
    )
