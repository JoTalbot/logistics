-- Persist deterministic commercial priority decisions for operator review.
ALTER TABLE opportunities
  ADD COLUMN IF NOT EXISTS priority_score numeric(6,4),
  ADD COLUMN IF NOT EXISTS priority_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS priority_updated_at timestamptz,
  ADD COLUMN IF NOT EXISTS priority_status text NOT NULL DEFAULT 'candidate'
    CHECK (priority_status IN ('candidate','reviewed','accepted','rejected','hold'));

CREATE INDEX IF NOT EXISTS opportunities_priority_queue_idx
  ON opportunities(tenant_id, priority_status, priority_score DESC NULLS LAST, priority_updated_at DESC)
  WHERE priority_score IS NOT NULL;
