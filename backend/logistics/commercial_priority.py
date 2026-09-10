from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

from .commercial_pipeline import CommercialCandidate


@dataclass(frozen=True)
class PriorityDecision:
    load_id: UUID
    priority_score: float
    reasons: tuple[str, ...]
    status: str = "candidate"


def to_priority_decision(candidate: CommercialCandidate) -> PriorityDecision:
    return PriorityDecision(
        load_id=candidate.load.id,
        priority_score=candidate.priority_score,
        reasons=candidate.reasons,
    )


def persist_priority_decision(conn: Any, *, tenant_id: UUID, decision: PriorityDecision, updated_at) -> bool:
    if decision.status not in {"candidate", "reviewed", "accepted", "rejected", "hold"}:
        raise ValueError("invalid priority status")
    if not 0 <= decision.priority_score <= 1:
        raise ValueError("priority_score must be between 0 and 1")
    result = conn.execute(
        """UPDATE opportunities
           SET priority_score=%s, priority_reasons=%s, priority_updated_at=%s, priority_status=%s
         WHERE tenant_id=%s AND load_id=%s""",
        (decision.priority_score, list(decision.reasons), updated_at, decision.status, tenant_id, decision.load_id),
    )
    if getattr(result, "rowcount", 1) != 1:
        raise LookupError("opportunity not found for tenant/load")
    return True


def persist_priority_decisions(conn: Any, *, tenant_id: UUID, candidates: Iterable[CommercialCandidate], updated_at) -> int:
    decisions = [to_priority_decision(candidate) for candidate in candidates]
    for decision in decisions:
        persist_priority_decision(conn, tenant_id=tenant_id, decision=decision, updated_at=updated_at)
    return len(decisions)
