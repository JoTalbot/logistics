from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .customer_opportunities import CustomerOpportunity, rank_customer_opportunities
from .domain import Load, Vehicle
from .market_ops import MatchCandidate, PriceEstimate, PricingInput, estimate_price, match_carriers, score_opportunity
from .recurring_demand import DemandPattern, demand_pattern_key, detect_recurring_demand, pattern_freshness


@dataclass(frozen=True)
class CommercialCandidate:
    load: Load
    price: PriceEstimate
    opportunity_score: float
    carrier_matches: tuple[MatchCandidate, ...]
    recurring_pattern_key: str | None
    recurring_score: float
    priority_score: float
    reasons: tuple[str, ...]


def build_commercial_candidates(
    loads: Iterable[Load],
    carriers: Iterable[Vehicle],
    pricing: PricingInput,
    *,
    now=None,
    min_observations: int = 3,
) -> list[CommercialCandidate]:
    items = list(loads)
    carrier_items = list(carriers)
    patterns = {p.key: p for p in detect_recurring_demand(items, min_observations=min_observations)}
    result: list[CommercialCandidate] = []
    for load in items:
        estimate = estimate_price(load, pricing)
        opportunity = score_opportunity(load, estimate)
        matches = tuple(match_carriers(load, carrier_items))
        key = demand_pattern_key(load)
        pattern = patterns.get(key)
        recurrence = pattern.recurrence_score * pattern_freshness(pattern, now=now) if pattern else 0.0
        priority = round(opportunity.score * 0.65 + min(1.0, len(matches) / 3.0) * 0.20 + recurrence * 0.15, 4)
        reasons = list(opportunity.reasons)
        reasons.append("carrier_match_available" if matches else "no_carrier_match")
        if pattern:
            reasons.append("recurring_demand")
        result.append(CommercialCandidate(load, estimate, opportunity.score, matches, key if pattern else None, round(recurrence, 4), priority, tuple(reasons)))
    return sorted(result, key=lambda x: (-x.priority_score, -x.opportunity_score, str(x.load.id)))


def rank_existing_customer_opportunities(items: Iterable[CustomerOpportunity]) -> list[CustomerOpportunity]:
    return rank_customer_opportunities(list(items))
