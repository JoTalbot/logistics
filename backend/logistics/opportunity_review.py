from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


ALLOWED_STATUSES = {"candidate", "reviewed", "accepted", "rejected", "hold"}


@dataclass(frozen=True)
class OpportunityReview:
    opportunity_id: UUID
    new_status: str
    operator_ref: str
    reason: str


def validate_opportunity_review(review: OpportunityReview) -> OpportunityReview:
    if review.new_status not in ALLOWED_STATUSES:
        raise ValueError("invalid opportunity status")
    if not review.operator_ref.strip():
        raise ValueError("operator_ref is required")
    if not review.reason.strip():
        raise ValueError("reason is required")
    return review


def apply_opportunity_review(conn: object, *, tenant_id: UUID, review: OpportunityReview) -> dict[str, object]:
    """Apply an explicit operator status transition and persist an immutable audit row."""
    validate_opportunity_review(review)
    row = conn.execute(
        """
        SELECT id, priority_status
          FROM opportunities
         WHERE tenant_id=%s AND id=%s AND priority_score IS NOT NULL
         FOR UPDATE
        """,
        (tenant_id, review.opportunity_id),
    ).fetchone()
    if row is None:
        raise ValueError("opportunity not found or has no priority decision")
    previous_status = row[1]
    conn.execute(
        """
        UPDATE opportunities
           SET priority_status=%s, priority_updated_at=now()
         WHERE tenant_id=%s AND id=%s
        """,
        (review.new_status, tenant_id, review.opportunity_id),
    )
    conn.execute(
        """
        INSERT INTO opportunity_review_history
          (tenant_id, opportunity_id, previous_status, new_status, operator_ref, reason)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (tenant_id, review.opportunity_id, previous_status, review.new_status,
         review.operator_ref, review.reason),
    )
    return {
        "opportunity_id": str(row[0]),
        "status": review.new_status,
        "previous_status": previous_status,
        "operator_ref": review.operator_ref,
        "reason": review.reason,
    }


def opportunity_review_metrics(conn: object, *, tenant_id: UUID) -> dict[str, object]:
    rows = conn.execute(
        """
        SELECT priority_status, count(*)
          FROM opportunities
         WHERE tenant_id=%s AND priority_score IS NOT NULL
         GROUP BY priority_status
         ORDER BY priority_status
        """,
        (tenant_id,),
    ).fetchall()
    history = conn.execute(
        """
        SELECT count(*), count(*) FILTER (WHERE new_status='accepted'),
               count(*) FILTER (WHERE new_status='rejected'),
               count(*) FILTER (WHERE new_status='hold')
          FROM opportunity_review_history
         WHERE tenant_id=%s
        """,
        (tenant_id,),
    ).fetchone()
    total = int(history[0])
    accepted = int(history[1])
    rejected = int(history[2])
    decided = accepted + rejected
    return {
        "by_status": {row[0]: int(row[1]) for row in rows},
        "review_transitions": total,
        "accepted_transitions": accepted,
        "rejected_transitions": rejected,
        "hold_transitions": int(history[3]),
        "acceptance_rate_of_terminal_decisions": round(accepted / decided, 4) if decided else 0.0,
    }


def list_opportunity_review_history(conn: object, *, tenant_id: UUID, opportunity_id: UUID, limit: int = 50) -> list[dict[str, object]]:
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT previous_status, new_status, operator_ref, reason, created_at
          FROM opportunity_review_history
         WHERE tenant_id=%s AND opportunity_id=%s
         ORDER BY created_at DESC, id DESC
         LIMIT %s
        """,
        (tenant_id, opportunity_id, limit),
    ).fetchall()
    return [
        {"previous_status": r[0], "new_status": r[1], "operator_ref": r[2],
         "reason": r[3], "created_at": r[4].isoformat()}
        for r in rows
    ]
