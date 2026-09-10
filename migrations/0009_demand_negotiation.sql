CREATE TABLE IF NOT EXISTS customer_demand_profiles (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  customer_ref text NOT NULL,
  lanes jsonb NOT NULL DEFAULT '[]'::jsonb,
  cargo_types jsonb NOT NULL DEFAULT '[]'::jsonb,
  target_price numeric(18,2),
  currency char(3),
  reliability_score numeric(6,5) NOT NULL DEFAULT 0.5 CHECK (reliability_score >= 0 AND reliability_score <= 1),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, customer_ref)
);

CREATE TABLE IF NOT EXISTS demand_opportunities (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  demand_profile_id uuid NOT NULL REFERENCES customer_demand_profiles(id),
  load_id uuid,
  score numeric(8,5) NOT NULL CHECK (score >= 0 AND score <= 1),
  expected_margin numeric(18,2),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'candidate',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS negotiation_sessions (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  load_id uuid NOT NULL,
  counterparty_ref text,
  role text NOT NULL CHECK (role IN ('forwarder','carrier','customer')),
  state text NOT NULL DEFAULT 'draft',
  current_offer numeric(18,2),
  currency char(3),
  max_rounds integer NOT NULL DEFAULT 3 CHECK (max_rounds BETWEEN 1 AND 10),
  round_count integer NOT NULL DEFAULT 0 CHECK (round_count >= 0),
  requires_human boolean NOT NULL DEFAULT false,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS demand_opportunities_rank_idx ON demand_opportunities(tenant_id, status, score DESC);
CREATE INDEX IF NOT EXISTS negotiation_sessions_state_idx ON negotiation_sessions(tenant_id, state, updated_at DESC);
