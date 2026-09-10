-- Record delivery attempts so replay/retry behavior is observable without
-- changing the idempotent event identity of the outbox itself.
CREATE TABLE IF NOT EXISTS outbox_delivery_attempts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id uuid NOT NULL REFERENCES outbox_events(event_id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  attempt_number integer NOT NULL CHECK (attempt_number > 0),
  worker_id text NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  outcome text NOT NULL DEFAULT 'running'
    CHECK (outcome IN ('running','succeeded','failed')),
  error_text text,
  UNIQUE(event_id, attempt_number)
);

CREATE INDEX IF NOT EXISTS outbox_delivery_attempts_tenant_time_idx
  ON outbox_delivery_attempts(tenant_id, started_at DESC);
CREATE INDEX IF NOT EXISTS outbox_delivery_attempts_event_idx
  ON outbox_delivery_attempts(event_id, attempt_number DESC);
