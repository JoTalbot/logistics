CREATE TABLE IF NOT EXISTS customer_demand_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  customer_party_id uuid NOT NULL REFERENCES parties(id),
  preferred_countries jsonb NOT NULL DEFAULT '[]'::jsonb,
  preferred_cargo jsonb NOT NULL DEFAULT '[]'::jsonb,
  min_weight_kg integer NOT NULL DEFAULT 0,
  max_weight_kg integer NOT NULL DEFAULT 2000000,
  min_price numeric(14,2) NOT NULL DEFAULT 0,
  max_price numeric(14,2),
  active boolean NOT NULL DEFAULT true,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, customer_party_id)
);

CREATE TABLE IF NOT EXISTS demand_opportunities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  load_id uuid NOT NULL REFERENCES loads(id) ON DELETE CASCADE,
  customer_profile_id uuid NOT NULL REFERENCES customer_demand_profiles(id) ON DELETE CASCADE,
  score numeric(7,6) NOT NULL CHECK (score BETWEEN 0 AND 1),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'candidate',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(load_id, customer_profile_id)
);
CREATE INDEX IF NOT EXISTS demand_opportunities_score_idx ON demand_opportunities(tenant_id, score DESC);
