from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol

from .events import EventEnvelope


@dataclass(frozen=True)
class DeliveryLease:
    event: EventEnvelope
    attempt: int
    leased_until: datetime


class Outbox(Protocol):
    def append(self, event: EventEnvelope) -> None: ...
    def pending(self, limit: int = 100) -> list[EventEnvelope]: ...
    def claim(self, limit: int = 100, lease_seconds: int = 60, worker_id: str = "worker") -> list[DeliveryLease]: ...
    def mark_published(self, event_id: str) -> None: ...
    def mark_failed(self, event_id: str, error: str, retry_at: datetime) -> None: ...
    def release_expired(self, now: datetime | None = None) -> int: ...


def retry_delay(attempt: int, *, base_seconds: int = 5, max_seconds: int = 3600) -> int:
    """Bounded exponential backoff: 5s, 10s, 20s ... capped at one hour."""
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    return min(max_seconds, base_seconds * (2 ** (attempt - 1)))


class InMemoryOutbox:
    """Deterministic outbox model used by unit tests and shadow execution."""

    def __init__(self) -> None:
        self._events: dict[str, EventEnvelope] = {}
        self._published: set[str] = set()
        self._attempts: dict[str, int] = {}
        self._available_at: dict[str, datetime] = {}
        self._leases: dict[str, tuple[str, datetime]] = {}
        self._errors: dict[str, str] = {}

    def append(self, event: EventEnvelope) -> None:
        key = str(event.event_id)
        if key not in self._events:
            self._events[key] = event
            self._available_at[key] = event.occurred_at

    def pending(self, limit: int = 100) -> list[EventEnvelope]:
        now = datetime.now(timezone.utc)
        result: list[EventEnvelope] = []
        for key, event in self._events.items():
            if key in self._published or self._available_at[key] > now:
                continue
            lease = self._leases.get(key)
            if lease and lease[1] > now:
                continue
            result.append(event)
            if len(result) >= limit:
                break
        return result

    def claim(self, limit: int = 100, lease_seconds: int = 60, worker_id: str = "worker") -> list[DeliveryLease]:
        if limit < 1 or lease_seconds < 1:
            raise ValueError("limit and lease_seconds must be >= 1")
        now = datetime.now(timezone.utc)
        self.release_expired(now)
        leases: list[DeliveryLease] = []
        for event in self.pending(limit):
            key = str(event.event_id)
            attempt = self._attempts.get(key, 0) + 1
            until = now + timedelta(seconds=lease_seconds)
            self._attempts[key] = attempt
            self._leases[key] = (worker_id, until)
            leases.append(DeliveryLease(event, attempt, until))
        return leases

    def mark_published(self, event_id: str) -> None:
        self._published.add(event_id)
        self._leases.pop(event_id, None)
        self._errors.pop(event_id, None)

    def mark_failed(self, event_id: str, error: str, retry_at: datetime) -> None:
        if event_id not in self._events or event_id in self._published:
            return
        self._errors[event_id] = error[:4000]
        self._available_at[event_id] = retry_at
        self._leases.pop(event_id, None)

    def release_expired(self, now: datetime | None = None) -> int:
        now = now or datetime.now(timezone.utc)
        expired = [key for key, (_, until) in self._leases.items() if until <= now]
        for key in expired:
            self._leases.pop(key, None)
        return len(expired)

    def attempt_count(self, event_id: str) -> int:
        return self._attempts.get(event_id, 0)

    def last_error(self, event_id: str) -> str | None:
        return self._errors.get(event_id)
