CREATE TABLE IF NOT EXISTS telegram_llm_batches (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  mode text NOT NULL DEFAULT 'batch-file-v1',
  model_digest text NOT NULL,
  input_file text NOT NULL,
  input_sha256 text NOT NULL,
  item_count integer NOT NULL CHECK(item_count BETWEEN 1 AND 100),
  request_count integer NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'processing',
  completed_count integer NOT NULL DEFAULT 0,
  failed_count integer NOT NULL DEFAULT 0,
  foreign_ids integer NOT NULL DEFAULT 0,
  error_type text,
  duration_seconds numeric,
  created_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);
ALTER TABLE telegram_llm_jobs ADD COLUMN IF NOT EXISTS batch_id uuid REFERENCES telegram_llm_batches(id);
CREATE INDEX IF NOT EXISTS telegram_llm_jobs_batch_idx ON telegram_llm_jobs(batch_id);
