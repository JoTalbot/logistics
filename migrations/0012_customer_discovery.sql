-- Durable, tenant-scoped customer discovery records.
CREATE TABLE IF NOT EXISTS customer_prospects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  organization_name text NOT NULL,
  country text,
  city text,
  website text,
  contact text,
  signal text,
  source_name text NOT NULL,
  source_url text NOT NULL,
  captured_at timestamptz NOT NULL,
  source_permitted boolean NOT NULL DEFAULT false,
  suppressed boolean NOT NULL DEFAULT false,
  qualification_score numeric(7,6),
  qualification_tier text,
  qualification_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  status text NOT NULL DEFAULT 'candidate',
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (length(trim(organization_name)) > 0),
  CHECK (source_url ~* '^https?://'),
  CHECK (qualification_score IS NULL OR qualification_score BETWEEN 0 AND 1),
  CHECK (qualification_tier IS NULL OR qualification_tier IN ('A','B','C')),
  CHECK (status IN ('candidate','qualified','contacted','customer','suppressed')),
  UNIQUE (tenant_id, source_name, source_url, organization_name)
);

CREATE INDEX IF NOT EXISTS customer_prospects_tenant_status_idx
  ON customer_prospects(tenant_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS customer_prospects_qualification_idx
  ON customer_prospects(tenant_id, qualification_score DESC)
  WHERE qualification_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS customer_prospects_freshness_idx
  ON customer_prospects(tenant_id, last_seen_at DESC);
