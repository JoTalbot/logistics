from __future__ import annotations

from typing import Protocol

from .events import EventEnvelope


class Outbox(Protocol):
    def append(self, event: EventEnvelope) -> None: ...
    def pending(self, limit: int = 100) -> list[EventEnvelope]: ...
    def mark_published(self, event_id: str) -> None: ...


class InMemoryOutbox:
    def __init__(self) -> None:
        self._events: dict[str, EventEnvelope] = {}
        self._published: set[str] = set()

    def append(self, event: EventEnvelope) -> None:
        self._events.setdefault(str(event.event_id), event)

    def pending(self, limit: int = 100) -> list[EventEnvelope]:
        return [e for key, e in list(self._events.items()) if key not in self._published][:limit]

    def mark_published(self, event_id: str) -> None:
        self._published.add(event_id)
