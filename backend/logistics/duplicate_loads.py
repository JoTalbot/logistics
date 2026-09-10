from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID


def find_duplicate_load_groups(
    conn: Any, *, tenant_id: UUID, window_hours: int = 48, limit: int = 1000
) -> list[list[UUID]]:
    """Find likely duplicate canonical loads without mutating data.

    Matching is tenant-scoped and based on normalized route, cargo, weight and currency,
    with a bounded creation-time window. Price is intentionally excluded because the same
    shipment can be reposted with a changed offer.
    """
    if window_hours < 1 or window_hours > 720:
        raise ValueError("window_hours must be between 1 and 720")
    if limit < 1 or limit > 10_000:
        raise ValueError("limit must be between 1 and 10000")
    rows = conn.execute(
        """
        WITH signatures AS (
            SELECT l.id, l.created_at,
                   md5(concat_ws('|', l.cargo_type, l.weight_kg::text, l.currency,
                       COALESCE(string_agg(
                           ls.sequence::text || ':' || ls.kind || ':' || lower(trim(ls.normalized_address)),
                           '>' ORDER BY ls.sequence), ''))) AS signature
            FROM loads l
            JOIN load_stops ls ON ls.load_id=l.id
            WHERE l.tenant_id=%s AND l.status <> 'cancelled'
            GROUP BY l.id, l.created_at, l.cargo_type, l.weight_kg, l.currency
        ), pairs AS (
            SELECT a.id AS left_id, b.id AS right_id
            FROM signatures a
            JOIN signatures b ON a.signature=b.signature
              AND a.id < b.id
              AND b.created_at BETWEEN a.created_at AND a.created_at + (%s * interval '1 hour')
        )
        SELECT left_id, right_id FROM pairs ORDER BY left_id, right_id LIMIT %s
        """,
        (tenant_id, window_hours, limit),
    ).fetchall()
    groups: list[list[UUID]] = []
    for left_id, right_id in rows:
        groups.append([left_id, right_id])
    return groups
