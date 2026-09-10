from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    tenant_id: UUID
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: UUID | None = None
    schema_version: int = 1
    payload: dict[str, Any]


@dataclass(frozen=True)
class CommandContext:
    tenant_id: UUID
    actor_id: UUID
    correlation_id: UUID
    risk_level: str = "normal"


class EventBus:
    def publish(self, event: EventEnvelope) -> None:
        raise NotImplementedError


class InMemoryEventBus(EventBus):
    def __init__(self) -> None:
        self.events: list[EventEnvelope] = []

    def publish(self, event: EventEnvelope) -> None:
        self.events.append(event)
