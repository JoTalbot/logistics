CREATE TABLE IF NOT EXISTS remote_agents (
  id uuid PRIMARY KEY,
  name text NOT NULL UNIQUE,
  last_seen timestamptz,
  status text NOT NULL DEFAULT 'offline',
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS remote_tasks (
  id uuid PRIMARY KEY,
  agent_id uuid NOT NULL REFERENCES remote_agents(id) ON DELETE CASCADE,
  command text NOT NULL,
  cwd text NOT NULL DEFAULT '/opt/logistics',
  status text NOT NULL DEFAULT 'queued',
  approval text NOT NULL DEFAULT 'AUTO',
  requested_by text NOT NULL,
  cancel_requested boolean NOT NULL DEFAULT false,
  returncode integer,
  stdout text NOT NULL DEFAULT '',
  stderr text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS remote_task_events (
  id bigserial PRIMARY KEY,
  task_id uuid NOT NULL REFERENCES remote_tasks(id) ON DELETE CASCADE,
  stream text NOT NULL,
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_remote_tasks_agent_status ON remote_tasks(agent_id,status,created_at);
CREATE INDEX IF NOT EXISTS idx_remote_task_events_task ON remote_task_events(task_id,id);
