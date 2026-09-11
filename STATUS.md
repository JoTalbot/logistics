# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V21 — controlled autonomy integration
STATUS: v21_authenticated_exception_queue_ci_pending
AGENT: logistics-commercial-batch-v21
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Deterministic simulation/shadow autonomy gating, durable policy metadata, authenticated exception queue and replay metrics. No autonomous external commitment or outreach is enabled.

## V21 completed implementation

- Added `backend/logistics/autonomy_policy.py` with deterministic approval tiers: `AUTO`, `REVIEW`, `HIGH_RISK`, `BLOCK`.
- Added `backend/logistics/shadow_decisions.py` with explicit `SIMULATION`/`SHADOW` decision records.
- Shadow records carry policy version, classification reason, tenant, action, confidence and timestamp without external side effects.
- Added `backend/logistics/policy_replay.py` for deterministic historical replay metrics, including tier counts and AUTO failure rate.
- Added `migrations/0022_autonomy_decisions.sql` for durable tenant-scoped simulation/shadow decision records with correlation IDs and idempotent `(tenant_id, decision_id)` identity.
- Added `backend/logistics/autonomy_store.py` to connect policy classification to durable persistence and provide an oldest-first exception queue for `REVIEW`, `HIGH_RISK` and `BLOCK` records.
- Added authenticated `GET /api/v1/review/autonomy-exceptions` to expose the exception queue without weakening the existing operator-token boundary.
- Added tests covering policy-to-persistence integration, tenant isolation, idempotency SQL, exception queue bounds and authenticated API access.
- Updated `docs/V21_CONTROLLED_AUTONOMY.md` with the authenticated queue gate.

## Safety boundary

The V21 policy, shadow and persistence layers only classify intended actions, persist auditable decision metadata and calculate replay metrics. They do not send messages, publish listings, negotiate, sign contracts, move money, call external providers or mutate business state.

Provider permissions, legal authorization, tenant policy and operational controls remain independent gates. Model confidence is never treated as authorization.

## V20 verified technical baseline

- Corrected hosted CI Run #258 `34544573319` passed successfully on commit `e5e96527abf23d4b75c94e2c9f7d39f607ad9f23`.
- CI passed dependency consistency, pip-audit, SQL migrations, full unit/integration tests, V20 commercial baseline replay, hardened Compose validation, release smoke checks and hardened API image build.

## V20 production/business readiness remaining outside repository/CI

1. Actual backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.

## V21 gates

1. Shadow/simulation classifier integration: **IMPLEMENTED**.
2. Policy version and classification reason: **IMPLEMENTED IN SHADOW RECORD**.
3. Durable shadow decision persistence: **IMPLEMENTED** via migration `0022_autonomy_decisions.sql` and `autonomy_store.py`.
4. Authenticated exception queue API for REVIEW/HIGH_RISK/BLOCK: **IMPLEMENTED** at `/api/v1/review/autonomy-exceptions`.
5. Replay metrics comparing policy classifications with historical outcomes: **IMPLEMENTED AS SIDE-EFFECT-FREE REPLAY MODULE**; durable historical aggregation remains pending.
6. Real external side effects: **DISABLED** until provider and authorization gates are independently verified.

## Verification

- V20 CI verification: **COMPLETE** via Run #258 `34544573319`.
- V21 durable persistence, exception API and tests are committed; a fresh CI run is required to verify the current batch.
- Lardi smoke Run `34519177888` remains blocked by provider-side Cloudflare/browser-signature policy.
- No retry loop, browser automation or anti-bot bypass is permitted.

## Release boundary

**Production release is NOT declared.** Repository hardening and V20 CI gates are verified. Production requires target-infrastructure rehearsal, provider/legal verification and explicit authorization for every external side effect.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and corrected CI verification, V21 deterministic autonomy policy, shadow/replay modules, durable decision persistence and authenticated exception queue.
IN_PROGRESS: V21 CI verification and durable historical outcome aggregation.
PENDING: durable historical outcome aggregation; target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the current blocked state.
OPEN_ISSUES: V21 CI verification, historical outcome evidence, provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions and production-infrastructure rehearsal.
