from __future__ import annotations

from uuid import UUID

import psycopg
from fastapi import Header, HTTPException

from .api import app, _dsn, _operator_auth
from .commercial_calibration import load_calibration_observations, calibrate_observations


@app.get("/api/v1/review/commercial-calibration")
def review_commercial_calibration(
    tenant_id: UUID,
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
        return {
            "tenant_id": str(tenant_id),
            "cases": report.cases,
            "terminal_cases": report.terminal_cases,
            "win_rate": report.win_rate,
            "mean_prediction_error": str(report.mean_prediction_error) if report.mean_prediction_error is not None else None,
            "mean_abs_prediction_error": str(report.mean_abs_prediction_error) if report.mean_abs_prediction_error is not None else None,
            "drift_detected": report.drift_detected,
            "drift_reason": report.drift_reason,
            "bands": [
                {
                    "band": band.band,
                    "cases": band.cases,
                    "terminal_cases": band.terminal_cases,
                    "wins": band.wins,
                    "win_rate": band.win_rate,
                    "mean_prediction_error": str(band.mean_prediction_error) if band.mean_prediction_error is not None else None,
                    "mean_abs_prediction_error": str(band.mean_abs_prediction_error) if band.mean_abs_prediction_error is not None else None,
                    "sufficient_sample": band.sufficient_sample,
                }
                for band in report.bands
            ],
            "recommendation": (
                "review scoring calibration manually"
                if report.drift_detected
                else "no scoring change recommended"
            ),
            "policy_mutation": False,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="database is not available") from exc
