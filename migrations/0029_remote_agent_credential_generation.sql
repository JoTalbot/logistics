ALTER TABLE remote_agents
    ADD COLUMN IF NOT EXISTS credential_generation bigint NOT NULL DEFAULT 1;

ALTER TABLE remote_tasks
    ADD COLUMN IF NOT EXISTS lease_credential_generation bigint;
