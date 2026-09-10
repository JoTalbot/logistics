CREATE TABLE telegram_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  source text NOT NULL,
  enabled boolean NOT NULL DEFAULT true,
  last_message_id bigint NOT NULL DEFAULT 0,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, source)
);
CREATE INDEX telegram_sources_tenant_enabled_idx ON telegram_sources(tenant_id, enabled);

CREATE TABLE telegram_source_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  source text NOT NULL,
  message_id bigint NOT NULL,
  message_url text,
  published_at timestamptz NOT NULL,
  raw_text text NOT NULL DEFAULT '',
  has_media boolean NOT NULL DEFAULT false,
  collected_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, source, message_id)
);
CREATE INDEX telegram_source_messages_tenant_time_idx
  ON telegram_source_messages(tenant_id, published_at DESC);

CREATE TABLE telegram_parsed_load_ads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  source_message_id uuid NOT NULL REFERENCES telegram_source_messages(id) ON DELETE CASCADE,
  origin text,
  destination text,
  cargo_type text,
  vehicle_type text,
  weight_kg integer CHECK (weight_kg IS NULL OR weight_kg > 0),
  volume_m3 numeric(12,3) CHECK (volume_m3 IS NULL OR volume_m3 > 0),
  price numeric(14,2) CHECK (price IS NULL OR price > 0),
  currency char(3),
  loading_date_text text,
  phone_numbers jsonb NOT NULL DEFAULT '[]'::jsonb,
  confidence numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  parser_version text NOT NULL,
  parsed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_message_id)
);
CREATE INDEX telegram_parsed_ads_tenant_confidence_idx
  ON telegram_parsed_load_ads(tenant_id, confidence DESC, parsed_at DESC);
