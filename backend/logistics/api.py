from __future__ import annotations

import os
from uuid import UUID

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .review import ReviewDecision, ReviewError, apply_review_decision


app = FastAPI(title="AI Logistics OS", version="0.4.0")


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


@app.get("/api/v1/review/recommendations")
def review_recommendations(
    tenant_id: UUID,
    limit: int = 50,
    x_operator_token: str | None = Header(default=None),
) -> list[dict]:
    """Return persisted explainable opportunity recommendations for an operator."""
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute(
            """
            SELECT id, load_id, status, score, estimated_cost, estimated_margin,
                   risk_adjusted_margin, recommended_price, market_median_price,
                   recommendation_reasons, recommendation_updated_at, created_at
            FROM opportunities
            WHERE tenant_id=%s AND recommendation_updated_at IS NOT NULL
            ORDER BY recommendation_updated_at DESC
            LIMIT %s
            """,
            (tenant_id, limit),
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "load_id": str(row[1]),
            "status": row[2],
            "score": float(row[3]),
            "estimated_cost": float(row[4]),
            "estimated_margin": float(row[5]),
            "risk_adjusted_margin": float(row[6]),
            "recommended_price": float(row[7]) if row[7] is not None else None,
            "market_median_price": float(row[8]) if row[8] is not None else None,
            "recommendation_reasons": row[9],
            "recommendation_updated_at": row[10].isoformat(),
            "created_at": row[11].isoformat(),
        }
        for row in rows
    ]


@app.get("/api/v1/review/audit/report")
def review_audit_report(
    tenant_id: UUID,
    days: int = 30,
    x_operator_token: str | None = Header(default=None),
) -> dict:
    """Summarize review decisions and queue age without exposing operator secrets."""
    _operator_auth(x_operator_token)
    if not 1 <= days <= 365:
        raise HTTPException(status_code=422, detail="days must be between 1 and 365")
    with psycopg.connect(_dsn()) as conn:
        decision_rows = conn.execute(
            """
            SELECT decision, count(*)
            FROM review_audit
            WHERE tenant_id=%s AND created_at >= now() - (%s * interval '1 day')
            GROUP BY decision
            ORDER BY decision
            """,
            (tenant_id, days),
        ).fetchall()
        trend_rows = conn.execute(
            """
            SELECT date_trunc('day', created_at) AS day, decision, count(*)
            FROM review_audit
            WHERE tenant_id=%s AND created_at >= now() - (%s * interval '1 day')
            GROUP BY 1, 2
            ORDER BY 1 ASC, 2 ASC
            """,
            (tenant_id, days),
        ).fetchall()
        queue_age = conn.execute(
            """
            SELECT count(*),
                   COALESCE(EXTRACT(EPOCH FROM (now() - min(created_at))), 0),
                   COALESCE(EXTRACT(EPOCH FROM (now() - avg(created_at))), 0)
            FROM (
              SELECT created_at FROM publication_intents
              WHERE tenant_id=%s AND status IN ('prepared','retry')
              UNION ALL
              SELECT created_at FROM negotiation_sessions
              WHERE tenant_id=%s AND (requires_human=true OR state='review')
            ) pending
            """,
            (tenant_id, tenant_id),
        ).fetchone()
    return {
        "window_days": days,
        "decisions": {row[0]: int(row[1]) for row in decision_rows},
        "daily_trend": [
            {"day": row[0].date().isoformat(), "decision": row[1], "count": int(row[2])}
            for row in trend_rows
        ],
        "queue_age": {
            "pending_total": int(queue_age[0]),
            "oldest_seconds": int(queue_age[1]),
            "average_age_seconds": int(queue_age[2]),
        },
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
