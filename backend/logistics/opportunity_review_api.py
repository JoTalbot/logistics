from __future__ import annotations

from uuid import UUID

import psycopg
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

from .api import app, _dsn, _operator_auth
from .opportunity_review import OpportunityReview, apply_opportunity_review, list_opportunity_review_history, opportunity_review_metrics

class OpportunityReviewRequest(BaseModel):
    tenant_id: UUID
    opportunity_id: UUID
    status: str
    operator_ref: str = Field(min_length=1)
    reason: str = Field(min_length=1)

@app.post('/api/v1/review/opportunities/decision')
def review_opportunity_decision(request: OpportunityReviewRequest, x_operator_token: str | None = Header(default=None)) -> dict[str, object]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            result = apply_opportunity_review(conn, tenant_id=request.tenant_id, review=OpportunityReview(request.opportunity_id, request.status, request.operator_ref, request.reason))
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail='database is not available') from exc

@app.get('/api/v1/review/opportunities/metrics')
def review_opportunity_metrics_endpoint(tenant_id: UUID, x_operator_token: str | None = Header(default=None)) -> dict[str, object]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        return {'tenant_id': str(tenant_id), **opportunity_review_metrics(conn, tenant_id=tenant_id)}

@app.get('/api/v1/review/opportunities/{opportunity_id}/history')
def review_opportunity_history(opportunity_id: UUID, tenant_id: UUID, limit: int = 50, x_operator_token: str | None = Header(default=None)) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            return list_opportunity_review_history(conn, tenant_id=tenant_id, opportunity_id=opportunity_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
