"""Persistence helpers for deterministic simulation/shadow decisions."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from .shadow_decisions import ShadowDecision


def save_shadow_decision(
    conn: object,
    decision: ShadowDecision,
    *,
    correlation_id: str | None = None,
) -> None:
    """Persist a decision idempotently inside the caller's transaction."""
    conn.execute(
        """
        INSERT INTO autonomy_decisions
          (tenant_id, decision_id, correlation_id, action, confidence, tier, mode,
           policy_version, classification_reason, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (tenant_id, decision_id) DO NOTHING
        """,
        (
            UUID(decision.tenant_id),
            decision.decision_id,
            correlation_id,
            decision.action,
            decision.confidence,
            decision.tier.value,
            decision.mode.value,
            decision.policy_version,
            decision.classification_reason,
            decision.created_at,
        ),
    )


def list_exception_decisions(
    conn: object,
    *,
    tenant_id: UUID,
    limit: int = 100,
) -> list[dict[str, object]]:
    """Return oldest non-AUTO decisions for operator review, tenant-scoped."""
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")
    rows = conn.execute(
        """
        SELECT decision_id, correlation_id, action, confidence, tier, mode,
               policy_version, classification_reason, created_at
          FROM autonomy_decisions
         WHERE tenant_id=%s AND tier IN ('REVIEW','HIGH_RISK','BLOCK')
         ORDER BY created_at ASC
         LIMIT %s
        """,
        (tenant_id, limit),
    ).fetchall()
    return [
        {
            "decision_id": row[0],
            "correlation_id": row[1],
            "action": row[2],
            "confidence": float(row[3]),
            "tier": row[4],
            "mode": row[5],
            "policy_version": row[6],
            "classification_reason": row[7],
            "created_at": row[8].isoformat() if isinstance(row[8], datetime) else row[8],
        }
        for row in rows
    ]
