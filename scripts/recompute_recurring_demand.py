from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import psycopg

from logistics.recurring_demand_db import recompute_recurring_demand


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute recurring demand from canonical Telegram loads")
    parser.add_argument("--tenant-id", required=True, type=UUID)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()
    if args.days < 1 or args.days > 3650:
        parser.error("--days must be between 1 and 3650")
    dsn = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://", 1)
    if not dsn:
        raise SystemExit("DATABASE_URL is not configured")
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)
    with psycopg.connect(dsn) as conn:
        count = recompute_recurring_demand(
            conn,
            tenant_id=args.tenant_id,
            now=now,
            since=since,
            limit=args.limit,
        )
        conn.commit()
    print(f"recurring-demand patterns persisted: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
