CREATE TABLE IF NOT EXISTS commercial_outcome_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  opportunity_id uuid NOT NULL REFERENCES opportunities(id),
  outcome text NOT NULL CHECK (outcome IN ('won','lost','cancelled','unknown')),
  currency text NOT NULL,
  offered_price numeric(14,2),
  actual_revenue numeric(14,2),
  actual_cost numeric(14,2),
  actual_margin numeric(14,2),
  operator_ref text NOT NULL,
  reason text NOT NULL,
  correlation_id text,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  CHECK (offered_price IS NULL OR offered_price >= 0),
  CHECK (actual_revenue IS NULL OR actual_revenue >= 0),
  CHECK (actual_cost IS NULL OR actual_cost >= 0),
  CHECK (actual_margin IS NULL OR actual_margin = actual_revenue - actual_cost)
);

CREATE INDEX IF NOT EXISTS commercial_outcome_history_tenant_opp_idx
  ON commercial_outcome_history(tenant_id, opportunity_id, recorded_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS commercial_outcome_history_tenant_outcome_idx
  ON commercial_outcome_history(tenant_id, outcome, recorded_at DESC);
