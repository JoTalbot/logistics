from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


class ReviewError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewDecision:
    resource_type: str
    resource_id: UUID
    decision: str
    operator_ref: str
    reason: str


def validate_review_decision(decision: ReviewDecision) -> ReviewDecision:
    if decision.decision not in {"approve", "reject", "hold"}:
        raise ReviewError("decision must be approve, reject or hold")
    if not decision.resource_type.strip():
        raise ReviewError("resource_type is required")
    if not decision.operator_ref.strip():
        raise ReviewError("operator_ref is required")
    if not decision.reason.strip():
        raise ReviewError("reason is required")
    allowed_resources = {"publication_intent", "negotiation_session"}
    if decision.resource_type not in allowed_resources:
        raise ReviewError("unsupported review resource")
    return decision


def apply_review_decision(conn, *, tenant_id: UUID, decision: ReviewDecision) -> None:
    """Apply only an explicit human review transition; no provider call is made."""
    validate_review_decision(decision)
    if decision.resource_type == "publication_intent":
        status = {"approve": "approved", "reject": "rejected", "hold": "prepared"}[decision.decision]
        result = conn.execute(
            """
            UPDATE publication_intents
            SET status=%s, updated_at=now()
            WHERE tenant_id=%s AND id=%s AND status IN ('prepared','retry','approved')
            RETURNING id
            """,
            (status, tenant_id, decision.resource_id),
        )
    else:
        state = {"approve": "approved", "reject": "rejected", "hold": "draft"}[decision.decision]
        result = conn.execute(
            """
            UPDATE negotiation_sessions
            SET state=%s, requires_human=false, updated_at=now()
            WHERE tenant_id=%s AND id=%s AND state IN ('draft','review','approved')
            RETURNING id
            """,
            (state, tenant_id, decision.resource_id),
        )
    if result.fetchone() is None:
        raise ReviewError("review resource not found or is no longer reviewable")
    conn.execute(
        """
        INSERT INTO review_audit(tenant_id, resource_type, resource_id, decision, operator_ref, reason)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (tenant_id, decision.resource_type, decision.resource_id, decision.decision, decision.operator_ref, decision.reason),
    )
