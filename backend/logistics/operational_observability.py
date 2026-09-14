"""Pure operational observability primitives for deterministic evidence."""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Iterable


@dataclass(frozen=True)
class ProviderLatency:
    provider: str
    samples_ms: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        if any(sample < 0 for sample in self.samples_ms):
            raise ValueError("latency samples must be non-negative")

    @property
    def sample_count(self) -> int:
        return len(self.samples_ms)

    @property
    def mean_ms(self) -> float:
        return round(mean(self.samples_ms), 3) if self.samples_ms else 0.0


@dataclass(frozen=True)
class RouteQualityObservation:
    route: str
    expected_score: float
    observed_score: float

    def __post_init__(self) -> None:
        if not self.route.strip():
            raise ValueError("route must not be empty")
        for name, value in (("expected_score", self.expected_score), ("observed_score", self.observed_score)):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    @property
    def absolute_error(self) -> float:
        return abs(self.expected_score - self.observed_score)

    @property
    def regression(self) -> float:
        """Positive score loss only; improvements are not regressions."""
        return max(0.0, self.expected_score - self.observed_score)


@dataclass(frozen=True)
class CostAttribution:
    component: str
    units: int
    unit_cost: float

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must not be empty")
        if self.units < 0 or self.unit_cost < 0:
            raise ValueError("cost units and unit_cost must be non-negative")

    @property
    def total_cost(self) -> float:
        return round(self.units * self.unit_cost, 6)


@dataclass(frozen=True)
class OperationalObservabilityReport:
    provider_latency_ms: dict[str, float]
    provider_samples: dict[str, int]
    route_quality_mean_absolute_error: float
    route_quality_regressions: int
    attributed_cost: float


def build_observability_report(
    latencies: Iterable[ProviderLatency],
    routes: Iterable[RouteQualityObservation],
    costs: Iterable[CostAttribution],
    *,
    regression_threshold: float = 0.10,
) -> OperationalObservabilityReport:
    """Aggregate deterministic latency, route-quality and cost evidence."""
    if regression_threshold < 0:
        raise ValueError("regression_threshold must be non-negative")

    latency_items = tuple(latencies)
    if len({item.provider for item in latency_items}) != len(latency_items):
        raise ValueError("provider names must be unique")

    route_items = tuple(routes)
    cost_items = tuple(costs)

    errors = tuple(item.absolute_error for item in route_items)
    regressions = sum(item.regression >= regression_threshold for item in route_items) if route_items else 0
    return OperationalObservabilityReport(
        provider_latency_ms={item.provider: item.mean_ms for item in latency_items},
        provider_samples={item.provider: item.sample_count for item in latency_items},
        route_quality_mean_absolute_error=round(mean(errors), 4) if errors else 0.0,
        route_quality_regressions=regressions,
        attributed_cost=round(sum(item.total_cost for item in cost_items), 6),
    )
