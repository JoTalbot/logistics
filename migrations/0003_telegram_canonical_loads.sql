ALTER TABLE loads
  ADD COLUMN IF NOT EXISTS telegram_source_message_id uuid;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'loads_telegram_source_message_id_fkey'
  ) THEN
    ALTER TABLE loads
      ADD CONSTRAINT loads_telegram_source_message_id_fkey
      FOREIGN KEY (telegram_source_message_id)
      REFERENCES telegram_source_messages(id)
      ON DELETE SET NULL;
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS loads_telegram_source_message_id_uidx
  ON loads(telegram_source_message_id)
  WHERE telegram_source_message_id IS NOT NULL;

ALTER TABLE outbox_events
  ADD COLUMN IF NOT EXISTS idempotency_key text;

CREATE UNIQUE INDEX IF NOT EXISTS outbox_events_idempotency_key_uidx
  ON outbox_events(idempotency_key)
  WHERE idempotency_key IS NOT NULL;
