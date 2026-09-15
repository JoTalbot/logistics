-- V41: bind remote control operations to per-agent credentials.
-- Plaintext credentials are never persisted. Existing agents are bootstrapped
-- with the global enrollment credential once, then receive a new per-agent
-- credential that the agent uses for heartbeat/task operations.
ALTER TABLE remote_agents
  ADD COLUMN IF NOT EXISTS credential_hash text;

ALTER TABLE remote_agents
  ADD COLUMN IF NOT EXISTS credential_created_at timestamptz;

CREATE INDEX IF NOT EXISTS remote_agents_credential_idx
  ON remote_agents(credential_hash)
  WHERE credential_hash IS NOT NULL;
