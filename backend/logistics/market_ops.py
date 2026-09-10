from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .domain import Load, Opportunity, Vehicle


@dataclass(frozen=True)
class PricingInput:
    distance_km: Decimal
    fuel_cost_per_km: Decimal = Decimal("0")
    tolls: Decimal = Decimal("0")
    driver_cost: Decimal = Decimal("0")
    overhead: Decimal = Decimal("0")
    risk_rate: Decimal = Decimal("0")
    target_margin_rate: Decimal = Decimal("0.12")


@dataclass(frozen=True)
class PriceEstimate:
    cost: Decimal
    minimum_price: Decimal
    target_price: Decimal
    risk_reserve: Decimal


def estimate_price(load: Load, inputs: PricingInput) -> PriceEstimate:
    if inputs.distance_km < 0 or inputs.risk_rate < 0 or inputs.risk_rate > 1:
        raise ValueError("invalid pricing inputs")
    variable = inputs.distance_km * inputs.fuel_cost_per_km
    cost = variable + inputs.tolls + inputs.driver_cost + inputs.overhead
    risk = cost * inputs.risk_rate
    protected = cost + risk
    target = protected / (Decimal("1") - inputs.target_margin_rate)
    return PriceEstimate(cost=cost, minimum_price=protected, target_price=target, risk_reserve=risk)


def score_opportunity(load: Load, estimate: PriceEstimate, risk_penalty: Decimal = Decimal("0")) -> Opportunity:
    margin = load.offered_price - estimate.cost
    risk_adjusted = load.offered_price - estimate.cost - estimate.risk_reserve
    ratio = risk_adjusted / load.offered_price if load.offered_price else Decimal("0")
    score = max(Decimal("0"), min(Decimal("1"), ratio - risk_penalty))
    reasons = []
    if risk_adjusted > 0:
        reasons.append("positive_risk_adjusted_margin")
    else:
        reasons.append("negative_risk_adjusted_margin")
    return Opportunity(
        tenant_id=load.tenant_id,
        load_id=load.id,
        score=float(score),
        estimated_cost=estimate.cost,
        estimated_margin=margin,
        risk_adjusted_margin=risk_adjusted,
        reasons=reasons,
    )


@dataclass(frozen=True)
class MatchCandidate:
    carrier_id: str
    score: float
    reasons: tuple[str, ...]


def match_carriers(load: Load, carriers: Iterable[Vehicle], *, risk_limit: float = 0.35) -> list[MatchCandidate]:
    result: list[MatchCandidate] = []
    for carrier in carriers:
        if carrier.capacity_kg < load.weight_kg:
            continue
        score = 0.7
        reasons = ["capacity_feasible"]
        if carrier.available_from is not None:
            score += 0.2
            reasons.append("availability_known")
        score = min(1.0, score)
        result.append(MatchCandidate(str(carrier.carrier_party_id), score, tuple(reasons)))
    return sorted(result, key=lambda item: item.score, reverse=True)


@dataclass(frozen=True)
class NegotiationPolicy:
    min_price: Decimal
    target_price: Decimal
    max_rounds: int = 3
    max_discount_rate: Decimal = Decimal("0.10")
    critical_risk_requires_human: bool = True


def next_counteroffer(current: Decimal, policy: NegotiationPolicy, round_no: int, risk_level: str = "normal") -> tuple[Decimal, bool]:
    if round_no >= policy.max_rounds:
        return current, True
    if risk_level == "critical" and policy.critical_risk_requires_human:
        return current, True
    floor = max(policy.min_price, policy.target_price * (Decimal("1") - policy.max_discount_rate))
    if current <= floor:
        return current, True
    proposal = max(floor, current - (current - policy.target_price) / Decimal("2"))
    return proposal.quantize(Decimal("0.01")), False
