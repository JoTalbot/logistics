"""Canonicalization and validation for persisted Telegram load ads."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from .domain import CanonicalLocation, Load, LoadStatus, LoadStop
from .telegram import ParsedLoadAd


@dataclass(frozen=True)
class LoadValidation:
    accepted: bool
    reasons: tuple[str, ...]


def validate_parsed_ad(ad: ParsedLoadAd, *, min_confidence: float = 0.6) -> LoadValidation:
    reasons: list[str] = []
    if not ad.origin:
        reasons.append("missing_origin")
    if not ad.destination:
        reasons.append("missing_destination")
    if not ad.cargo_type:
        reasons.append("missing_cargo_type")
    if not ad.weight_kg:
        reasons.append("missing_weight")
    if not ad.price or ad.price <= 0:
        reasons.append("missing_price")
    if not ad.currency or len(ad.currency) != 3:
        reasons.append("missing_currency")
    if ad.confidence < min_confidence:
        reasons.append("low_confidence")
    return LoadValidation(not reasons, tuple(reasons))


def parsed_ad_to_load(
    ad: ParsedLoadAd,
    *,
    tenant_id: UUID,
    min_confidence: float = 0.6,
) -> Load:
    validation = validate_parsed_ad(ad, min_confidence=min_confidence)
    if not validation.accepted:
        raise ValueError("Telegram ad cannot become canonical Load: " + ",".join(validation.reasons))

    assert ad.origin and ad.destination and ad.cargo_type and ad.weight_kg and ad.price and ad.currency
    stops = [
        LoadStop(
            sequence=0,
            kind="pickup",
            location=CanonicalLocation(
                raw_address=ad.origin,
                normalized_address=ad.origin,
                confidence=ad.confidence,
                provenance="telegram-regex-v1",
            ),
        ),
        LoadStop(
            sequence=1,
            kind="delivery",
            location=CanonicalLocation(
                raw_address=ad.destination,
                normalized_address=ad.destination,
                confidence=ad.confidence,
                provenance="telegram-regex-v1",
            ),
        ),
    ]
    return Load(
        tenant_id=tenant_id,
        external_ref=f"telegram:{ad.source_chat}:{ad.source_message_id}",
        cargo_type=ad.cargo_type,
        weight_kg=ad.weight_kg,
        offered_price=Decimal(ad.price),
        currency=ad.currency,
        stops=stops,
        status=LoadStatus.NORMALIZED,
    )
