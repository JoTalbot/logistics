"""Safe orchestration for Telegram -> canonical loads -> commercial discovery.

The pipeline is deliberately evidence-only: it never publishes, negotiates,
contracts, mutates prices, or performs financial actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from .commercial_pipeline import CommercialCandidate, build_commercial_candidates
from .domain import Load, Vehicle
from .market_ops import PricingInput
from .telegram import ParsedLoadAd, TelegramSourceMessage, parse_messages
from .telegram_pipeline import LoadValidation, parsed_ad_to_load, validate_parsed_ad


@dataclass(frozen=True)
class DiscoveryItem:
    message: TelegramSourceMessage
    parsed: ParsedLoadAd
    validation: LoadValidation
    load: Load | None


@dataclass(frozen=True)
class DiscoveryReport:
    items: tuple[DiscoveryItem, ...]
    candidates: tuple[CommercialCandidate, ...]

    @property
    def accepted_count(self) -> int:
        return sum(item.load is not None for item in self.items)

    @property
    def rejected_count(self) -> int:
        return len(self.items) - self.accepted_count


def build_discovery_report(
    messages: Iterable[TelegramSourceMessage],
    carriers: Iterable[Vehicle],
    pricing: PricingInput,
    *,
    tenant_id: UUID,
    min_confidence: float = 0.6,
    min_observations: int = 3,
    now=None,
) -> DiscoveryReport:
    """Run deterministic discovery over already-collected Telegram messages."""
    source_messages = list(messages)
    parsed_ads = parse_messages(source_messages)
    items: list[DiscoveryItem] = []
    loads: list[Load] = []

    for message, parsed in zip(source_messages, parsed_ads):
        validation = validate_parsed_ad(parsed, min_confidence=min_confidence)
        load = None
        if validation.accepted:
            load = parsed_ad_to_load(parsed, tenant_id=tenant_id, min_confidence=min_confidence)
            loads.append(load)
        items.append(DiscoveryItem(message, parsed, validation, load))

    candidates = build_commercial_candidates(
        loads,
        carriers,
        pricing,
        now=now,
        min_observations=min_observations,
    )
    return DiscoveryReport(tuple(items), tuple(candidates))


def candidate_digest(candidate: CommercialCandidate) -> dict[str, object]:
    """Return stable, UI/API-friendly evidence for an opportunity candidate."""
    return {
        "load_id": str(candidate.load.id),
        "external_ref": candidate.load.external_ref,
        "origin": candidate.load.stops[0].location.normalized_address if candidate.load.stops else None,
        "destination": candidate.load.stops[-1].location.normalized_address if candidate.load.stops else None,
        "cargo_type": candidate.load.cargo_type,
        "weight_kg": candidate.load.weight_kg,
        "offered_price": str(candidate.load.offered_price),
        "currency": candidate.load.currency,
        "estimated_price": str(candidate.price.target_price),
        "opportunity_score": candidate.opportunity_score,
        "priority_score": candidate.priority_score,
        "carrier_match_count": len(candidate.carrier_matches),
        "recurring_score": candidate.recurring_score,
        "reasons": list(candidate.reasons),
    }
