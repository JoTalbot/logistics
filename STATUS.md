# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V21 — controlled autonomy foundation
STATUS: v21_controlled_autonomy_ci_pending
AGENT: logistics-commercial-batch-v21
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Deterministic simulation/shadow autonomy gating, auditable approval tiers and preparation for controlled rollout. No autonomous external commitment or outreach is enabled.

## V21 completed implementation

- Added `backend/logistics/autonomy_policy.py` with deterministic approval tiers: `AUTO`, `REVIEW`, `HIGH_RISK`, `BLOCK`.
- Default confidence bands are configurable: `>=0.90` AUTO, `0.70–0.89` REVIEW, `<0.70` HIGH_RISK.
- Unauthorized actions always resolve to BLOCK.
- Critical-risk actions always resolve to BLOCK regardless of confidence.
- Explicit human-approval requirements resolve to REVIEW even at high confidence.
- Invalid confidence and threshold configurations fail closed.
- Added `tests/test_autonomy_policy.py` covering confidence bands, hard blocks, human-approval override and bounds.
- Added `docs/V21_CONTROLLED_AUTONOMY.md` defining the implementation boundary and next gates.

## Safety boundary

The V21 policy gate only classifies an intended action. It does not send messages, publish listings, negotiate, sign contracts, move money, call external providers or mutate business state.

Provider permissions, legal authorization, tenant policy and operational controls remain independent gates. Model confidence is never treated as authorization.

## V20 verified technical baseline

- Corrected hosted CI Run #258 `34544573319` passed successfully on commit `e5e96527abf23d4b75c94e2c9f7d39f607ad9f23`.
- CI passed dependency consistency, pip-audit, SQL migrations, full unit/integration tests, V20 commercial baseline replay, hardened Compose validation, release smoke checks and hardened API image build.

## V20 production/business readiness remaining outside repository/CI

1. Actual backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. Previous live smoke returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**.

## V21 next gates

1. Integrate the classifier with simulation/shadow decision records.
2. Persist policy version and classification reason alongside auditable decisions.
3. Add replay metrics comparing policy classifications with historical outcomes.
4. Add operator-visible exception queues for REVIEW, HIGH_RISK and BLOCK decisions.
5. Keep real external side effects disabled until provider and authorization gates are independently verified.

## Verification

- V20 CI verification: **COMPLETE** via Run #258 `34544573319`.
- V21 implementation is committed; a fresh CI run is required to verify the new module and tests.
- Lardi smoke Run `34519177888` remains blocked by provider-side Cloudflare/browser-signature policy.
- No retry loop, browser automation or anti-bot bypass is permitted.

## Release boundary

**Production release is NOT declared.** Repository hardening and V20 CI gates are verified. Production requires target-infrastructure rehearsal, provider/legal verification and explicit authorization for every external side effect.

## Handoff

DONE: V17 reliability/replay, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening, V20 KPI/replay/Compose implementation and corrected CI verification, V21 deterministic autonomy policy foundation.
IN_PROGRESS: V21 CI verification and controlled-autonomy integration.
PENDING: V21 shadow decision persistence/replay/exception queue; target infrastructure rehearsal; Lardi provider access/mapping; contact adapters; external publication permissions.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the current blocked state.
OPEN_ISSUES: V21 CI verification, provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions and production-infrastructure rehearsal.
