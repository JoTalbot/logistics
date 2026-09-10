from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from .delivery_telemetry import finish_attempt, record_attempt
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
            for row in rows:
                record_attempt(
                    conn,
                    event_id=str(row["event_id"]),
                    tenant_id=str(row["tenant_id"]),
                    attempt_number=int(row["attempt_count"]),
                    worker_id=self.worker_id,
                    started_at=now,
                )
            conn.commit()
            return list(rows)

    def ack(self, event_id: str, attempt: int | None = None) -> None:
        with psycopg.connect(self.dsn) as conn:
            result = conn.execute(
                "UPDATE outbox_events SET published_at=now(), locked_at=NULL, locked_by=NULL, last_error=NULL WHERE event_id=%s AND locked_by=%s AND published_at IS NULL",
                (event_id, self.worker_id),
            )
            if result.rowcount != 1:
                conn.rollback()
                return
            if attempt is not None:
                finish_attempt(conn, event_id=event_id, attempt_number=attempt, outcome="succeeded")
            conn.commit()

    def fail(self, event_id: str, attempt: int, error: str, max_attempts: int = 12) -> None:
        delay = retry_delay(min(attempt, max_attempts))
        terminal = attempt >= max_attempts
        bounded_error = error[:4000]
        with psycopg.connect(self.dsn) as conn:
            result = conn.execute(
                """
                UPDATE outbox_events
                   SET available_at = CASE WHEN %(terminal)s THEN 'infinity'::timestamptz ELSE now() + (%(delay)s * interval '1 second') END,
                       locked_at = NULL,
                       locked_by = NULL,
                       last_error = %(error)s
                 WHERE event_id=%(event_id)s AND locked_by=%(worker)s AND published_at IS NULL
                """,
                {"terminal": terminal, "delay": delay, "error": bounded_error, "event_id": event_id, "worker": self.worker_id},
            )
            if result.rowcount != 1:
                conn.rollback()
                return
            finish_attempt(conn, event_id=event_id, attempt_number=attempt, outcome="failed", error_text=bounded_error)
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
            event_id = str(row["event_id"])
            attempt = int(row["attempt_count"])
            try:
                publisher(row)
                self.ack(event_id, attempt)
                results.append(DeliveryResult(event_id, True))
            except Exception as exc:
                self.fail(event_id, attempt, repr(exc))
                results.append(DeliveryResult(event_id, False, repr(exc)))
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
