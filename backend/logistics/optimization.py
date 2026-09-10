from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from decimal import Decimal

from .domain import CanonicalLocation, GeoPoint, Load, Opportunity


def normalize_address(raw: str) -> CanonicalLocation:
    text = re.sub(r"\\s+", " ", raw.strip())
    text = re.sub(r"[,;]+", ", ", text)
    return CanonicalLocation(raw_address=raw, normalized_address=text, confidence=0.0)


@dataclass(frozen=True)
class RoutingEstimate:
    distance_km: Decimal
    duration_hours: Decimal


class DeterministicRoutingProvider:
    """Offline-safe routing substitute for tests/replay.

    It deliberately does not pretend to know road reality. Production providers
    plug into the RoutingProvider interface described in the architecture docs.
    """

    def estimate(self, load: Load) -> RoutingEstimate:
        names = "|".join(stop.location.normalized_address.lower() for stop in load.stops)
        digest = hashlib.sha256(names.encode()).digest()
        distance = Decimal(100 + digest[0] % 901)
        duration = (distance / Decimal("55")).quantize(Decimal("0.01"))
        return RoutingEstimate(distance_km=distance, duration_hours=duration)


class DeterministicOptimizationService:
    def __init__(self, routing: DeterministicRoutingProvider | None = None) -> None:
        self.routing = routing or DeterministicRoutingProvider()

    def score(self, load: Load) -> Opportunity:
        estimate = self.routing.estimate(load)
        cost = (estimate.distance_km * Decimal("18")).quantize(Decimal("0.01"))
        margin = (load.offered_price - cost).quantize(Decimal("0.01"))
        risk_adjusted = (margin * Decimal("0.85")).quantize(Decimal("0.01"))
        score = max(0.0, min(1.0, float(risk_adjusted / load.offered_price)))
        reasons = [f"distance_km={estimate.distance_km}", f"duration_h={estimate.duration_hours}"]
        if risk_adjusted <= 0:
            reasons.append("risk_adjusted_margin_non_positive")
        else:
            reasons.append("positive_risk_adjusted_margin")
        return Opportunity(
            tenant_id=load.tenant_id,
            load_id=load.id,
            score=score,
            estimated_cost=cost,
            estimated_margin=margin,
            risk_adjusted_margin=risk_adjusted,
            reasons=reasons,
        )
