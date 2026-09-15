-- V41: support explicit operator-driven remote-agent credential revocation.
-- Keep the revocation timestamp separate from the credential hash so an
-- invalidated credential is both unusable and auditable.
ALTER TABLE remote_agents
  ADD COLUMN IF NOT EXISTS credential_revoked_at timestamptz;
