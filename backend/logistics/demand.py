from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .domain import Load


@dataclass(frozen=True)
class DemandSignal:
    customer_id: str
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DemandProfile:
    customer_id: str
    preferred_countries: frozenset[str] = frozenset()
    preferred_cargo: frozenset[str] = frozenset()
    min_weight_kg: int = 0
    max_weight_kg: int = 2_000_000
    min_price: Decimal = Decimal("0")
    max_price: Decimal | None = None


def score_customer_demand(load: Load, profile: DemandProfile) -> DemandSignal:
    score = 0.0
    reasons: list[str] = []
    if load.cargo_type.casefold() in {x.casefold() for x in profile.preferred_cargo}:
        score += 0.35
        reasons.append("cargo_match")
    if profile.min_weight_kg <= load.weight_kg <= profile.max_weight_kg:
        score += 0.25
        reasons.append("weight_match")
    if load.offered_price >= profile.min_price and (profile.max_price is None or load.offered_price <= profile.max_price):
        score += 0.25
        reasons.append("price_match")
    countries = {s.location.country_code for s in load.stops if s.location.country_code}
    if not profile.preferred_countries or countries.intersection(profile.preferred_countries):
        score += 0.15
        reasons.append("geography_match")
    return DemandSignal(profile.customer_id, min(1.0, score), tuple(reasons))


def rank_demand(load: Load, profiles: Iterable[DemandProfile]) -> list[DemandSignal]:
    return sorted((score_customer_demand(load, profile) for profile in profiles), key=lambda x: x.score, reverse=True)
