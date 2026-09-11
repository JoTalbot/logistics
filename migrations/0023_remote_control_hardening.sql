-- V22: bounded remote execution hardening. Legacy rows may remain tenant-less;
-- all newly associated agents/tasks should carry tenant_id from the API contract.
ALTER TABLE remote_agents
  ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES tenants(id);

ALTER TABLE remote_tasks
  ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES tenants(id);

ALTER TABLE remote_tasks
  ADD COLUMN IF NOT EXISTS idempotency_key text;

ALTER TABLE remote_tasks
  ADD COLUMN IF NOT EXISTS lease_expires_at timestamptz;

ALTER TABLE remote_tasks
  ADD COLUMN IF NOT EXISTS heartbeat_at timestamptz;

CREATE UNIQUE INDEX IF NOT EXISTS remote_tasks_tenant_idempotency_idx
  ON remote_tasks(tenant_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS remote_tasks_lease_idx
  ON remote_tasks(agent_id, status, lease_expires_at);

CREATE INDEX IF NOT EXISTS remote_agents_tenant_idx
  ON remote_agents(tenant_id, name);
