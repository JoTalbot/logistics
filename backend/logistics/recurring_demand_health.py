from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


DEFAULT_STALE_AFTER_HOURS = 12
DEFAULT_RUNNING_TIMEOUT_HOURS = 2


def start_run(conn: Any, *, started_at: datetime) -> Any:
    row = conn.execute(
        "INSERT INTO recurring_demand_runs (started_at, status) VALUES (%s, 'running') RETURNING id",
        (started_at,),
    ).fetchone()
    return row[0]


def finish_run(
    conn: Any,
    *,
    run_id: Any,
    completed_at: datetime,
    status: str,
    tenant_count: int,
    pattern_count: int,
    error_text: str | None = None,
) -> None:
    if status not in {"succeeded", "failed"}:
        raise ValueError("status must be succeeded or failed")
    if tenant_count < 0 or pattern_count < 0:
        raise ValueError("counts must be non-negative")
    conn.execute(
        """UPDATE recurring_demand_runs
           SET completed_at=%s, status=%s, tenant_count=%s, pattern_count=%s, error_text=%s
         WHERE id=%s""",
        (completed_at, status, tenant_count, pattern_count, error_text, run_id),
    )


def scheduler_health(
    conn: Any,
    *,
    now: datetime | None = None,
    stale_after_hours: int = DEFAULT_STALE_AFTER_HOURS,
    running_timeout_hours: int = DEFAULT_RUNNING_TIMEOUT_HOURS,
) -> dict[str, object]:
    if stale_after_hours < 1:
        raise ValueError("stale_after_hours must be at least 1")
    if running_timeout_hours < 1:
        raise ValueError("running_timeout_hours must be at least 1")

    reference = now or datetime.now(timezone.utc)
    row = conn.execute(
        """SELECT id, started_at, completed_at, status, tenant_count, pattern_count, error_text
             FROM recurring_demand_runs
            ORDER BY started_at DESC
            LIMIT 1"""
    ).fetchone()
    if row is None:
        return {
            "status": "never_run",
            "operational_status": "critical",
            "thresholds": {
                "stale_after_hours": stale_after_hours,
                "running_timeout_hours": running_timeout_hours,
            },
            "last_run": None,
        }

    started_at = row[1]
    age_seconds = max(0.0, (reference - started_at).total_seconds())
    if row[3] == "running":
        operational_status = "stale" if age_seconds >= running_timeout_hours * 3600 else "running"
    elif row[3] == "succeeded":
        operational_status = "stale" if age_seconds >= stale_after_hours * 3600 else "healthy"
    else:
        operational_status = "failed"

    return {
        "status": row[3],
        "operational_status": operational_status,
        "thresholds": {
            "stale_after_hours": stale_after_hours,
            "running_timeout_hours": running_timeout_hours,
        },
        "last_run": {
            "id": str(row[0]),
            "started_at": started_at.isoformat(),
            "completed_at": row[2].isoformat() if row[2] else None,
            "age_seconds": int(age_seconds),
            "tenant_count": int(row[4]),
            "pattern_count": int(row[5]),
            "error_text": row[6],
        },
    }
