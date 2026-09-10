# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V20 — production/business readiness
STATUS: v20_production_business_readiness
AGENT: logistics-commercial-batch-v20
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Production hardening, operational readiness, measurable business execution and safe transition from internal commercial pipeline to controlled real-world use. No autonomous external commitment or outreach is enabled.

## V18 completed

- Added `/health` liveness and `/ready` database readiness probes.
- Readiness uses a bounded three-second PostgreSQL connection timeout and returns HTTP 503 when configuration or database connectivity is unavailable.
- Added API container healthcheck against `/ready` and a 30-second graceful shutdown window in Compose.
- Added missing migrations `0020_commercial_priority.sql` and `0021_outbox_delivery_telemetry.sql` to the PostgreSQL bootstrap mounts so a fresh Compose database receives the complete schema.
- Added unit coverage for readiness success, database failure, missing configuration and tenant-scoped review metrics.
- Added PostgreSQL outbox recovery/replay integration coverage for durable delivery telemetry.
- Restored the authenticated `/api/v1/review/audit/report` endpoint with tenant-scoped decision totals, daily trend and queue-age reporting plus bounds validation.
- Hosted CI Run #221 `34535526756` on commit `a0b002f...` passed: PostgreSQL migrations and the complete unit/integration test job succeeded.

## V19 completed

- Added `docs/SECURITY_RELEASE_GATE.md` covering the nine requested security/compliance/release-gate areas, including tenant isolation, secrets, startup/readiness, migrations, smoke checks, provider contracts, contact/publication gates, threat/dependency review and final release criteria.
- Added `docs/THREAT_MODEL.md` with trust boundaries, protected assets, abuse cases, mitigations and residual risks.
- Added `scripts/release_smoke.py` with fail-closed local checks for liveness, readiness failure, operator authentication and tenant-scoped audit reporting. It uses only fake/local dependencies and cannot publish or contact externally.
- Extended CI with `pip check`, `pip-audit`, SQL migration execution, full tests and the release smoke suite.
- Upgraded pytest to the patched `>=9.0.3,<10` line after `pip-audit` identified the vulnerable pytest 8.4.2 dependency.
- Fixed the release smoke cursor fixtures; hosted CI Run #231 `34539152470` passed all stages: dependency audit, migrations, tests and release smoke.
- Reconciled provider policy: Lardi remains read-only; unverified provider fields cannot become canonical data; no browser bypass or autonomous publication/outreach is enabled.
- Production Compose defaults remain explicitly documented as development defaults; production must replace credentials and apply network restrictions.

## Reliability boundary

The outbox event UUID remains the canonical idempotency identity. A retry/replay creates a new attempt record, not a new business event. This preserves safe recovery semantics while making repeated delivery observable before any stronger database identity constraints are considered.

## Commercial chain

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → recurring demand → deterministic priority → operator queue → SLA/health visibility → observable delivery/recovery`

V14 priority formula:

`65% opportunity score + 20% carrier availability signal + 15% recurring-demand signal`

The commercial pipeline remains deterministic and explainable. It does not publish, contact or commit funds.

## V20 production/business readiness

V20 follows the established strategy: first make the existing commercial chain safe and measurable in production-like operation, then enable only those external actions whose provider, legal and operational contracts are verified.

Completed V20 batch work:

1. Production configuration contract: `.env.example` documents required database/operator configuration and keeps provider secrets runtime-only.
2. Deployment hardening: API runs as non-root, Compose uses read-only API/scheduler filesystems, drops Linux capabilities, enables `no-new-privileges`, limits resources, binds API locally by default and does not expose PostgreSQL publicly.
3. Operational runbook: `docs/PRODUCTION_RUNBOOK.md` covers preflight, startup, migrations, backup/restore, scheduler health, outbox recovery, degraded mode, incidents, rollback and release gate.
4. Business KPI foundation: `backend/logistics/business_kpi.py` provides deterministic tenant-scoped operational/commercial KPI aggregation with test coverage.
5. Commercial replay/evaluation foundation: `backend/logistics/commercial_replay.py` provides side-effect-free historical/synthetic evaluation with test coverage.
6. Provider readiness matrix: `docs/PROVIDER_READINESS.md` records Lardi as blocked/read-only and DELLA as unverified, with explicit evidence and required verification fields.
7. Data governance: `docs/DATA_GOVERNANCE.md` documents provenance, tenant isolation, PII minimization, retention, secrets and auditability.
8. CI release validation: `.github/workflows/ci.yml` now builds the hardened API Docker image after tests and release smoke checks.

Remaining V20 work:

1. Expose the KPI snapshot through the authenticated review API after final schema/API review.
2. Add production-like KPI baseline and replay fixtures using representative non-sensitive data.
3. Perform an actual backup/restore rehearsal in the target infrastructure.
4. Verify the hardened Compose stack end-to-end in the target deployment environment.
5. Complete provider-side Lardi access/mapping verification and any required contractual review.
6. Recheck the release candidate after the new CI run completes.

V20 exit criterion: the system can run the existing commercial pipeline continuously in a production-like environment with measurable economics, observable failures/recovery and documented rollback, while every external side effect remains explicitly authorized and auditable.

## Verification

- V19 hosted CI Run #231 `34539152470` passed on commit `0cf8eecd1c5d4f9196b8a57b4f90b1610511b80c`: dependency consistency, `pip-audit`, PostgreSQL migrations, unit/integration tests and local release smoke all succeeded.
- V20 CI is automatically triggered by each new main-branch commit and now includes hardened API image build validation.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical provider mapping remains blocked until a verified response is obtained. No field semantics are inferred from guessed JSON names.

## Release boundary

V19 technical gate is green. V20 production release is not declared merely because CI is green. External/provider/legal conditions, production configuration, operational rehearsal and explicit authorization remain separate release conditions.

## Security / compliance

Credentials remain runtime secrets. Review APIs require `REVIEW_OPERATOR_TOKEN`. No autonomous outreach, unsupported scraping, anti-bot bypass or external publication is enabled.

## Handoff

DONE: V17 reliability/replay foundation, V18 integration/deployment hardening and V19 security/compliance/release-gate hardening with green hosted CI.
IN_PROGRESS: V20 production/business readiness.
PENDING: provider-side Lardi access/mapping, duplicate identity evidence, contact adapters, external publication permissions, target-infrastructure restore rehearsal and final KPI API exposure.
REQUIRED HUMAN ACTION: Lardi provider/support action before another live smoke. No repository-secret change is required.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters, external publication permissions and production-infrastructure rehearsal.
