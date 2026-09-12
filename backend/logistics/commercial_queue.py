from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException

from .api import app, _dsn, _operator_auth
import psycopg


_ALLOWED_STATUS = {"candidate", "reviewed", "accepted", "rejected", "hold"}


@app.get("/api/v1/review/commercial-opportunities")
def review_commercial_opportunities(
    tenant_id: UUID,
    status: str = "candidate",
    min_priority: float = 0.0,
    limit: int = 50,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    """Return a tenant-scoped, read-only commercial opportunity queue."""
    _operator_auth(x_operator_token)
    if status not in _ALLOWED_STATUS:
        raise HTTPException(status_code=422, detail="invalid priority status")
    if not 0 <= min_priority <= 1:
        raise HTTPException(status_code=422, detail="min_priority must be between 0 and 1")
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")

    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute(
            """
            SELECT o.id, o.load_id, l.external_ref, l.cargo_type, l.weight_kg,
                   l.offered_price, l.currency, o.score, o.estimated_cost,
                   o.estimated_margin, o.risk_adjusted_margin, o.reasons,
                   o.priority_score, o.priority_reasons, o.priority_status,
                   o.priority_updated_at
              FROM opportunities o
              JOIN loads l ON l.id = o.load_id AND l.tenant_id = o.tenant_id
             WHERE o.tenant_id=%s
               AND o.priority_status=%s
               AND o.priority_score IS NOT NULL
               AND o.priority_score >= %s
             ORDER BY o.priority_score DESC, o.priority_updated_at DESC, o.created_at ASC
             LIMIT %s
            """,
            (tenant_id, status, min_priority, limit),
        ).fetchall()

    return [
        {
            "id": str(r[0]),
            "load_id": str(r[1]),
            "external_ref": r[2],
            "cargo_type": r[3],
            "weight_kg": int(r[4]),
            "offered_price": str(r[5]),
            "currency": r[6],
            "opportunity_score": float(r[7]),
            "estimated_cost": str(r[8]),
            "estimated_margin": str(r[9]),
            "risk_adjusted_margin": str(r[10]),
            "reasons": r[11],
            "priority_score": float(r[12]),
            "priority_reasons": r[13],
            "priority_status": r[14],
            "priority_updated_at": r[15].isoformat() if r[15] else None,
        }
        for r in rows
    ]
