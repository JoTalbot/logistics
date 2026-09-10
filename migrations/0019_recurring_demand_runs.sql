CREATE TABLE IF NOT EXISTS recurring_demand_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at timestamptz NOT NULL,
  completed_at timestamptz,
  status text NOT NULL CHECK (status IN ('running','succeeded','failed')),
  tenant_count integer NOT NULL DEFAULT 0 CHECK (tenant_count >= 0),
  pattern_count integer NOT NULL DEFAULT 0 CHECK (pattern_count >= 0),
  error_text text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS recurring_demand_runs_status_time_idx
  ON recurring_demand_runs (status, started_at DESC);
