from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from .demand import DemandSignal


@dataclass(frozen=True)
class CustomerOpportunity:
    customer_id: str
    load_id: str
    demand_score: float
    commercial_score: float
    freshness_score: float
    total_score: float
    reasons: tuple[str, ...]


def freshness_score(observed_at: datetime, *, now: datetime | None = None) -> float:
    """Return a deterministic 0..1 freshness score, decaying over 72 hours."""
    reference = now or datetime.now(timezone.utc)
    age_hours = max(0.0, (reference - observed_at).total_seconds() / 3600.0)
    return round(max(0.0, 1.0 - age_hours / 72.0), 4)


def score_customer_opportunity(
    *,
    customer_id: str,
    load_id: str,
    demand: DemandSignal,
    observed_at: datetime,
    commercial_score: float,
    now: datetime | None = None,
) -> CustomerOpportunity:
    if not 0 <= commercial_score <= 1:
        raise ValueError("commercial_score must be between 0 and 1")
    fresh = freshness_score(observed_at, now=now)
    total = round(demand.score * 0.55 + commercial_score * 0.30 + fresh * 0.15, 4)
    reasons = tuple(demand.reasons) + (("fresh_signal",) if fresh >= 0.5 else ())
    return CustomerOpportunity(customer_id, load_id, demand.score, commercial_score, fresh, total, reasons)


def rank_customer_opportunities(items: list[CustomerOpportunity]) -> list[CustomerOpportunity]:
    return sorted(items, key=lambda x: (-x.total_score, x.customer_id, x.load_id))
