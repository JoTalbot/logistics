# V22 — Bounded Remote Control Plane

## Goal

Provide an auditable control plane for remote logistics agents without turning the system into an unrestricted remote shell.

## Implemented

- Remote agents and tasks are persisted in PostgreSQL.
- Agent heartbeat supports optional tenant association and rejects explicit tenant mismatches.
- New task records inherit the agent tenant when available and reject an explicit mismatch.
- Task creation supports idempotency keys scoped by tenant.
- Only a narrow read-only/diagnostic command allowlist is classified `AUTO`.
- Unknown commands are `REVIEW`; explicitly destructive patterns are `BLOCK`.
- Agents can only receive queued `AUTO` tasks.
- Running tasks receive a 120-second lease and heartbeat renewal through event submission.
- Expired leases return tasks to the queue instead of remaining permanently stuck in `running`.
- Completion is accepted only while the task lease is active.
- Operator cancellation prevents queued execution and clears the active lease.
- Operator and agent credentials remain separate secrets.
- The API container receives the control-plane secrets through the deployment contract.

## API surface

- `GET /api/v1/control/agents` — operator-only agent inventory.
- `POST /api/v1/control/agents/heartbeat` — agent heartbeat.
- `POST /api/v1/control/tasks` — operator-only task creation.
- `GET /api/v1/control/agents/{agent_id}/tasks/next` — agent-only AUTO task claim.
- `POST /api/v1/control/tasks/{task_id}/events` — agent task telemetry and lease renewal.
- `POST /api/v1/control/tasks/{task_id}/complete` — agent completion while leased.
- `POST /api/v1/control/tasks/{task_id}/cancel` — operator cancellation.
- `GET /api/v1/control/tasks` and `/events` — operator-only inspection.

## Safety boundary

V22 is a controlled execution transport, not an autonomy grant. It does not authorize publication, customer outreach, negotiation, contract signing, financial transactions, provider bypasses or other external business commitments.

The command classifier is intentionally conservative. `AUTO` is a small explicit allowlist, not a prediction. Everything outside that allowlist requires review, while known destructive patterns are blocked.

A remote agent token is not an operator token. Tenant metadata is carried where available, and idempotency prevents accidental duplicate task creation for the same tenant/key.

## Migration

`migrations/0023_remote_control_hardening.sql` adds tenant metadata, idempotency and lease fields to the existing V22 control-plane schema. Legacy rows can remain tenant-less; newly created records should use tenant association whenever the caller provides it.

## Verification

Tests cover authentication, heartbeat metadata, safe lifecycle, conservative command classification and idempotent task creation. CI must also pass SQL migrations, dependency audit, full unit/integration tests, Compose validation, release smoke and API image build.

## Exit criterion

A remote agent can be observed, receive only explicitly safe AUTO work, report progress, complete within a lease and be cancelled by an operator, with durable task history and no automatic path to external logistics commitments.
