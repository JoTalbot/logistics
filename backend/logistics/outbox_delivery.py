from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import time

import psycopg
from psycopg.rows import dict_row

from .outbox import retry_delay


@dataclass(frozen=True)
class DeliveryResult:
    event_id: str
    success: bool
    error: str | None = None


class PostgresOutboxDelivery:
    """Concurrent-safe outbox delivery primitive using PostgreSQL row leases."""

    def __init__(self, dsn: str, worker_id: str):
        self.dsn = dsn
        self.worker_id = worker_id

    def claim(self, limit: int = 20, lease_seconds: int = 60) -> list[dict]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            rows = conn.execute(
                """
                WITH candidates AS (
                  SELECT event_id
                  FROM outbox_events
                  WHERE published_at IS NULL
                    AND available_at <= %(now)s
                    AND (locked_at IS NULL OR locked_at < %(now)s - (%(lease)s * interval '1 second'))
                  ORDER BY occurred_at, event_id
                  FOR UPDATE SKIP LOCKED
                  LIMIT %(limit)s
                )
                UPDATE outbox_events o
                   SET locked_at = %(now)s,
                       locked_by = %(worker)s,
                       attempt_count = o.attempt_count + 1
                  FROM candidates c
                 WHERE o.event_id = c.event_id
                RETURNING o.event_id, o.event_type, o.aggregate_type, o.aggregate_id,
                          o.tenant_id, o.schema_version, o.occurred_at,
                          o.correlation_id, o.causation_id, o.payload, o.attempt_count
                """,
                {"now": now, "lease": lease_seconds, "limit": limit, "worker": self.worker_id},
            ).fetchall()
            conn.commit()
            return list(rows)

    def ack(self, event_id: str) -> None:
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                "UPDATE outbox_events SET published_at=now(), locked_at=NULL, locked_by=NULL, last_error=NULL WHERE event_id=%s AND locked_by=%s",
                (event_id, self.worker_id),
            )
            conn.commit()

    def fail(self, event_id: str, attempt: int, error: str, max_attempts: int = 12) -> None:
        delay = retry_delay(min(attempt, max_attempts))
        terminal = attempt >= max_attempts
        with psycopg.connect(self.dsn) as conn:
            conn.execute(
                """
                UPDATE outbox_events
                   SET available_at = CASE WHEN %(terminal)s THEN 'infinity'::timestamptz ELSE now() + (%(delay)s * interval '1 second') END,
                       locked_at = NULL,
                       locked_by = NULL,
                       last_error = %(error)s
                 WHERE event_id=%(event_id)s AND locked_by=%(worker)s AND published_at IS NULL
                """,
                {"terminal": terminal, "delay": delay, "error": error[:4000], "event_id": event_id, "worker": self.worker_id},
            )
            conn.commit()

    def release_expired(self) -> int:
        with psycopg.connect(self.dsn) as conn:
            result = conn.execute(
                "UPDATE outbox_events SET locked_at=NULL, locked_by=NULL WHERE published_at IS NULL AND locked_at < now() - interval '60 seconds'"
            )
            conn.commit()
            return result.rowcount

    def deliver_once(self, publisher, limit: int = 20) -> list[DeliveryResult]:
        results = []
        for row in self.claim(limit):
            try:
                publisher(row)
                self.ack(str(row["event_id"]))
                results.append(DeliveryResult(str(row["event_id"]), True))
            except Exception as exc:  # delivery boundary must record and retry provider failures
                self.fail(str(row["event_id"]), int(row["attempt_count"]), repr(exc))
                results.append(DeliveryResult(str(row["event_id"]), False, repr(exc)))
        return results


def json_publisher(callback):
    def publish(row: dict) -> None:
        callback({
            "event_id": str(row["event_id"]),
            "event_type": row["event_type"],
            "aggregate_type": row["aggregate_type"],
            "aggregate_id": str(row["aggregate_id"]),
            "tenant_id": str(row["tenant_id"]),
            "schema_version": row["schema_version"],
            "occurred_at": row["occurred_at"].isoformat(),
            "correlation_id": str(row["correlation_id"]),
            "causation_id": str(row["causation_id"]) if row["causation_id"] else None,
            "payload": row["payload"],
        })
    return publish
