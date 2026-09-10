from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Iterable

from .market_observations import MarketObservation, extract_price


@dataclass(frozen=True)
class PriceSnapshot:
    currency: str | None
    count: int
    median_price: Decimal | None
    minimum_price: Decimal | None
    maximum_price: Decimal | None


def summarize_prices(observations: Iterable[MarketObservation]) -> PriceSnapshot:
    prices: list[tuple[Decimal, str | None]] = []
    for observation in observations:
        price, currency = extract_price(observation.payload)
        if price is not None and price >= 0:
            prices.append((price, currency))
    if not prices:
        return PriceSnapshot(None, 0, None, None, None)
    currencies = {currency for _, currency in prices if currency}
    currency = currencies.pop() if len(currencies) == 1 else None
    values = sorted(price for price, _ in prices)
    return PriceSnapshot(currency, len(values), median(values), values[0], values[-1])
