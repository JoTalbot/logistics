from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import UUID

from .domain import Load
from .recurring_demand import detect_recurring_demand, pattern_freshness
from .recurring_demand_store import record_evidence, upsert_pattern


def persist_recurring_demand(
    conn,
    *,
    tenant_id: UUID,
    loads: Iterable[Load],
    now: datetime | None = None,
    min_observations: int = 3,
) -> int:
    """Detect recurring patterns from canonical loads and persist patterns/evidence."""
    reference = now or datetime.now(timezone.utc)
    items = list(loads)
    patterns = detect_recurring_demand(items, min_observations=min_observations)
    by_key: dict[str, list[Load]] = {}
    from .recurring_demand import demand_pattern_key
    for load in items:
        by_key.setdefault(demand_pattern_key(load), []).append(load)

    persisted = 0
    for pattern in patterns:
        freshness = pattern_freshness(pattern, now=reference)
        pattern_id = upsert_pattern(conn, tenant_id=tenant_id, pattern=pattern, freshness=freshness)
        for load in by_key.get(pattern.key, []):
            load_id = getattr(load, "id", None)
            if load_id is None:
                continue
            record_evidence(
                conn,
                tenant_id=tenant_id,
                pattern_id=pattern_id,
                load_id=UUID(str(load_id)),
                observed_at=load.created_at,
            )
        persisted += 1
    return persisted
