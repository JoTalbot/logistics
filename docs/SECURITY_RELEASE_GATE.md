# V19 Security, Compliance and Release Gate

## Scope

V19 is the final gate before a release candidate. It validates the existing market-intelligence/review system without enabling autonomous publication, outreach, provider bypasses or financial commitments.

## 1. Security boundaries and tenant isolation

- Every review/operator endpoint requires `REVIEW_OPERATOR_TOKEN`.
- Database reads and writes in review APIs must include the authenticated `tenant_id` in their predicates.
- Tenant identifiers are never inferred from request-global state.
- Probabilistic duplicate detection remains tenant-scoped and read-only.
- Contact intents remain separate from sending and require explicit authorization plus human approval.
- External publication remains disabled until provider capability, terms and legal requirements are verified.

Release criterion: tests demonstrate that data from tenant A cannot satisfy tenant B queries.

## 2. Secrets and configuration

- Provider/API credentials are runtime secrets and must not be committed to source.
- `LARDI_API_KEY` is consumed only from the runtime environment/secret store.
- `REVIEW_OPERATOR_TOKEN` is required for protected review endpoints.
- `DATABASE_URL` is required for readiness and database-backed API operations.
- Missing critical configuration must fail closed with an explicit error.
- Production deployments must replace development database credentials and should not expose PostgreSQL publicly unless an explicit network policy requires it.

## 3. Startup, readiness and recovery

- `/health` is liveness only.
- `/ready` verifies PostgreSQL reachability with a bounded timeout and returns HTTP 503 when unavailable.
- API containers wait for a healthy PostgreSQL dependency.
- Graceful shutdown allows up to 30 seconds for in-flight work.
- Outbox event UUID is the canonical idempotency identity.
- Delivery retries create attempt telemetry rather than new business events.

## 4. Migration/bootstrap review

- CI applies every SQL migration with `ON_ERROR_STOP=1`.
- Fresh Compose bootstrap mounts the complete migration sequence through `0021_outbox_delivery_telemetry.sql`.
- Migration numbering must remain unique.
- Destructive schema changes require an explicit migration and recovery plan. No automatic rollback is assumed.
- Production upgrades must take a database backup/snapshot before applying irreversible migrations.

## 5. Release smoke checks

The release smoke suite must cover:

1. liveness response;
2. readiness with a healthy database;
3. readiness failure/missing configuration;
4. protected review endpoint rejects missing/invalid operator credentials;
5. tenant-scoped review/reporting behavior;
6. outbox retry/ack/failure telemetry and replay identity;
7. migration/bootstrap integrity.

Smoke checks must use local/fake providers only. They must not publish externally, contact customers, bypass anti-bot controls, or spend funds.

## 6. Provider contracts

Lardi discovery remains read-only. Provider-specific canonical field mappings must be derived only from verified provider response samples. The current Cloudflare `browser_signature_banned` result is a provider-edge access issue, not a reason to add browser automation or bypass logic.

DELLA and future providers follow the same rule: official API/permitted mechanism, explicit capability contract, rate limits, terms and legal review before activation.

## 7. Contact and publication controls

Contact intents are planning/audit objects, not send commands. External publication and outreach require:

- provider permission/capability;
- terms/privacy/legal verification;
- authorized channel;
- suppression/opt-out checks;
- human approval for the current release boundary.

No release gate may silently enable autonomous contact or publication.

## 8. Threat model and dependency review

Primary threats:

- cross-tenant data leakage;
- leaked runtime secrets;
- unauthorized operator actions;
- replay/double delivery;
- stale scheduler state;
- migration drift;
- provider contract changes;
- dependency vulnerabilities;
- accidental activation of external side effects.

Mitigations are enforced through tenant predicates, operator authentication, transactional outbox semantics, durable telemetry, readiness checks, migration CI and explicit provider capability gates.

Dependency review must be repeated at release time against the lock/configuration actually deployed. Vulnerability findings must be triaged by reachability and exploitability rather than ignored or blindly upgraded.

## 9. Final release decision

Release is allowed only when:

- hosted CI is green;
- security/tenant-isolation tests are green;
- migration/bootstrap checks are green;
- readiness/recovery smoke checks are green;
- no critical unresolved security issue exists;
- provider access is documented as read-only where verification is incomplete;
- publication/contact remain disabled unless their permissions are explicitly verified;
- release notes and rollback/recovery runbook are present.

If any criterion fails, the release remains blocked. A green test suite does not override an external provider, legal or security blocker.
