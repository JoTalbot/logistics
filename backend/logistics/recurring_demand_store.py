from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from .recurring_demand import DemandPattern


def upsert_pattern(conn: Any, *, tenant_id: UUID, pattern: DemandPattern, freshness: float) -> UUID:
    if not 0 <= freshness <= 1:
        raise ValueError("freshness must be between 0 and 1")
    row = conn.execute(
        """
        INSERT INTO recurring_demand_patterns
          (tenant_id, pattern_key, observations, first_seen, last_seen,
           median_interval_hours, regularity_score, recurrence_score,
           freshness_score, reasons, status, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,
                CASE WHEN %s < 0.2 THEN 'stale' ELSE 'active' END, now())
        ON CONFLICT (tenant_id, pattern_key)
        DO UPDATE SET
          observations=EXCLUDED.observations,
          first_seen=LEAST(recurring_demand_patterns.first_seen, EXCLUDED.first_seen),
          last_seen=GREATEST(recurring_demand_patterns.last_seen, EXCLUDED.last_seen),
          median_interval_hours=EXCLUDED.median_interval_hours,
          regularity_score=EXCLUDED.regularity_score,
          recurrence_score=EXCLUDED.recurrence_score,
          freshness_score=EXCLUDED.freshness_score,
          reasons=EXCLUDED.reasons,
          status=CASE WHEN EXCLUDED.freshness_score < 0.2 THEN 'stale' ELSE 'active' END,
          updated_at=now()
        RETURNING id
        """,
        (tenant_id, pattern.key, pattern.observations, pattern.first_seen, pattern.last_seen,
         pattern.median_interval_hours, pattern.regularity_score, pattern.recurrence_score,
         freshness, json.dumps(list(pattern.reasons), ensure_ascii=False), freshness),
    ).fetchone()
    return row[0]


def record_evidence(conn: Any, *, tenant_id: UUID, pattern_id: UUID, load_id: UUID, observed_at) -> None:
    conn.execute(
        """
        INSERT INTO recurring_demand_evidence (tenant_id, pattern_id, load_id, observed_at)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (tenant_id, pattern_id, load_id) DO NOTHING
        """,
        (tenant_id, pattern_id, load_id, observed_at),
    )


def list_patterns(conn: Any, *, tenant_id: UUID, status: str = "active", limit: int = 50) -> list[dict[str, Any]]:
    if status not in {"active", "stale", "reviewed"}:
        raise ValueError("invalid recurring-demand status")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT id, pattern_key, observations, first_seen, last_seen,
               median_interval_hours, regularity_score, recurrence_score,
               freshness_score, reasons, status, created_at, updated_at
        FROM recurring_demand_patterns
        WHERE tenant_id=%s AND status=%s
        ORDER BY recurrence_score DESC, freshness_score DESC, last_seen DESC
        LIMIT %s
        """, (tenant_id, status, limit)
    ).fetchall()
    keys = ("id", "pattern_key", "observations", "first_seen", "last_seen", "median_interval_hours", "regularity_score", "recurrence_score", "freshness_score", "reasons", "status", "created_at", "updated_at")
    result = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = str(item["id"])
        for key in ("first_seen", "last_seen", "created_at", "updated_at"):
            item[key] = item[key].isoformat()
        for key in ("median_interval_hours", "regularity_score", "recurrence_score", "freshness_score"):
            if item[key] is not None:
                item[key] = float(item[key])
        result.append(item)
    return result
