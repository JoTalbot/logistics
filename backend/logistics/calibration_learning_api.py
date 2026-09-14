from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import psycopg
from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

from .api import app, _dsn, _operator_auth
from .calibration_learning import (
    acknowledge_recommendation,
    build_shadow_recommendations,
    create_calibration_snapshot,
    learning_metrics,
    list_recommendation_events,
    list_recommendations,
    persist_shadow_recommendations,
)
from .commercial_calibration import calibrate_observations, load_calibration_observations


class RecommendationDecision(BaseModel):
    decision: str
    operator_ref: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)


@app.post("/api/v1/review/commercial-calibration/snapshots")
def create_review_calibration_snapshot(
    tenant_id: UUID,
    policy_version: str = "v28.1",
    limit: int = 5000,
    min_sample: int = 10,
    drift_win_rate_delta: float = 0.15,
    drift_error_delta: float = 100.0,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    try:
        from decimal import Decimal
        with psycopg.connect(_dsn()) as conn:
            report = calibrate_observations(
                load_calibration_observations(conn, tenant_id=tenant_id, limit=limit),
                min_sample=min_sample,
                drift_win_rate_delta=drift_win_rate_delta,
                drift_error_delta=Decimal(str(drift_error_delta)),
            )
            snapshot = create_calibration_snapshot(conn, tenant_id=tenant_id, policy_version=policy_version, report=report)
            recommendations = build_shadow_recommendations(report, snapshot_id=snapshot.snapshot_id)
            persisted = persist_shadow_recommendations(conn, tenant_id=tenant_id, snapshot_id=snapshot.snapshot_id, recommendations=recommendations)
            conn.commit()
        return {
            "snapshot_id": str(snapshot.snapshot_id),
            "tenant_id": str(tenant_id),
            "policy_version": policy_version,
            "cases": report.cases,
            "terminal_cases": report.terminal_cases,
            "win_rate": report.win_rate,
            "drift_detected": report.drift_detected,
            "drift_reason": report.drift_reason,
            "recommendations_created": persisted,
            "policy_mutation": False,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="database is not available") from exc


@app.get("/api/v1/review/commercial-calibration/snapshots")
def review_calibration_snapshots(
    tenant_id: UUID,
    limit: int = 100,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    with psycopg.connect(_dsn()) as conn:
        rows = conn.execute(
            """
            SELECT id, policy_version, cases, terminal_cases, win_rate,
                   mean_prediction_error, mean_abs_prediction_error,
                   drift_detected, drift_reason, created_at
              FROM calibration_snapshots
             WHERE tenant_id=%s
             ORDER BY created_at DESC, id DESC
             LIMIT %s
            """,
            (tenant_id, limit),
        ).fetchall()
    return [
        {
            "id": str(row[0]), "policy_version": row[1], "cases": row[2], "terminal_cases": row[3],
            "win_rate": row[4], "mean_prediction_error": str(row[5]) if row[5] is not None else None,
            "mean_abs_prediction_error": str(row[6]) if row[6] is not None else None,
            "drift_detected": row[7], "drift_reason": row[8], "created_at": row[9].isoformat(),
        }
        for row in rows
    ]


@app.get("/api/v1/review/commercial-calibration/recommendations")
def review_calibration_recommendations(
    tenant_id: UUID,
    status: str | None = None,
    limit: int = 100,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            return list_recommendations(conn, tenant_id=tenant_id, status=status, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="database is not available") from exc


@app.post("/api/v1/review/commercial-calibration/recommendations/{recommendation_id}/ack")
def decide_calibration_recommendation(
    recommendation_id: UUID,
    tenant_id: UUID,
    body: RecommendationDecision,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    try:
        with psycopg.connect(_dsn()) as conn:
            acknowledge_recommendation(
                conn, tenant_id=tenant_id, recommendation_id=recommendation_id,
                decision=body.decision, operator_ref=body.operator_ref, reason=body.reason,
            )
            conn.commit()
        return {"recommendation_id": str(recommendation_id), "tenant_id": str(tenant_id), "decision": body.decision, "policy_mutation": False}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="database is not available") from exc


@app.get("/api/v1/review/commercial-calibration/recommendations/{recommendation_id}/events")
def review_calibration_recommendation_events(
    recommendation_id: UUID,
    tenant_id: UUID,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        return list_recommendation_events(conn, tenant_id=tenant_id, recommendation_id=recommendation_id)


@app.get("/api/v1/review/commercial-calibration/learning-metrics")
def review_calibration_learning_metrics(
    tenant_id: UUID,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        return {"tenant_id": str(tenant_id), **learning_metrics(conn, tenant_id=tenant_id), "policy_mutation": False}
