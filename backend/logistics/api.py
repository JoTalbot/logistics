from __future__ import annotations

import os
from uuid import UUID

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .review import ReviewDecision, ReviewError, apply_review_decision


app = FastAPI(title="AI Logistics OS", version="0.3.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "logistics-api"}


@app.get("/api/v1")
def api_info() -> dict[str, str]:
    return {"version": "v1", "mode": "market-intelligence"}


class ReviewRequest(BaseModel):
    tenant_id: UUID
    resource_type: str = Field(min_length=1)
    resource_id: UUID
    decision: str
    operator_ref: str = Field(min_length=1)
    reason: str = Field(min_length=1)


def _operator_auth(token: str | None) -> None:
    expected = os.getenv("REVIEW_OPERATOR_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="human review is not configured")
    if token != expected:
        raise HTTPException(status_code=401, detail="invalid operator token")


def _dsn() -> str:
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)


@app.get("/api/v1/review/queue")
def review_queue(
    tenant_id: UUID,
    x_operator_token: str | None = Header(default=None),
) -> list[dict]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute(
            """
            SELECT id, 'publication_intent' AS resource_type, provider, status, created_at
            FROM publication_intents
            WHERE tenant_id=%s AND status IN ('prepared','retry')
            UNION ALL
            SELECT id, 'negotiation_session' AS resource_type, NULL, state, created_at
            FROM negotiation_sessions
            WHERE tenant_id=%s AND (requires_human=true OR state='review')
            ORDER BY created_at ASC
            LIMIT 100
            """,
            (tenant_id, tenant_id),
        ).fetchall()
    return [
        {"id": str(row[0]), "resource_type": row[1], "provider": row[2], "status": row[3], "created_at": row[4].isoformat()}
        for row in rows
    ]


@app.get("/api/v1/review/metrics")
def review_metrics(
    tenant_id: UUID,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, int]:
    """Operational counters for the authenticated human-review queue."""
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        publication_pending = conn.execute(
            "SELECT count(*) FROM publication_intents WHERE tenant_id=%s AND status IN ('prepared','retry')",
            (tenant_id,),
        ).fetchone()[0]
        negotiation_pending = conn.execute(
            "SELECT count(*) FROM negotiation_sessions WHERE tenant_id=%s AND (requires_human=true OR state='review')",
            (tenant_id,),
        ).fetchone()[0]
        audit_total = conn.execute(
            "SELECT count(*) FROM review_audit WHERE tenant_id=%s",
            (tenant_id,),
        ).fetchone()[0]
    return {
        "publication_pending": int(publication_pending),
        "negotiation_pending": int(negotiation_pending),
        "pending_total": int(publication_pending + negotiation_pending),
        "review_decisions_total": int(audit_total),
    }


@app.post("/api/v1/review/decision")
def review_decision(
    request: ReviewRequest,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, str]:
    _operator_auth(x_operator_token)
    decision = ReviewDecision(
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        decision=request.decision,
        operator_ref=request.operator_ref,
        reason=request.reason,
    )
    try:
        with psycopg.connect(_dsn()) as conn:
            apply_review_decision(conn, tenant_id=request.tenant_id, decision=decision)
            conn.commit()
    except ReviewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "recorded", "resource_id": str(request.resource_id), "decision": request.decision}
