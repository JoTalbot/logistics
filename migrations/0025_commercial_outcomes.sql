CREATE TABLE IF NOT EXISTS commercial_outcomes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  opportunity_id uuid NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  outcome text NOT NULL CHECK (outcome IN ('won','lost','cancelled','unknown')),
  offered_price numeric(18,4),
  actual_revenue numeric(18,4),
  actual_cost numeric(18,4),
  actual_margin numeric(18,4),
  currency text,
  operator_ref text NOT NULL,
  reason text NOT NULL,
  outcome_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, opportunity_id)
);

CREATE TABLE IF NOT EXISTS commercial_outcome_history (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  opportunity_id uuid NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  previous_outcome text,
  new_outcome text NOT NULL CHECK (new_outcome IN ('won','lost','cancelled','unknown')),
  offered_price numeric(18,4),
  actual_revenue numeric(18,4),
  actual_cost numeric(18,4),
  actual_margin numeric(18,4),
  currency text,
  operator_ref text NOT NULL,
  reason text NOT NULL,
  outcome_at timestamptz NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS commercial_outcomes_queue_idx
  ON commercial_outcomes(tenant_id, outcome, outcome_at DESC);
CREATE INDEX IF NOT EXISTS commercial_outcome_history_queue_idx
  ON commercial_outcome_history(tenant_id, opportunity_id, created_at DESC);
