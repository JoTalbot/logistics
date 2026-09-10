ALTER TABLE outbox_events
  ADD COLUMN IF NOT EXISTS attempt_count integer NOT NULL DEFAULT 0
    CHECK (attempt_count >= 0),
  ADD COLUMN IF NOT EXISTS available_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS locked_at timestamptz,
  ADD COLUMN IF NOT EXISTS locked_by text,
  ADD COLUMN IF NOT EXISTS last_error text;

UPDATE outbox_events
SET available_at = COALESCE(available_at, now())
WHERE available_at IS NULL;

DROP INDEX IF EXISTS outbox_pending_idx;
CREATE INDEX IF NOT EXISTS outbox_delivery_pending_idx
  ON outbox_events(available_at, occurred_at)
  WHERE published_at IS NULL;

CREATE INDEX IF NOT EXISTS outbox_delivery_lease_idx
  ON outbox_events(locked_at)
  WHERE published_at IS NULL AND locked_at IS NOT NULL;
