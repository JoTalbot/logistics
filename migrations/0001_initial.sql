CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE parties (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  legal_name text NOT NULL,
  country_code char(2) NOT NULL DEFAULT 'UA',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX parties_tenant_idx ON parties(tenant_id);

CREATE TABLE loads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  external_ref text,
  shipper_party_id uuid REFERENCES parties(id),
  cargo_type text NOT NULL,
  weight_kg integer NOT NULL CHECK (weight_kg > 0),
  offered_price numeric(14,2) NOT NULL CHECK (offered_price > 0),
  currency char(3) NOT NULL DEFAULT 'UAH',
  status text NOT NULL DEFAULT 'new',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX loads_tenant_status_idx ON loads(tenant_id, status);

CREATE TABLE load_stops (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  load_id uuid NOT NULL REFERENCES loads(id) ON DELETE CASCADE,
  sequence integer NOT NULL CHECK (sequence >= 0),
  kind text NOT NULL CHECK (kind IN ('pickup','delivery')),
  raw_address text NOT NULL,
  normalized_address text NOT NULL,
  latitude double precision,
  longitude double precision,
  geo_confidence numeric(5,4) NOT NULL DEFAULT 0 CHECK (geo_confidence BETWEEN 0 AND 1),
  geo_provenance text NOT NULL DEFAULT 'deterministic',
  earliest timestamptz,
  latest timestamptz,
  UNIQUE(load_id, sequence)
);

CREATE TABLE opportunities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  load_id uuid NOT NULL REFERENCES loads(id),
  score numeric(7,6) NOT NULL CHECK (score BETWEEN 0 AND 1),
  estimated_cost numeric(14,2) NOT NULL,
  estimated_margin numeric(14,2) NOT NULL,
  risk_adjusted_margin numeric(14,2) NOT NULL,
  status text NOT NULL DEFAULT 'candidate',
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX opportunities_tenant_score_idx ON opportunities(tenant_id, score DESC);

CREATE TABLE outbox_events (
  event_id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  event_type text NOT NULL,
  aggregate_type text NOT NULL,
  aggregate_id uuid NOT NULL,
  schema_version integer NOT NULL DEFAULT 1,
  occurred_at timestamptz NOT NULL,
  correlation_id uuid NOT NULL,
  causation_id uuid,
  payload jsonb NOT NULL,
  published_at timestamptz
);
CREATE INDEX outbox_pending_idx ON outbox_events(occurred_at) WHERE published_at IS NULL;

CREATE TABLE audit_log (
  audit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  actor_id uuid NOT NULL,
  action text NOT NULL,
  resource_type text NOT NULL,
  resource_id uuid NOT NULL,
  decision text NOT NULL,
  reason text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_tenant_time_idx ON audit_log(tenant_id, created_at DESC);
