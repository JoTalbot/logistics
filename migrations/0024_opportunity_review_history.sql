CREATE TABLE IF NOT EXISTS opportunity_review_history (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  opportunity_id uuid NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  previous_status text,
  new_status text NOT NULL CHECK (new_status IN ('candidate','reviewed','accepted','rejected','hold')),
  operator_ref text NOT NULL,
  reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS opportunity_review_history_queue_idx
  ON opportunity_review_history(tenant_id, opportunity_id, created_at DESC);
CREATE INDEX IF NOT EXISTS opportunity_review_history_status_idx
  ON opportunity_review_history(tenant_id, new_status, created_at DESC);
