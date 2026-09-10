CREATE TABLE IF NOT EXISTS recurring_demand_patterns (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    pattern_key text NOT NULL,
    observations integer NOT NULL CHECK (observations >= 2),
    first_seen timestamptz NOT NULL,
    last_seen timestamptz NOT NULL,
    median_interval_hours numeric(12,2),
    regularity_score numeric(6,4) NOT NULL CHECK (regularity_score BETWEEN 0 AND 1),
    recurrence_score numeric(6,4) NOT NULL CHECK (recurrence_score BETWEEN 0 AND 1),
    freshness_score numeric(6,4) NOT NULL CHECK (freshness_score BETWEEN 0 AND 1),
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','stale','reviewed')), 
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, pattern_key)
);

CREATE TABLE IF NOT EXISTS recurring_demand_evidence (
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    pattern_id uuid NOT NULL REFERENCES recurring_demand_patterns(id) ON DELETE CASCADE,
    load_id uuid NOT NULL,
    observed_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, pattern_id, load_id)
);

CREATE INDEX IF NOT EXISTS idx_recurring_demand_queue
    ON recurring_demand_patterns (tenant_id, status, recurrence_score DESC, freshness_score DESC, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_recurring_demand_evidence
    ON recurring_demand_evidence (tenant_id, pattern_id, observed_at DESC);
