from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from .domain import Load, Vehicle


@dataclass(frozen=True)
class Pricing:
    revenue: Decimal
    cost: Decimal
    margin: Decimal
    risk_adjusted_margin: Decimal


def price_load(load: Load, *, cost: Decimal, risk: Decimal = Decimal('0')) -> Pricing:
    if cost < 0 or risk < 0 or risk > 1:
        raise ValueError('cost >= 0 and risk must be between 0 and 1')
    margin = load.offered_price - cost
    return Pricing(load.offered_price, cost, margin, margin * (Decimal('1') - risk))


def match_vehicle(load: Load, vehicle: Vehicle) -> tuple[float, list[str]]:
    reasons: list[str] = []
    score = 0.0
    if vehicle.capacity_kg >= load.weight_kg:
        score += 0.7
        reasons.append('capacity_fit')
    else:
        reasons.append('capacity_insufficient')
    if vehicle.available_from is None:
        score += 0.3
        reasons.append('availability_unspecified')
    else:
        pickup = next(s for s in load.stops if s.kind == 'pickup')
        if pickup.earliest is None or vehicle.available_from <= pickup.earliest:
            score += 0.3
            reasons.append('availability_fit')
        else:
            reasons.append('availability_mismatch')
    return min(1.0, score), reasons
