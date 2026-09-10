from __future__ import annotations

import os
from uuid import UUID

import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .review import ReviewDecision, ReviewError, apply_review_decision
from .prospect_store import list_prospects, set_prospect_suppression
from .customer_opportunity_store import list_customer_opportunities
from .recurring_demand_store import list_patterns
from .contact_outbox import list_contact_intents
from .contact_review import decide_contact_intent
from .duplicate_loads import find_duplicate_load_groups
from .recurring_demand_health import scheduler_health

app = FastAPI(title="AI Logistics OS", version="0.7.3")

@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok", "service": "logistics-api"}

@app.get("/ready")
def readiness() -> dict[str, str]:
    """Readiness probe: verifies that the configured PostgreSQL database is reachable."""
    try:
        with psycopg.connect(_dsn(), connect_timeout=3) as conn:
            conn.execute("SELECT 1").fetchone()
    except (HTTPException, psycopg.Error) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else "database is not ready"
        raise HTTPException(status_code=503, detail=detail) from exc
    return {"status": "ready", "service": "logistics-api"}

@app.get("/api/v1")
def api_info() -> dict[str, str]: return {"version": "v1", "mode": "market-intelligence"}

class ReviewRequest(BaseModel):
    tenant_id: UUID
    resource_type: str = Field(min_length=1)
    resource_id: UUID
    decision: str
    operator_ref: str = Field(min_length=1)
    reason: str = Field(min_length=1)

class ProspectSuppressionRequest(BaseModel):
    tenant_id: UUID
    prospect_id: UUID
    suppressed: bool
    reason: str = Field(min_length=1)

class ContactIntentDecisionRequest(BaseModel):
    tenant_id: UUID
    contact_intent_id: UUID
    action: str
    operator_ref: str = Field(min_length=1)
    reason: str = Field(min_length=1)

def _operator_auth(token: str | None) -> None:
    expected = os.getenv("REVIEW_OPERATOR_TOKEN", "")
    if not expected: raise HTTPException(status_code=503, detail="human review is not configured")
    if token != expected: raise HTTPException(status_code=401, detail="invalid operator token")

def _dsn() -> str:
    dsn = os.getenv("DATABASE_URL", "")
    if not dsn: raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return dsn.replace("postgresql+psycopg://", "postgresql://", 1)

def _priority_metrics(conn: object, *, tenant_id: UUID, high_priority_threshold: float, stale_after_hours: int) -> dict[str, object]:
    if not 0 <= high_priority_threshold <= 1: raise ValueError("high_priority_threshold must be between 0 and 1")
    if stale_after_hours < 1: raise ValueError("stale_after_hours must be at least 1")
    rows = conn.execute("""SELECT priority_status, count(*),
                                  COALESCE(EXTRACT(EPOCH FROM (now()-min(priority_updated_at))), 0),
                                  COALESCE(avg(EXTRACT(EPOCH FROM (now()-priority_updated_at))), 0)
                             FROM opportunities
                            WHERE tenant_id=%s AND priority_score IS NOT NULL AND priority_updated_at IS NOT NULL
                            GROUP BY priority_status
                            ORDER BY priority_status""", (tenant_id,)).fetchall()
    high = conn.execute("""SELECT count(*)
                              FROM opportunities
                             WHERE tenant_id=%s AND priority_score IS NOT NULL AND priority_score >= %s
                               AND priority_status IN ('candidate','reviewed','hold')""", (tenant_id, high_priority_threshold)).fetchone()[0]
    stale = conn.execute("""SELECT count(*)
                              FROM opportunities
                             WHERE tenant_id=%s AND priority_score IS NOT NULL AND priority_updated_at IS NOT NULL
                               AND priority_status IN ('candidate','reviewed','hold')
                               AND priority_updated_at < now() - (%s * interval '1 hour')""", (tenant_id, stale_after_hours)).fetchone()[0]
    by_status = {}
    oldest = 0
    average = 0
    total = 0
    for status, count, oldest_seconds, average_seconds in rows:
        count = int(count)
        by_status[status] = count
        total += count
        oldest = max(oldest, int(oldest_seconds))
        average = max(average, int(average_seconds))
    return {
        "total": total,
        "by_status": by_status,
        "high_priority_open": int(high),
        "stale_open": int(stale),
        "oldest_age_seconds": oldest,
        "average_age_seconds": average,
        "sla": {"stale_after_hours": stale_after_hours, "high_priority_threshold": high_priority_threshold},
    }

@app.get("/api/v1/review/queue")
def review_queue(tenant_id: UUID, x_operator_token: str | None = Header(default=None)) -> list[dict]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute("""SELECT id, 'publication_intent' AS resource_type, provider, status, created_at FROM publication_intents WHERE tenant_id=%s AND status IN ('prepared','retry') UNION ALL SELECT id, 'negotiation_session' AS resource_type, NULL, state, created_at FROM negotiation_sessions WHERE tenant_id=%s AND (requires_human=true OR state='review') ORDER BY created_at ASC LIMIT 100""", (tenant_id, tenant_id)).fetchall()
    return [{"id": str(r[0]), "resource_type": r[1], "provider": r[2], "status": r[3], "created_at": r[4].isoformat()} for r in rows]

