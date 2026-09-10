from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException

from .api import app, _dsn, _operator_auth
from .duplicate_loads import find_duplicate_load_groups
from .recurring_demand_health import scheduler_health


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
    with __import__("psycopg").connect(_dsn()) as conn:
        groups = find_duplicate_load_groups(conn, tenant_id=tenant_id, window_hours=window_hours, limit=limit)
    return [{"load_ids": [str(load_id) for load_id in group]} for group in groups]


@app.get("/api/v1/review/recurring-demand/health")
def review_recurring_demand_health(
    x_operator_token: str | None = Header(default=None),
) -> dict[str, object]:
    _operator_auth(x_operator_token)
    with __import__("psycopg").connect(_dsn()) as conn:
        return scheduler_health(conn)
