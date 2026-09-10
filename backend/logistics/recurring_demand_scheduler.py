from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import psycopg

from .recurring_demand_db import recompute_recurring_demand
from .recurring_demand_health import finish_run, start_run


def recompute_all_tenants(conn, *, now: datetime, days: int = 90, limit: int = 5000) -> tuple[int, int]:
    if days < 1 or days > 3650:
        raise ValueError("days must be between 1 and 3650")
    if limit < 1 or limit > 50_000:
        raise ValueError("limit must be between 1 and 50000")
    tenants = conn.execute("SELECT id FROM tenants ORDER BY id").fetchall()
    since = now - timedelta(days=days)
    total = 0
    for (tenant_id,) in tenants:
        total += recompute_recurring_demand(
            conn,
            tenant_id=tenant_id,
            now=now,
            since=since,
            limit=limit,
        )
    return len(tenants), total


def run_forever(*, interval_seconds: int = 21_600, days: int = 90, limit: int = 5000) -> None:
    if interval_seconds < 3600:
        raise ValueError("interval_seconds must be at least one hour")
    dsn = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://", 1)
    if not dsn:
        raise RuntimeError("DATABASE_URL is not configured")
    while True:
        now = datetime.now(timezone.utc)
        with psycopg.connect(dsn) as conn:
            run_id = start_run(conn, started_at=now)
            try:
                tenant_count, total = recompute_all_tenants(conn, now=now, days=days, limit=limit)
            except Exception as exc:
                finish_run(conn, run_id=run_id, completed_at=datetime.now(timezone.utc), status="failed", tenant_count=0, pattern_count=0, error_text=str(exc)[:2000])
                conn.commit()
                raise
            else:
                finish_run(conn, run_id=run_id, completed_at=datetime.now(timezone.utc), status="succeeded", tenant_count=tenant_count, pattern_count=total)
                conn.commit()
        print(f"recurring-demand scheduled recomputation: {total} patterns", flush=True)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_forever()
