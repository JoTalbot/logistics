from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class BusinessKPI:
    """Deterministic operational/commercial KPI snapshot."""

    ingestion_volume: int
    opportunities_created: int
    high_priority_opportunities: int
    open_priority_work: int
    successful_deliveries: int
    failed_deliveries: int
    delivery_success_rate: float
    recurring_demand_profiles: int
    fresh_recurring_demand_profiles: int
    provider_errors: int


def _scalar(execute: Callable[[str, tuple[Any, ...]], Any], sql: str, params: tuple[Any, ...] = ()) -> int:
    row = execute(sql, params).fetchone()
    if not row:
        return 0
    return int(row[0] or 0)


def snapshot_kpis(execute: Callable[[str, tuple[Any, ...]], Any], tenant_id: str) -> BusinessKPI:
    """Read a tenant-scoped KPI snapshot from an SQL executor.

    The executor is intentionally tiny so the KPI layer can be unit-tested without
    coupling the calculation to a particular SQLAlchemy session implementation.
    """

    ingestion = _scalar(execute, "SELECT count(*) FROM market_observations WHERE tenant_id = %s", (tenant_id,))
    opportunities = _scalar(execute, "SELECT count(*) FROM customer_opportunities WHERE tenant_id = %s", (tenant_id,))
    high_priority = _scalar(
        execute,
        "SELECT count(*) FROM opportunities WHERE tenant_id = %s AND priority_score >= %s",
        (tenant_id, 0.75),
    )
    open_priority = _scalar(
        execute,
        "SELECT count(*) FROM opportunities WHERE tenant_id = %s AND priority_status = %s",
        (tenant_id, "candidate"),
    )
    successful = _scalar(
        execute,
        "SELECT count(*) FROM outbox_delivery_attempts WHERE tenant_id = %s AND outcome = %s",
        (tenant_id, "succeeded"),
    )
    failed = _scalar(
        execute,
        "SELECT count(*) FROM outbox_delivery_attempts WHERE tenant_id = %s AND outcome = %s",
        (tenant_id, "failed"),
    )
    recurring = _scalar(execute, "SELECT count(*) FROM recurring_demand_patterns WHERE tenant_id = %s", (tenant_id,))
    fresh_recurring = _scalar(
        execute,
        "SELECT count(*) FROM recurring_demand_patterns WHERE tenant_id = %s AND freshness_score >= %s",
        (tenant_id, 0.2),
    )
    provider_errors = _scalar(
        execute,
        "SELECT count(*) FROM outbox_delivery_attempts WHERE tenant_id = %s AND outcome = %s AND error_text IS NOT NULL",
        (tenant_id, "failed"),
    )
    attempts = successful + failed
    success_rate = successful / attempts if attempts else 0.0

    return BusinessKPI(
        ingestion_volume=ingestion,
        opportunities_created=opportunities,
        high_priority_opportunities=high_priority,
        open_priority_work=open_priority,
        successful_deliveries=successful,
        failed_deliveries=failed,
        delivery_success_rate=round(success_rate, 4),
        recurring_demand_profiles=recurring,
        fresh_recurring_demand_profiles=fresh_recurring,
        provider_errors=provider_errors,
    )
