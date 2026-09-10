CREATE TABLE IF NOT EXISTS market_observations (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  provider text NOT NULL,
  external_ref text,
  kind text NOT NULL CHECK (kind IN ('cargo','transport')),
  observed_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL,
  source_provenance text NOT NULL,
  UNIQUE (tenant_id, provider, kind, external_ref)
);

CREATE TABLE IF NOT EXISTS carrier_profiles (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  party_id uuid,
  capacity_kg integer CHECK (capacity_kg > 0),
  available_from timestamptz,
  equipment jsonb NOT NULL DEFAULT '{}'::jsonb,
  lanes jsonb NOT NULL DEFAULT '[]'::jsonb,
  reliability_score numeric(6,5) NOT NULL DEFAULT 0.5 CHECK (reliability_score >= 0 AND reliability_score <= 1),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS opportunity_matches (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  load_id uuid NOT NULL,
  carrier_profile_id uuid,
  score numeric(8,5) NOT NULL CHECK (score >= 0 AND score <= 1),
  estimated_cost numeric(18,2),
  estimated_margin numeric(18,2),
  risk_adjusted_margin numeric(18,2),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'candidate',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS market_observations_lookup_idx ON market_observations(tenant_id, provider, kind, observed_at DESC);
CREATE INDEX IF NOT EXISTS opportunity_matches_rank_idx ON opportunity_matches(tenant_id, status, score DESC);
