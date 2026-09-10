-- Persist scored customer/load opportunities for operator review.
CREATE TABLE IF NOT EXISTS customer_opportunities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  customer_id text NOT NULL,
  load_id uuid NOT NULL,
  demand_score numeric(7,6) NOT NULL CHECK (demand_score BETWEEN 0 AND 1),
  commercial_score numeric(7,6) NOT NULL CHECK (commercial_score BETWEEN 0 AND 1),
  freshness_score numeric(7,6) NOT NULL CHECK (freshness_score BETWEEN 0 AND 1),
  total_score numeric(7,6) NOT NULL CHECK (total_score BETWEEN 0 AND 1),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, customer_id, load_id)
);

CREATE INDEX IF NOT EXISTS customer_opportunities_rank_idx
  ON customer_opportunities(tenant_id, total_score DESC, updated_at DESC);
