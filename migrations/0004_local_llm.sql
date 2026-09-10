-- Local LLM outputs are separate review-only candidates, never executable intents.
CREATE TABLE IF NOT EXISTS telegram_llm_config (
  tenant_id uuid PRIMARY KEY REFERENCES tenants(id),
  activated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS telegram_llm_jobs (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  source_message_id uuid NOT NULL REFERENCES telegram_source_messages(id),
  parser_version text NOT NULL,
  model text NOT NULL,
  model_digest text NOT NULL,
  content_hash text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed','skipped')),
  attempts integer NOT NULL DEFAULT 0,
  available_at timestamptz NOT NULL DEFAULT now(),
  normalized jsonb,
  error_type text,
  duration_seconds numeric,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(source_message_id,parser_version,model_digest)
);
CREATE INDEX IF NOT EXISTS telegram_llm_jobs_pending_idx ON telegram_llm_jobs(status,available_at,id);
CREATE INDEX IF NOT EXISTS telegram_llm_jobs_cache_idx ON telegram_llm_jobs(tenant_id,content_hash,parser_version,model_digest) WHERE status='completed';
