-- Persist explainable market/economic recommendation outputs on canonical opportunities.
ALTER TABLE opportunities
  ADD COLUMN IF NOT EXISTS recommended_price numeric(14,2),
  ADD COLUMN IF NOT EXISTS market_median_price numeric(14,2),
  ADD COLUMN IF NOT EXISTS recommendation_reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS recommendation_updated_at timestamptz;

CREATE INDEX IF NOT EXISTS opportunities_recommendation_idx
  ON opportunities(tenant_id, recommendation_updated_at DESC)
  WHERE recommendation_updated_at IS NOT NULL;