@app.get("/api/v1/review/summary")
def review_summary(tenant_id: UUID, duplicate_window_hours: int = 48, x_operator_token: str | None = Header(default=None)) -> dict[str, object]:
    """Compact tenant-scoped operator snapshot; all mutable external actions remain disabled."""
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            publication_pending = conn.execute("SELECT count(*) FROM publication_intents WHERE tenant_id=%s AND status IN ('prepared','retry')", (tenant_id,)).fetchone()[0]
            negotiation_pending = conn.execute("SELECT count(*) FROM negotiation_sessions WHERE tenant_id=%s AND (requires_human=true OR state='review')", (tenant_id,)).fetchone()[0]
            contact_pending = conn.execute("SELECT count(*) FROM contact_intents WHERE tenant_id=%s AND status='pending'", (tenant_id,)).fetchone()[0]
            customer_opportunities = conn.execute("SELECT count(*) FROM customer_opportunities WHERE tenant_id=%s AND status='candidate'", (tenant_id,)).fetchone()[0]
            duplicate_groups = len(find_duplicate_load_groups(conn, tenant_id=tenant_id, window_hours=duplicate_window_hours, limit=10000))
            priorities = _priority_metrics(conn, tenant_id=tenant_id, high_priority_threshold=0.8, stale_after_hours=12)
            scheduler = scheduler_health(conn)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    operational_status = "critical" if scheduler["operational_status"] in {"critical", "failed", "stale"} else ("degraded" if priorities["stale_open"] else "healthy")
    return {"tenant_id": str(tenant_id), "operational_status": operational_status, "review_queue": {"publication_pending": int(publication_pending), "negotiation_pending": int(negotiation_pending), "contact_pending": int(contact_pending), "customer_opportunities_candidate": int(customer_opportunities), "pending_total": int(publication_pending + negotiation_pending + contact_pending)}, "priority_queue": priorities, "duplicate_loads": {"groups": duplicate_groups, "window_hours": duplicate_window_hours, "max_groups_evaluated": 10000}, "scheduler": scheduler}

@app.get("/api/v1/review/metrics")
def review_metrics(tenant_id: UUID, x_operator_token: str | None = Header(default=None)) -> dict[str, int]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        publication_pending = conn.execute("SELECT count(*) FROM publication_intents WHERE tenant_id=%s AND status IN ('prepared','retry')", (tenant_id,)).fetchone()[0]
        negotiation_pending = conn.execute("SELECT count(*) FROM negotiation_sessions WHERE tenant_id=%s AND (requires_human=true OR state='review')", (tenant_id,)).fetchone()[0]
        audit_total = conn.execute("SELECT count(*) FROM review_audit WHERE tenant_id=%s", (tenant_id,)).fetchone()[0]
    return {"publication_pending": int(publication_pending), "negotiation_pending": int(negotiation_pending), "pending_total": int(publication_pending + negotiation_pending), "review_decisions_total": int(audit_total)}

@app.get("/api/v1/review/priorities/metrics")
def review_priority_metrics(tenant_id: UUID, high_priority_threshold: float = 0.8, stale_after_hours: int = 12, x_operator_token: str | None = Header(default=None)) -> dict[str, object]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            return {"tenant_id": str(tenant_id), **_priority_metrics(conn, tenant_id=tenant_id, high_priority_threshold=high_priority_threshold, stale_after_hours=stale_after_hours)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/api/v1/review/priorities")
def review_priorities(tenant_id: UUID, status: str = "candidate", limit: int = 50, x_operator_token: str | None = Header(default=None)) -> list[dict]:
    _operator_auth(x_operator_token)
    allowed = {"candidate", "reviewed", "accepted", "rejected", "hold"}
    if status not in allowed: raise HTTPException(status_code=422, detail="invalid priority status")
    if not 1 <= limit <= 100: raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute("""SELECT id, load_id, priority_score, priority_reasons, priority_status, priority_updated_at
                                FROM opportunities
                               WHERE tenant_id=%s AND priority_status=%s AND priority_score IS NOT NULL
                               ORDER BY priority_score DESC, priority_updated_at DESC
                               LIMIT %s""", (tenant_id, status, limit)).fetchall()
    return [{"id": str(r[0]), "load_id": str(r[1]), "priority_score": float(r[2]), "priority_reasons": r[3], "priority_status": r[4], "priority_updated_at": r[5].isoformat()} for r in rows]

@app.get("/api/v1/review/prospects")
def review_prospects(tenant_id: UUID, limit: int = 50, x_operator_token: str | None = Header(default=None)) -> list[dict]:
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 100: raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    with psycopg.connect(_dsn()) as conn: return list_prospects(conn, tenant_id=tenant_id, limit=limit)

@app.post("/api/v1/review/prospects/suppression")
def review_prospect_suppression(request: ProspectSuppressionRequest, x_operator_token: str | None = Header(default=None)) -> dict[str, object]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        changed = set_prospect_suppression(conn, tenant_id=request.tenant_id, prospect_id=request.prospect_id, suppressed=request.suppressed, reason=request.reason); conn.commit()
    if not changed: raise HTTPException(status_code=404, detail="prospect not found")
    return {"status": "updated", "prospect_id": str(request.prospect_id), "suppressed": request.suppressed}

@app.get("/api/v1/review/customer-opportunities")
def review_customer_opportunities(tenant_id: UUID, status: str = "candidate", limit: int = 50, x_operator_token: str | None = Header(default=None)) -> list[dict]:
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 100: raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    try:
        with psycopg.connect(_dsn()) as conn: return list_customer_opportunities(conn, tenant_id=tenant_id, status=status, limit=limit)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/api/v1/review/recurring-demand")
def review_recurring_demand(tenant_id: UUID, status: str = "active", limit: int = 50, x_operator_token: str | None = Header(default=None)) -> list[dict]:
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 100: raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    try:
        with psycopg.connect(_dsn()) as conn: return list_patterns(conn, tenant_id=tenant_id, status=status, limit=limit)
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
