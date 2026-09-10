from __future__ import annotations

from datetime import datetime
from typing import Any


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


def scheduler_health(conn: Any) -> dict[str, object]:
    row = conn.execute(
        """SELECT id, started_at, completed_at, status, tenant_count, pattern_count, error_text
             FROM recurring_demand_runs
            ORDER BY started_at DESC
            LIMIT 1"""
    ).fetchone()
    if row is None:
        return {"status": "never_run", "last_run": None}
    return {
        "status": row[3],
        "last_run": {
            "id": str(row[0]),
            "started_at": row[1].isoformat(),
            "completed_at": row[2].isoformat() if row[2] else None,
            "tenant_count": int(row[4]),
            "pattern_count": int(row[5]),
            "error_text": row[6],
        },
    }
