ALTER TABLE customer_prospects
  ADD COLUMN IF NOT EXISTS suppression_reason text,
  ADD COLUMN IF NOT EXISTS suppressed_at timestamptz,
  ADD COLUMN IF NOT EXISTS identity_key text;

CREATE INDEX IF NOT EXISTS idx_customer_prospects_identity
  ON customer_prospects (tenant_id, identity_key);

CREATE TABLE IF NOT EXISTS prospect_observations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    prospect_id uuid NOT NULL REFERENCES customer_prospects(id) ON DELETE CASCADE,
    source_name text NOT NULL,
    source_url text NOT NULL,
    captured_at timestamptz NOT NULL,
    payload jsonb NOT NULL,
    observation_key text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, observation_key)
);

CREATE INDEX IF NOT EXISTS idx_prospect_observations_prospect
  ON prospect_observations (tenant_id, prospect_id, captured_at DESC);
