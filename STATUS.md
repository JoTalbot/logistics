# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V20 — production/business readiness
STATUS: v20_production_business_readiness
AGENT: logistics-commercial-batch-v20
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Production hardening, operational readiness, measurable business execution and safe transition from internal commercial pipeline to controlled real-world use. No autonomous external commitment or outreach is enabled.

## V20 verified technical baseline

- Hosted CI Run #249 `34543221498` passed all stages, including the hardened API Docker image build.
- Hosted CI Run #251 `34543589591` passed all stages, including migrations, tests, release smoke and hardened API image build.
- Hosted CI Run #252 `34543604962` passed all stages, including migrations, tests, release smoke and hardened API image build.
- Added a deterministic synthetic commercial baseline at `fixtures/commercial/v20_baseline.json`; it contains no real customer, provider, contact or financial commitment data.
- Added `scripts/v20_baseline.py` to execute the replay baseline without external side effects.
- Added regression tests for the five-case baseline: 2 profitable, 2 loss and 1 unknown case, with a 0.4 profitable rate.
- Baseline prices are parsed as `Decimal` before commercial replay evaluation.
- The authenticated `/api/v1/review/business-kpis` endpoint is present and delegates to the tenant-scoped deterministic KPI snapshot layer.
- CI now validates both the V20 replay runner and the hardened Docker Compose configuration contract with non-production CI credentials.

## V18 completed

- Added `/health` liveness and `/ready` database readiness probes.
- Readiness uses a bounded three-second PostgreSQL connection timeout and returns HTTP 503 when configuration or database connectivity is unavailable.
- Added API container healthcheck against `/ready` and a 30-second graceful shutdown window in Compose.
- Added missing migrations `0020_commercial_priority.sql` and `0021_outbox_delivery_telemetry.sql` to the PostgreSQL bootstrap mounts so a fresh Compose database receives the complete schema.
- Added unit coverage for readiness success, database failure, missing configuration and tenant-scoped review metrics.
- Added PostgreSQL outbox recovery/replay integration coverage for durable delivery telemetry.
- Restored the authenticated `/api/v1/review/audit/report` endpoint with tenant-scoped decision totals, daily trend and queue-age reporting plus bounds validation.

## V19 completed

- Added `docs/SECURITY_RELEASE_GATE.md` covering security/compliance/release-gate areas, including tenant isolation, secrets, startup/readiness, migrations, smoke checks, provider contracts, contact/publication gates, threat/dependency review and final release criteria.
- Added `docs/THREAT_MODEL.md` with trust boundaries, protected assets, abuse cases, mitigations and residual risks.
- Added `scripts/release_smoke.py` with fail-closed local checks for liveness, readiness failure, operator authentication and tenant-scoped audit reporting. It uses only fake/local dependencies and cannot publish or contact externally.
- Extended CI with `pip check`, `pip-audit`, SQL migration execution, full tests and the release smoke suite.
- Upgraded pytest to the patched `>=9.0.3,<10` line after dependency audit review.
- Reconciled provider policy: Lardi remains read-only; unverified provider fields cannot become canonical data; no browser bypass or autonomous publication/outreach is enabled.

## Reliability boundary

The outbox event UUID remains the canonical idempotency identity. A retry/replay creates a new attempt record, not a new business event. This preserves safe recovery semantics while making repeated delivery observable before any stronger database identity constraints are considered.

## Commercial chain

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → recurring demand → deterministic priority → operator queue → SLA/health visibility → observable delivery/recovery`

V14 priority formula:

`65% opportunity score + 20% carrier availability signal + 15% recurring-demand signal`

The commercial pipeline remains deterministic and explainable. It does not publish, contact or commit funds.

## V20 production/business readiness

V20 follows the established strategy: first make the existing commercial chain safe and measurable in production-like operation, then enable only those external actions whose provider, legal and operational contracts are verified.

### Completed

1. Production configuration contract: `.env.example` documents required database/operator configuration and keeps provider secrets runtime-only.
2. Deployment hardening: API runs as non-root; Compose uses read-only API/scheduler filesystems, drops Linux capabilities, enables `no-new-privileges`, limits resources, binds API locally by default and does not expose PostgreSQL publicly.
3. Operational runbook: `docs/PRODUCTION_RUNBOOK.md` covers preflight, startup, migrations, backup/restore, scheduler health, outbox recovery, degraded mode, incidents, rollback and release gate.
4. Business KPI foundation: `backend/logistics/business_kpi.py` provides deterministic tenant-scoped operational/commercial KPI aggregation with test coverage.
5. Authenticated KPI review endpoint: `/api/v1/review/business-kpis` exposes the tenant-scoped snapshot behind operator authentication.
6. Commercial replay/evaluation foundation: `backend/logistics/commercial_replay.py` provides side-effect-free historical/synthetic evaluation with test coverage.
7. Synthetic V20 baseline: fixture, replay runner and regression tests provide a stable non-sensitive commercial control point.
8. Provider readiness matrix: `docs/PROVIDER_READINESS.md` records Lardi as blocked/read-only and DELLA as unverified, with explicit evidence and required verification fields.
9. Data governance: `docs/DATA_GOVERNANCE.md` documents provenance, tenant isolation, PII minimization, retention, secrets and auditability.
10. CI release validation: `.github/workflows/ci.yml` builds the hardened API image and validates the V20 replay and Compose contract.

### Cannot be completed from repository/CI alone

1. Actual backup/restore rehearsal in target infrastructure: **PENDING TARGET INFRASTRUCTURE**. The repository documents the procedure, but no target production database/storage environment is connected to this workflow.
2. Hardened Compose end-to-end rehearsal in target deployment environment: **PENDING TARGET INFRASTRUCTURE**. CI validates the Compose configuration contract and builds the API image, but this is not equivalent to a production deployment rehearsal.
3. Lardi access/mapping verification: **BLOCKED BY PROVIDER**. The previous live smoke reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`. No bypass or browser automation is permitted.
4. External publication permissions and contact adapters: **PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION**. No autonomous publication, unsolicited outreach, negotiation or financial commitment is enabled.

## Verification

- Latest fully verified CI baseline before this status-only commit: Run #252 `34543604962`, success on commit `11467f2e903247461db7fa65cf105efea2d3f1c3`; all test, audit, migration, release-smoke and hardened-image stages passed.
- CI now additionally runs `python scripts/v20_baseline.py` and `docker compose config --quiet` using CI-only non-production credentials.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical provider mapping remains blocked until a verified response is obtained. No field semantics are inferred from guessed JSON names.

## Release boundary

**V20 production release is NOT declared.** The repository/CI technical gate is green through Run #252, but production release additionally requires target-infrastructure backup/restore rehearsal, deployment rehearsal, provider/legal verification and explicit authorization for every external side effect.

## Security / compliance

Credentials remain runtime secrets. Review APIs require `REVIEW_OPERATOR_TOKEN`. No autonomous outreach, unsupported scraping, anti-bot bypass or external publication is enabled.

## Handoff

DONE: V17 reliability/replay foundation, V18 integration/deployment hardening, V19 security/compliance/release-gate hardening and V20 technical KPI/replay/Compose validation.
IN_PROGRESS: V20 production/business readiness.
PENDING: target-infrastructure backup/restore rehearsal, target deployment rehearsal, provider-side Lardi access/mapping, duplicate identity evidence, contact adapters and external publication permissions.
REQUIRED HUMAN ACTION: target infrastructure rehearsal plus Lardi provider/support action before another live smoke. No repository-secret change is required for the current blocked state.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions and production-infrastructure rehearsal.
