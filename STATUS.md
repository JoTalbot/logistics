# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: V19 — security, compliance and release-gate hardening
STATUS: v19_release_gate_hardening
AGENT: logistics-commercial-batch-v19
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-11
UPDATED: 2026-09-11
SCOPE: Historical market observations, explainable opportunity economics, authenticated human review and provenance-first customer discovery. No autonomous external commitment or outreach is enabled.

## V18 completed

- Added `/health` liveness and `/ready` database readiness probes.
- Readiness uses a bounded three-second PostgreSQL connection timeout and returns HTTP 503 when configuration or database connectivity is unavailable.
- Added API container healthcheck against `/ready` and a 30-second graceful shutdown window in Compose.
- Added missing migrations `0020_commercial_priority.sql` and `0021_outbox_delivery_telemetry.sql` to the PostgreSQL bootstrap mounts so a fresh Compose database receives the complete schema.
- Added unit coverage for readiness success, database failure, missing configuration and tenant-scoped review metrics.
- Added PostgreSQL outbox recovery/replay integration coverage for durable delivery telemetry.
- Restored the authenticated `/api/v1/review/audit/report` endpoint with tenant-scoped decision totals, daily trend and queue-age reporting plus bounds validation.
- Hosted CI Run #221 `34535526756` on commit `a0b002f...` passed: PostgreSQL migrations and the complete unit/integration test job succeeded.

## V19 batch implemented

- Added `docs/SECURITY_RELEASE_GATE.md` covering the nine requested security/compliance/release-gate areas, including tenant isolation, secrets, startup/readiness, migrations, smoke checks, provider contracts, contact/publication gates, threat/dependency review and final release criteria.
- Added `docs/THREAT_MODEL.md` with trust boundaries, protected assets, abuse cases, mitigations and residual risks.
- Added `scripts/release_smoke.py` with fail-closed local checks for liveness, readiness failure, operator authentication and tenant-scoped audit reporting. It uses only fake/local dependencies and cannot publish or contact externally.
- Extended CI with `pip check`, `pip-audit`, SQL migration execution, full tests and the release smoke suite.
- Reconciled provider policy: Lardi remains read-only; unverified provider fields cannot become canonical data; no browser bypass or autonomous publication/outreach is enabled.
- Production Compose defaults remain explicitly documented as development defaults; production must replace credentials and apply network restrictions.

## Reliability boundary

The outbox event UUID remains the canonical idempotency identity. A retry/replay creates a new attempt record, not a new business event. This preserves safe recovery semantics while making repeated delivery observable before any stronger database identity constraints are considered.

## Commercial chain

`Telegram → canonical Load → normalize → score → Opportunity → pricing/matching → recurring demand → deterministic priority → operator queue → SLA/health visibility → observable delivery/recovery`

V14 priority formula:

`65% opportunity score + 20% carrier availability signal + 15% recurring-demand signal`

The commercial pipeline remains deterministic and explainable. It does not publish, contact or commit funds.

## Verification

- V18 hosted CI Run #221 `34535526756` passed on PostgreSQL 17; migration, unit and integration test steps all succeeded.
- V19 CI is currently running against the latest release-gate hardening changes. It must finish green before V19 can be declared complete.
- Real PostgreSQL integration tests are configured through `DATABASE_URL`.
- Lardi smoke Run `34519177888` reached Lardi infrastructure but returned HTTP 403 Cloudflare Error 1010 / `browser_signature_banned`; this remains a provider-edge block requiring provider-side action.
- No retry loop, browser automation or anti-bot bypass was added.

## Provider status

Lardi discovery remains read-only. Canonical provider mapping remains blocked until a verified response is obtained. No field semantics are inferred from guessed JSON names.

## V19 release gate

1. Security boundaries and tenant isolation: implemented/documented; existing tenant-scoped tests remain mandatory.
2. Secrets/configuration and startup failure modes: implemented/documented; readiness fails closed and CI checks dependency consistency.
3. Migration/bootstrap/recovery review: implemented/documented; CI applies all SQL migrations with `ON_ERROR_STOP=1`.
4. Release smoke checks: implemented in `scripts/release_smoke.py` and wired into CI.
5. Provider contracts/deployment documentation: reconciled; official/permitted mechanisms only.
6. Lardi canonical mappings: intentionally blocked pending verified provider access/samples.
7. Contact/publication controls: intentionally gated behind permission, legal/privacy checks and human approval.
8. Threat/dependency/final documentation audit: implemented in release-gate and threat-model docs; `pip-audit` wired into CI.
9. Final release decision: blocked until the latest V19 CI run is green and all external/legal/provider blockers are explicitly cleared or accepted by the release owner.

## Security / compliance

Credentials remain runtime secrets. Review APIs require `REVIEW_OPERATOR_TOKEN`. No autonomous outreach, unsupported scraping, anti-bot bypass or external publication is enabled.

## Handoff

DONE: V17 reliability/replay foundation and V18 integration/deployment hardening, including PostgreSQL recovery coverage and green hosted CI.
V19 IMPLEMENTED: security/release documentation, threat model, local smoke checks, dependency consistency/audit and release-gate CI wiring.
PENDING: latest V19 hosted CI result; provider-side Lardi access/mapping; duplicate identity evidence; contact adapters and external publication permissions.
REQUIRED HUMAN ACTION: Lardi provider/support action before another live smoke. No repository-secret change is required.
OPEN_ISSUES: provider access/mapping, duplicate identity evidence, contact adapters and external publication permissions.
