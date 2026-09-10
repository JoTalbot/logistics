from __future__ import annotations

from typing import Any
from uuid import UUID


_ALLOWED_ACTIONS = {"approve", "reject", "hold"}


def decide_contact_intent(
    conn: Any,
    *,
    tenant_id: UUID,
    contact_intent_id: UUID,
    action: str,
    operator_ref: str,
    reason: str,
) -> str:
    """Apply an audited human decision. This function never sends contact."""
    if action not in _ALLOWED_ACTIONS:
        raise ValueError("invalid contact intent action")
    if not operator_ref.strip() or not reason.strip():
        raise ValueError("operator_ref and reason are required")

    row = conn.execute(
        """
        SELECT status, authorized, suppressed, human_approval_required
        FROM contact_intents
        WHERE tenant_id=%s AND id=%s
        FOR UPDATE
        """,
        (tenant_id, contact_intent_id),
    ).fetchone()
    if row is None:
        raise LookupError("contact intent not found")

    status, authorized, suppressed, human_approval_required = row
    if action == "approve":
        if suppressed:
            raise ValueError("suppressed contact intent cannot be approved")
        if not authorized:
            raise ValueError("unauthorized contact intent cannot be approved")
        if status != "pending" or not human_approval_required:
            raise ValueError("only pending contact intents requiring human approval can be approved")
        resulting_status = "approved"
        conn.execute(
            """
            UPDATE contact_intents
            SET status='approved', human_approval_required=false, updated_at=now()
            WHERE tenant_id=%s AND id=%s AND status='pending'
            """,
            (tenant_id, contact_intent_id),
        )
    elif action == "reject":
        if status not in {"pending", "approved"}:
            raise ValueError("contact intent cannot be rejected from its current state")
        resulting_status = "rejected"
        conn.execute(
            "UPDATE contact_intents SET status='rejected', updated_at=now() WHERE tenant_id=%s AND id=%s",
            (tenant_id, contact_intent_id),
        )
    else:
        if status != "pending":
            raise ValueError("only pending contact intents can be put on hold")
        resulting_status = "pending"

    conn.execute(
        """
        INSERT INTO contact_intent_audit
          (tenant_id, contact_intent_id, action, resulting_status, operator_ref, reason)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (tenant_id, contact_intent_id, action, resulting_status, operator_ref, reason),
    )
    return resulting_status
