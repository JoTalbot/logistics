from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from .domain import Load, Opportunity
from .route_economics import PriceTrendPoint, RouteEconomics, recommended_price


@dataclass(frozen=True)
class OpportunityRecommendation:
    score: float
    recommended_price: Decimal
    market_median: Decimal | None
    risk_adjusted_profit: Decimal
    reasons: tuple[str, ...]


def recommend_opportunity(
    load: Load,
    opportunity: Opportunity,
    economics: RouteEconomics,
    *,
    trend: Sequence[PriceTrendPoint] = (),
    target_margin_rate: Decimal = Decimal("0.12"),
) -> OpportunityRecommendation:
    """Combine internal route economics with recent market evidence.

    Market evidence is advisory: it cannot reduce the economic safety floor.
    Currency is considered compatible only when every trend point has the same
    currency as the load; otherwise market median is deliberately ignored.
    """
    if target_margin_rate < 0 or target_margin_rate >= 1:
        raise ValueError("target_margin_rate must be between 0 and 1")
    if economics.revenue != load.offered_price:
        raise ValueError("economics revenue must match load offered price")

    compatible = [point for point in trend if point.currency == load.currency]
    market_median = compatible[-1].median_price if compatible else None
    floor = recommended_price(
        market_median=market_median or Decimal("0"),
        economics=economics,
        target_margin_rate=target_margin_rate,
    )

    reasons: list[str] = []
    if economics.risk_adjusted_profit > 0:
        reasons.append("positive_risk_adjusted_profit")
    else:
        reasons.append("non_positive_risk_adjusted_profit")
    if market_median is not None:
        reasons.append("recent_market_median_available")
        if load.offered_price >= market_median:
            reasons.append("offered_price_at_or_above_market_median")
        else:
            reasons.append("offered_price_below_market_median")
    else:
        reasons.append("market_median_unavailable_or_currency_mismatch")
    if floor > load.offered_price:
        reasons.append("price_below_safe_recommendation")

    economic_signal = Decimal(str(max(0.0, min(1.0, float(economics.risk_adjusted_profit / economics.revenue) if economics.revenue else 0.0))))
    market_signal = Decimal("0.5")
    if market_median is not None and market_median > 0:
        market_signal = max(Decimal("0"), min(Decimal("1"), load.offered_price / market_median))
    score = float(min(Decimal("1"), max(Decimal("0"), economic_signal * Decimal("0.75") + market_signal * Decimal("0.25"))))
    return OpportunityRecommendation(
        score=score,
        recommended_price=floor,
        market_median=market_median,
        risk_adjusted_profit=economics.risk_adjusted_profit,
        reasons=tuple(reasons),
    )
