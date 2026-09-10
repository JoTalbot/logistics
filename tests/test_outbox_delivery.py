from datetime import datetime, timedelta, timezone
from uuid import uuid4

from logistics.events import EventEnvelope
from logistics.outbox import InMemoryOutbox, retry_delay


def make_event():
    return EventEnvelope(
        event_type="LOAD_FOUND",
        aggregate_type="load",
        aggregate_id=uuid4(),
        tenant_id=uuid4(),
        payload={"source": "telegram"},
    )


def test_retry_delay_is_bounded_exponential():
    assert retry_delay(1) == 5
    assert retry_delay(2) == 10
    assert retry_delay(3) == 20
    assert retry_delay(20) == 3600


def test_in_memory_outbox_claim_lease_and_retry():
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)

    lease = outbox.claim(limit=1, lease_seconds=60, worker_id="w1")[0]
    assert lease.attempt == 1
    assert outbox.pending() == []

    outbox.mark_failed(str(event.event_id), "provider unavailable", datetime.now(timezone.utc) - timedelta(seconds=1))
    assert outbox.last_error(str(event.event_id)) == "provider unavailable"
    assert outbox.claim(limit=1, worker_id="w2")[0].attempt == 2


def test_in_memory_outbox_published_is_not_pending():
    outbox = InMemoryOutbox()
    event = make_event()
    outbox.append(event)
    outbox.claim(limit=1)
    outbox.mark_published(str(event.event_id))
    assert outbox.pending() == []
