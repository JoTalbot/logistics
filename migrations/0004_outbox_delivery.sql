ALTER TABLE outbox_events
  ADD COLUMN IF NOT EXISTS delivery_status text NOT NULL DEFAULT 'pending'
    CHECK (delivery_status IN ('pending','leased','published','retry','dead')),
  ADD COLUMN IF NOT EXISTS delivery_attempts integer NOT NULL DEFAULT 0
    CHECK (delivery_attempts >= 0),
  ADD COLUMN IF NOT EXISTS locked_until timestamptz,
  ADD COLUMN IF NOT EXISTS next_attempt_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS last_error text;

UPDATE outbox_events
SET delivery_status = CASE WHEN published_at IS NULL THEN 'pending' ELSE 'published' END,
    next_attempt_at = COALESCE(next_attempt_at, now())
WHERE delivery_status = 'pending';

DROP INDEX IF EXISTS outbox_pending_idx;
CREATE INDEX IF NOT EXISTS outbox_delivery_pending_idx
  ON outbox_events(next_attempt_at, occurred_at)
  WHERE published_at IS NULL AND delivery_status IN ('pending','retry');

CREATE INDEX IF NOT EXISTS outbox_delivery_lease_idx
  ON outbox_events(locked_until)
  WHERE published_at IS NULL AND delivery_status = 'leased';
