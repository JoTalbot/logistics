-- Durable, tenant-scoped shadow/simulation decisions.
-- This is a decision record, not a second review-audit store: human review remains in review_audit.
CREATE TABLE IF NOT EXISTS autonomy_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  decision_id text NOT NULL,
  correlation_id text,
  action text NOT NULL,
  confidence double precision NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  tier text NOT NULL CHECK (tier IN ('AUTO','REVIEW','HIGH_RISK','BLOCK')),
  mode text NOT NULL CHECK (mode IN ('SIMULATION','SHADOW')),
  policy_version text NOT NULL,
  classification_reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, decision_id)
);

CREATE INDEX IF NOT EXISTS autonomy_decisions_queue_idx
  ON autonomy_decisions(tenant_id, tier, created_at ASC);
CREATE INDEX IF NOT EXISTS autonomy_decisions_correlation_idx
  ON autonomy_decisions(tenant_id, correlation_id, created_at DESC);
