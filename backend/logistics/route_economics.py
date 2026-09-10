from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from typing import Iterable

from .market_observations import MarketObservation, extract_price, observation_is_fresh


@dataclass(frozen=True)
class RouteEconomics:
    revenue: Decimal
    direct_cost: Decimal
    risk_reserve: Decimal
    clean_profit: Decimal
    margin_rate: Decimal
    risk_adjusted_profit: Decimal


def calculate_route_economics(
    *,
    revenue: Decimal,
    distance_km: Decimal,
    fuel_cost_per_km: Decimal,
    tolls: Decimal = Decimal("0"),
    driver_cost: Decimal = Decimal("0"),
    overhead: Decimal = Decimal("0"),
    risk_rate: Decimal = Decimal("0"),
) -> RouteEconomics:
    values = (revenue, distance_km, fuel_cost_per_km, tolls, driver_cost, overhead, risk_rate)
    if any(value < 0 for value in values) or risk_rate > 1:
        raise ValueError("invalid route economics inputs")
    direct_cost = distance_km * fuel_cost_per_km + tolls + driver_cost + overhead
    risk_reserve = direct_cost * risk_rate
    clean_profit = revenue - direct_cost
    risk_adjusted_profit = revenue - direct_cost - risk_reserve
    margin_rate = clean_profit / revenue if revenue else Decimal("0")
    return RouteEconomics(
        revenue=revenue,
        direct_cost=direct_cost,
        risk_reserve=risk_reserve,
        clean_profit=clean_profit,
        margin_rate=margin_rate,
        risk_adjusted_profit=risk_adjusted_profit,
    )


@dataclass(frozen=True)
class PriceTrendPoint:
    period_start: datetime
    currency: str | None
    count: int
    median_price: Decimal
    minimum_price: Decimal
    maximum_price: Decimal


def price_trend(
    observations: Iterable[MarketObservation],
    *,
    route_key: str | None = None,
    now: datetime | None = None,
    window_days: int = 30,
    bucket_days: int = 7,
) -> list[PriceTrendPoint]:
    if window_days < 1 or bucket_days < 1:
        raise ValueError("window_days and bucket_days must be positive")
    current = now or datetime.now(timezone.utc)
    start = current - timedelta(days=window_days)
    buckets: dict[datetime, list[tuple[Decimal, str | None]]] = {}
    for observation in observations:
        if not observation_is_fresh(observation.observed_at, now=current, max_age_seconds=window_days * 86400):
            continue
        if observation.observed_at < start:
            continue
        if route_key is not None and observation.payload.get("route_key") != route_key:
            continue
        price, currency = extract_price(observation.payload)
        if price is None or price < 0:
            continue
        elapsed_days = (observation.observed_at - start).total_seconds() / 86400
        bucket_no = int(elapsed_days // bucket_days)
        period = start + timedelta(days=bucket_no * bucket_days)
        period = period.replace(hour=0, minute=0, second=0, microsecond=0)
        buckets.setdefault(period, []).append((price, currency))
    result: list[PriceTrendPoint] = []
    for period in sorted(buckets):
        values = buckets[period]
        prices = sorted(value for value, _ in values)
        currencies = {currency for _, currency in values if currency}
        result.append(PriceTrendPoint(period, currencies.pop() if len(currencies) == 1 else None, len(prices), median(prices), prices[0], prices[-1]))
    return result


def recommended_price(
    *,
    market_median: Decimal,
    economics: RouteEconomics,
    target_margin_rate: Decimal = Decimal("0.12"),
) -> Decimal:
    if market_median < 0 or target_margin_rate < 0 or target_margin_rate >= 1:
        raise ValueError("invalid recommendation inputs")
    cost_floor = economics.direct_cost + economics.risk_reserve
    margin_floor = cost_floor / (Decimal("1") - target_margin_rate)
    return max(market_median, margin_floor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
