-- V42: scope remote-task idempotency to the target agent identity.
-- Tenant scope is insufficient for unscoped agents because PostgreSQL UNIQUE
-- indexes treat NULL tenant values as distinct and replay lookup could return
-- another agent's task. Each agent gets an independent idempotency namespace.
DROP INDEX IF EXISTS remote_tasks_tenant_idempotency_idx;

CREATE UNIQUE INDEX IF NOT EXISTS remote_tasks_agent_idempotency_idx
  ON remote_tasks(agent_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;
