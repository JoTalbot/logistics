-- Historical market observations preserve every verified provider snapshot.
CREATE TABLE IF NOT EXISTS market_observation_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  source text NOT NULL,
  external_ref text NOT NULL,
  observed_at timestamptz NOT NULL,
  payload jsonb NOT NULL,
  captured_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, source, external_ref, observed_at)
);

CREATE INDEX IF NOT EXISTS market_observation_history_lane_time_idx
  ON market_observation_history(tenant_id, source, observed_at DESC);

CREATE INDEX IF NOT EXISTS market_observation_history_ref_time_idx
  ON market_observation_history(tenant_id, source, external_ref, observed_at DESC);

CREATE TABLE IF NOT EXISTS review_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  resource_type text NOT NULL,
  resource_id uuid NOT NULL,
  decision text NOT NULL CHECK (decision IN ('approve','reject','hold')),
  operator_ref text NOT NULL,
  reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS review_audit_resource_idx
  ON review_audit(tenant_id, resource_type, resource_id, created_at DESC);
