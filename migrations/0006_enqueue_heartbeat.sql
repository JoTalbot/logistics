ALTER TABLE telegram_llm_config ADD COLUMN IF NOT EXISTS enqueued_at timestamptz;
ALTER TABLE telegram_llm_config ADD COLUMN IF NOT EXISTS last_enqueued_count integer NOT NULL DEFAULT 0;
