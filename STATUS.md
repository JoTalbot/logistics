# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V22 — bounded remote control plane
STATUS: v22_remote_control_hardening_ci_pending
AGENT: logistics-commercial-batch-v22
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Auditable remote agent/task control with conservative command gating, tenant metadata, idempotency and lease-based execution. No autonomous external commitment or outreach is enabled.

## V22 completed implementation

- Hardened `backend/logistics/remote_control.py` so only a narrow read-only/diagnostic allowlist is eligible for `AUTO` dispatch.
- Unknown commands require `REVIEW`; explicitly destructive command patterns are `BLOCK`.
- Agent and operator credentials remain separate.
- Added optional tenant association to agents/tasks and explicit tenant mismatch checks.
- Added tenant-scoped idempotency keys for task creation.
- Added 120-second task leases with heartbeat renewal and expiry recovery.
- Completion is accepted only while a task lease remains active.
- Added `migrations/0023_remote_control_hardening.sql` and wired it into Compose.
- Added V22 deployment secret contract for `REMOTE_AGENT_TOKEN` and `CONTROL_PLANE_OPERATOR_TOKEN`.
- Added integration coverage for authentication, safe lifecycle, conservative command gating and idempotent task creation.
- Added `docs/V22_REMOTE_CONTROL_PLANE.md`.

## V22 safety boundary

The control plane is an execution transport, not an authorization grant. It does not publish listings, contact customers, negotiate, sign contracts, move money, call providers or bypass provider controls. Only explicitly allowlisted diagnostics can be dispatched automatically. All other commands require review or are blocked.

## V21 verified baseline

- Durable autonomy decisions, authenticated exception queue and historical policy replay are implemented.
- Historical replay remains read-only and conservative: missing delivery telemetry is `UNKNOWN`.
- Model confidence is never treated as authorization.

## V20 verified technical baseline

- Corrected hosted CI Run #258 `34544573319` passed successfully.
- Dependency consistency, pip-audit, SQL migrations, full unit/integration tests, V20 commercial replay, hardened Compose validation, release smoke and hardened API image build passed.

## Production gates remaining outside repository/CI

1. Backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.

## Verification

- V22 changes are committed; fresh CI verification is pending.
- No retry loop, browser automation or anti-bot bypass is permitted.
- Production release is **NOT declared**.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence, authenticated exception queue and historical aggregation, V22 bounded remote control hardening.
IN_PROGRESS: V22 CI verification.
PENDING: target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions; broader remote-agent operational rollout only after security review.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the current code batch beyond configuring the new control-plane secrets in an actual deployment.
OPEN_ISSUES: V22 CI verification, provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions and production-infrastructure rehearsal.
