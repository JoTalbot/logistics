from __future__ import annotations

from uuid import UUID

import psycopg
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

from .api import app, _dsn, _operator_auth
from .commercial_outcomes import (
    CommercialOutcome,
    commercial_outcome_metrics,
    list_commercial_outcomes,
    prediction_actual_report,
    record_commercial_outcome,
)


class CommercialOutcomeRequest(BaseModel):
    tenant_id: UUID
    opportunity_id: UUID
    outcome: str
    currency: str = Field(min_length=1, max_length=16)
    operator_ref: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    offered_price: str | None = None
    actual_revenue: str | None = None
    actual_cost: str | None = None
    correlation_id: str | None = None


@app.post("/api/v1/review/opportunities/outcome")
def review_opportunity_outcome(
    request: CommercialOutcomeRequest,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            result = record_commercial_outcome(
                conn,
                tenant_id=request.tenant_id,
                outcome=CommercialOutcome(
                    opportunity_id=request.opportunity_id,
                    outcome=request.outcome,
                    currency=request.currency,
                    operator_ref=request.operator_ref,
                    reason=request.reason,
                    offered_price=request.offered_price,
                    actual_revenue=request.actual_revenue,
                    actual_cost=request.actual_cost,
                    correlation_id=request.correlation_id,
                ),
            )
            conn.commit()
            return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="database is not available") from exc


@app.get("/api/v1/review/commercial-outcomes/metrics")
def review_commercial_outcome_metrics(
    tenant_id: UUID,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        return {"tenant_id": str(tenant_id), **commercial_outcome_metrics(conn, tenant_id=tenant_id)}


@app.get("/api/v1/review/opportunities/{opportunity_id}/outcomes")
def review_opportunity_outcomes(
    opportunity_id: UUID,
    tenant_id: UUID,
    limit: int = 50,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            return list_commercial_outcomes(conn, tenant_id=tenant_id, opportunity_id=opportunity_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/review/commercial-outcomes/prediction-vs-actual")
def review_prediction_actual(
    tenant_id: UUID,
    limit: int = 500,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            return prediction_actual_report(conn, tenant_id=tenant_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
