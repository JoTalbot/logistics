from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def record_attempt(
    conn: Any,
    *,
    event_id: str,
    tenant_id: str,
    attempt_number: int,
    worker_id: str,
    started_at: datetime | None = None,
) -> None:
    """Record one delivery attempt idempotently."""
    if attempt_number < 1:
        raise ValueError("attempt_number must be positive")
    conn.execute(
        """
        INSERT INTO outbox_delivery_attempts
          (event_id, tenant_id, attempt_number, worker_id, started_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (event_id, attempt_number) DO NOTHING
        """,
        (event_id, tenant_id, attempt_number, worker_id, started_at or datetime.now(timezone.utc)),
    )


def finish_attempt(
    conn: Any,
    *,
    event_id: str,
    attempt_number: int,
    outcome: str,
    error_text: str | None = None,
    finished_at: datetime | None = None,
) -> None:
    if outcome not in {"succeeded", "failed"}:
        raise ValueError("outcome must be succeeded or failed")
    conn.execute(
        """
        UPDATE outbox_delivery_attempts
           SET finished_at=%s, outcome=%s, error_text=%s
         WHERE event_id=%s AND attempt_number=%s
        """,
        (finished_at or datetime.now(timezone.utc), outcome, error_text[:4000] if error_text else None,
         event_id, attempt_number),
    )
