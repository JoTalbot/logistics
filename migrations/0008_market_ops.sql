CREATE TABLE IF NOT EXISTS market_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  source text NOT NULL,
  external_ref text NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL,
  UNIQUE(tenant_id, source, external_ref)
);
CREATE INDEX IF NOT EXISTS market_observations_tenant_time_idx ON market_observations(tenant_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS carrier_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  party_id uuid NOT NULL REFERENCES parties(id),
  capacity_kg integer NOT NULL CHECK (capacity_kg > 0),
  home_country char(2) NOT NULL DEFAULT 'UA',
  risk_score numeric(6,5) NOT NULL DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 1),
  active boolean NOT NULL DEFAULT true,
  attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE(tenant_id, party_id)
);

CREATE TABLE IF NOT EXISTS opportunity_matches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  opportunity_id uuid NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
  carrier_id uuid NOT NULL REFERENCES carrier_profiles(id) ON DELETE CASCADE,
  score numeric(7,6) NOT NULL CHECK (score BETWEEN 0 AND 1),
  estimated_cost numeric(14,2) NOT NULL,
  estimated_margin numeric(14,2) NOT NULL,
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'candidate',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(opportunity_id, carrier_id)
);
CREATE INDEX IF NOT EXISTS opportunity_matches_score_idx ON opportunity_matches(opportunity_id, score DESC);

CREATE TABLE IF NOT EXISTS negotiation_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  opportunity_id uuid REFERENCES opportunities(id),
  counterparty_id uuid REFERENCES parties(id),
  state text NOT NULL DEFAULT 'draft',
  min_price numeric(14,2),
  target_price numeric(14,2),
  max_rounds integer NOT NULL DEFAULT 3 CHECK (max_rounds BETWEEN 1 AND 20),
  rounds integer NOT NULL DEFAULT 0 CHECK (rounds >= 0),
  risk_level text NOT NULL DEFAULT 'normal',
  requires_human boolean NOT NULL DEFAULT true,
  audit jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS negotiation_sessions_tenant_state_idx ON negotiation_sessions(tenant_id, state);

CREATE TABLE IF NOT EXISTS publication_intents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  load_id uuid NOT NULL REFERENCES loads(id),
  provider text NOT NULL,
  idempotency_key text NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'prepared',
  attempts integer NOT NULL DEFAULT 0,
  last_error text,
  next_attempt_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS publication_intents_ready_idx ON publication_intents(next_attempt_at) WHERE status IN ('prepared','retry');
