from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from .customer_opportunities import CustomerOpportunity


def upsert_customer_opportunity(
    conn: Any,
    *,
    tenant_id: UUID,
    opportunity: CustomerOpportunity,
) -> UUID:
    row = conn.execute(
        """
        INSERT INTO customer_opportunities
          (tenant_id, customer_id, load_id, demand_score, commercial_score,
           freshness_score, total_score, reasons, observed_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,now())
        ON CONFLICT (tenant_id, customer_id, load_id)
        DO UPDATE SET
          demand_score=EXCLUDED.demand_score,
          commercial_score=EXCLUDED.commercial_score,
          freshness_score=EXCLUDED.freshness_score,
          total_score=EXCLUDED.total_score,
          reasons=EXCLUDED.reasons,
          observed_at=EXCLUDED.observed_at,
          updated_at=now()
        WHERE EXCLUDED.observed_at >= customer_opportunities.observed_at
        RETURNING id
        """,
        (
            tenant_id,
            opportunity.customer_id,
            opportunity.load_id,
            opportunity.demand_score,
            opportunity.commercial_score,
            opportunity.freshness_score,
            opportunity.total_score,
            json.dumps(list(opportunity.reasons), ensure_ascii=False),
            opportunity.observed_at if hasattr(opportunity, "observed_at") else None,
        ),
    ).fetchone()
    if row:
        return row[0]
    existing = conn.execute(
        "SELECT id FROM customer_opportunities WHERE tenant_id=%s AND customer_id=%s AND load_id=%s",
        (tenant_id, opportunity.customer_id, opportunity.load_id),
    ).fetchone()
    if not existing:
        raise RuntimeError("customer opportunity disappeared during stale update")
    return existing[0]


def list_customer_opportunities(
    conn: Any,
    *,
    tenant_id: UUID,
    status: str = "candidate",
    limit: int = 50,
) -> list[dict[str, Any]]:
    if status not in {"candidate", "reviewed", "accepted", "rejected"}:
        raise ValueError("invalid opportunity status")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    rows = conn.execute(
        """
        SELECT id, customer_id, load_id, demand_score, commercial_score,
               freshness_score, total_score, reasons, observed_at, status,
               created_at, updated_at
        FROM customer_opportunities
        WHERE tenant_id=%s AND status=%s
        ORDER BY total_score DESC, observed_at DESC
        LIMIT %s
        """,
        (tenant_id, status, limit),
    ).fetchall()
    keys = ("id", "customer_id", "load_id", "demand_score", "commercial_score", "freshness_score", "total_score", "reasons", "observed_at", "status", "created_at", "updated_at")
    result = []
    for row in rows:
        item = dict(zip(keys, row))
        item["id"] = str(item["id"])
        for key in ("observed_at", "created_at", "updated_at"):
            item[key] = item[key].isoformat()
        for key in ("demand_score", "commercial_score", "freshness_score", "total_score"):
            item[key] = float(item[key])
        result.append(item)
    return result
