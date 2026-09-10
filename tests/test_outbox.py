from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from logistics.events import EventEnvelope
from logistics.outbox import InMemoryOutbox, retry_delay


def make_event():
    return EventEnvelope(
        event_type="load.created",
        aggregate_type="load",
        aggregate_id=uuid4(),
        tenant_id=uuid4(),
        payload={"ok": True},
    )


def test_retry_delay_is_bounded_exponential():
    assert retry_delay(1) == 5
    assert retry_delay(2) == 10
    assert retry_delay(3) == 20
    assert retry_delay(20) == 3600
    with pytest.raises(ValueError):
        retry_delay(0)


def test_claim_leases_and_publish_are_idempotent():
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)
    outbox.append(event)

    leases = outbox.claim(worker_id="worker-a")
    assert len(leases) == 1
    assert leases[0].attempt == 1
    assert outbox.pending() == []

    outbox.mark_published(str(event.event_id))
    assert outbox.pending() == []


def test_failed_delivery_becomes_retryable_and_increments_attempt():
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)

    first = outbox.claim(worker_id="worker-a")[0]
    retry_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    outbox.mark_failed(str(event.event_id), "provider timeout", retry_at)

    second = outbox.claim(worker_id="worker-b")[0]
    assert first.attempt == 1
    assert second.attempt == 2
    assert outbox.last_error(str(event.event_id)) == "provider timeout"


def test_expired_lease_is_released():
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)
    lease = outbox.claim(lease_seconds=1)[0]

    future = lease.leased_until + timedelta(seconds=1)
    assert outbox.release_expired(future) == 1
    assert len(outbox.pending()) == 1
