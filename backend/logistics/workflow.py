from __future__ import annotations

from uuid import UUID, uuid4

from .domain import Load, Opportunity
from .events import CommandContext, EventEnvelope, EventBus
from .optimization import DeterministicOptimizationService, normalize_address


def evaluate_load(load: Load, context: CommandContext, bus: EventBus, optimizer: DeterministicOptimizationService | None = None) -> Opportunity:
    normalized_stops = [stop.model_copy(update={"location": normalize_address(stop.location.raw_address)}) for stop in load.stops]
    normalized = load.model_copy(update={"stops": normalized_stops})
    opportunity = (optimizer or DeterministicOptimizationService()).score(normalized)
    bus.publish(EventEnvelope(
        event_type="load.opportunity_scored",
        aggregate_type="load",
        aggregate_id=normalized.id,
        tenant_id=context.tenant_id,
        correlation_id=context.correlation_id,
        causation_id=uuid4(),
        payload={"opportunity": opportunity.model_dump(mode="json")},
    ))
    return opportunity
