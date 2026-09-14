CREATE TABLE IF NOT EXISTS calibration_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  policy_version text NOT NULL,
  cases integer NOT NULL CHECK (cases >= 0),
  terminal_cases integer NOT NULL CHECK (terminal_cases >= 0 AND terminal_cases <= cases),
  win_rate double precision NOT NULL CHECK (win_rate >= 0 AND win_rate <= 1),
  mean_prediction_error numeric(18,6),
  mean_abs_prediction_error numeric(18,6),
  drift_detected boolean NOT NULL,
  drift_reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS calibration_snapshots_tenant_policy_idx
  ON calibration_snapshots(tenant_id, policy_version, created_at DESC);

CREATE TABLE IF NOT EXISTS calibration_recommendations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  snapshot_id uuid NOT NULL REFERENCES calibration_snapshots(id),
  recommendation_key text NOT NULL,
  band text NOT NULL,
  current_score numeric(6,4) NOT NULL CHECK (current_score >= 0 AND current_score <= 1),
  suggested_delta numeric(6,4) NOT NULL,
  suggested_score numeric(6,4) NOT NULL CHECK (suggested_score >= 0 AND suggested_score <= 1),
  rationale text NOT NULL,
  policy_mutation boolean NOT NULL DEFAULT false CHECK (policy_mutation = false),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, recommendation_key)
);

CREATE INDEX IF NOT EXISTS calibration_recommendations_queue_idx
  ON calibration_recommendations(tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS calibration_recommendation_events (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  recommendation_id uuid NOT NULL REFERENCES calibration_recommendations(id) ON DELETE CASCADE,
  event text NOT NULL CHECK (event IN ('acknowledged','rejected')),
  operator_ref text NOT NULL,
  reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS calibration_recommendation_events_idx
  ON calibration_recommendation_events(tenant_id, recommendation_id, created_at DESC);
