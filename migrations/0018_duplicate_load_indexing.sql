-- Query-supporting indexes for tenant-scoped duplicate detection.
-- The duplicate signature remains computed from canonical stop data; these indexes
-- deliberately avoid declaring distinct loads duplicates at the database level.
CREATE INDEX IF NOT EXISTS loads_duplicate_candidates_idx
  ON loads (tenant_id, cargo_type, weight_kg, currency, created_at, id)
  WHERE status <> 'cancelled';

CREATE INDEX IF NOT EXISTS load_stops_duplicate_lookup_idx
  ON load_stops (load_id, sequence, kind, normalized_address);
