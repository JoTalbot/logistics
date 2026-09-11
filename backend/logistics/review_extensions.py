from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException

from .api import app, _dsn, _operator_auth
from .autonomy_store import list_exception_decisions
from .duplicate_loads import find_duplicate_load_groups
from .historical_policy_replay import aggregate_historical_policy_replay
from .recurring_demand_health import scheduler_health
import psycopg


@app.get("/api/v1/review/duplicate-loads")
def review_duplicate_loads(
    tenant_id: UUID,
    window_hours: int = 48,
    limit: int = 100,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 1000:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 1000")
    if not 1 <= window_hours <= 720:
        raise HTTPException(status_code=422, detail="window_hours must be between 1 and 720")
    with psycopg.connect(_dsn()) as conn:
        groups = find_duplicate_load_groups(conn, tenant_id=tenant_id, window_hours=window_hours, limit=limit)
    return [{"load_ids": [str(load_id) for load_id in group]} for group in groups]


@app.get("/api/v1/review/recurring-demand/health")
def review_recurring_demand_health(
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    with psycopg.connect(_dsn()) as conn:
        return scheduler_health(conn)


@app.get("/api/v1/review/autonomy-exceptions")
def review_autonomy_exceptions(
    tenant_id: UUID,
    limit: int = 100,
    x_operator_token: str | None = Header(default=None),
) -> list[dict[str, object]]:
    """Return tenant-scoped non-AUTO shadow decisions for operator review."""
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    with psycopg.connect(_dsn()) as conn:
        return list_exception_decisions(conn, tenant_id=tenant_id, limit=limit)


@app.get("/api/v1/review/autonomy-replay")
def review_autonomy_replay(
    tenant_id: UUID,
    limit: int = 10_000,
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    """Return tenant-scoped historical policy replay metrics by policy version."""
    _operator_auth(x_operator_token)
    if not 1 <= limit <= 100_000:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100000")
    with psycopg.connect(_dsn()) as conn:
        result = aggregate_historical_policy_replay(conn, tenant_id=tenant_id, limit=limit)
    return {
        "tenant_id": str(result.tenant_id),
        "reports": [
            {
                "policy_version": report.policy_version,
                "report": {
                    "cases": report.report.cases,
                    "by_tier": report.report.by_tier,
                    "successful_auto_cases": report.report.successful_auto_cases,
                    "failed_auto_cases": report.report.failed_auto_cases,
                    "auto_failure_rate": report.report.auto_failure_rate,
                    "review_or_higher_cases": report.report.review_or_higher_cases,
                },
            }
            for report in result.reports
        ],
    }
