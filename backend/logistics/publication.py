from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol
from uuid import UUID

from .domain import Load
from .policy import PolicyDecision, PolicyEngine


@dataclass(frozen=True)
class PublicationRequest:
    tenant_id: UUID
    load: Load
    provider: str
    actor_roles: frozenset[str]
    markup_percent: Decimal = Decimal("0")
    risk_level: str = "normal"
    source_provenance: str = "canonical"


@dataclass(frozen=True)
class PublicationPayload:
    provider: str
    external_ref: str
    title: str
    body: str
    price: Decimal
    currency: str
    provenance: str
    role: str


@dataclass(frozen=True)
class PublicationDecision:
    allowed: bool
    policy: PolicyDecision
    payload: PublicationPayload | None = None


class PublicationAdapter(Protocol):
    provider: str

    def render(self, request: PublicationRequest) -> PublicationPayload: ...


class GenericFreightExchangeAdapter:
    """Provider-neutral publication renderer; network publication is intentionally separate."""

    provider = "freight_exchange"

    def render(self, request: PublicationRequest) -> PublicationPayload:
        load = request.load
        pickup = next(stop for stop in load.stops if stop.kind == "pickup")
        delivery = next(stop for stop in load.stops if stop.kind == "delivery")
        multiplier = Decimal("1") + request.markup_percent / Decimal("100")
        price = (load.offered_price * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        title = f"{pickup.location.normalized_address} → {delivery.location.normalized_address} | {load.cargo_type}"
        body = (
            f"Маршрут: {pickup.location.normalized_address} → {delivery.location.normalized_address}\n"
            f"Груз: {load.cargo_type}\n"
            f"Вес: {load.weight_kg / 1000:g} т\n"
            f"Ставка: {price} {load.currency}\n"
            f"Источник: {request.source_provenance}\n"
            "Публикация от имени экспедитора."
        )
        return PublicationPayload(
            provider=self.provider,
            external_ref=load.external_ref or str(load.id),
            title=title,
            body=body,
            price=price,
            currency=load.currency,
            provenance=request.source_provenance,
            role="forwarder",
        )


class PublicationEngine:
    def __init__(self, policy: PolicyEngine | None = None):
        self.policy = policy or PolicyEngine()

    def prepare(self, request: PublicationRequest, adapter: PublicationAdapter) -> PublicationDecision:
        decision = self.policy.decide("autonomous.publish_load", request.risk_level, set(request.actor_roles))
        if not decision.allowed:
            return PublicationDecision(False, decision)
        if request.markup_percent < 0 or request.markup_percent > Decimal("100"):
            return PublicationDecision(False, PolicyDecision(False, "markup outside allowed range"))
        if request.load.status.value == "cancelled":
            return PublicationDecision(False, PolicyDecision(False, "cancelled load cannot be published"))
        return PublicationDecision(True, decision, adapter.render(request))
