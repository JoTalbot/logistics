# Production Runbook

## Purpose

Operational procedure for running Logistics OS in a production-like environment. External publication, customer contact, negotiation, contracts, payments, and other real-world side effects remain explicitly authorized and auditable.

## 1. Preflight

Before every release or restart:

1. Confirm the target commit and release scope.
2. Confirm PostgreSQL is reachable and has enough disk space.
3. Confirm `DATABASE_URL` and `REVIEW_OPERATOR_TOKEN` are present in the runtime environment.
4. Confirm provider credentials are supplied only where the provider contract permits their use.
5. Confirm no real secrets are present in `.env.example` or repository files.
6. Review `docs/SECURITY_RELEASE_GATE.md` and `docs/PROVIDER_READINESS.md`.
7. Confirm backup freshness and restore procedure availability.
8. Confirm the operator knows the rollback target.

## 2. Environment

Use a secret manager or protected deployment environment for production values. Never commit `.env` files containing real credentials.

Minimum application configuration:

- `DATABASE_URL`
- `REVIEW_OPERATOR_TOKEN`
- `API_PORT` when a non-default local binding is required
- provider secrets only after documented access approval

The supplied Compose configuration intentionally binds the API to localhost and does not publish PostgreSQL directly.

## 3. Startup

From the repository checkout:

```bash
docker compose config
docker compose up -d postgres
docker compose up -d api scheduler
docker compose ps
```

Verify liveness and readiness through the protected deployment interface. `/health` confirms process liveness; `/ready` requires database connectivity.

## 4. Database migrations

Apply migrations in filename order against the intended database. Back up the database before destructive or structurally significant changes.

For a controlled manual migration:

```bash
for migration in migrations/*.sql; do
  echo "Applying ${migration}"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done
```

Do not skip migrations or apply them out of order.

## 5. Backup

At minimum, maintain a recent PostgreSQL logical backup before release operations:

```bash
pg_dump "$DATABASE_URL" --format=custom --file="logistics-$(date +%Y%m%d-%H%M%S).dump"
```

Store backups outside the application container, protect them as sensitive operational data, and periodically verify that the backup can actually be restored.

## 6. Restore rehearsal

Use a disposable PostgreSQL instance for rehearsal. Never test restoration by overwriting the only production copy.

```bash
createdb logistics_restore_test
pg_restore --clean --if-exists --dbname=logistics_restore_test logistics-YYYYMMDD-HHMMSS.dump
```

After restoration, run the migration/schema checks and application readiness checks. Record the rehearsal date and result.

## 7. Scheduler health

The recurring-demand scheduler is expected to run every six hours. Inspect the scheduler health endpoint and investigate:

- `critical` or `failed` state;
- stale last-success timestamp;
- runs stuck in `running` beyond the configured timeout;
- repeated failures;
- unexpected zero-output runs.

If the scheduler is unhealthy, stop treating derived recurring-demand signals as fresh until recovery is confirmed.

## 8. Outbox and replay recovery

Delivery is transactional and idempotent. On delivery failure:

1. inspect the delivery attempt telemetry;
2. identify the event and tenant;
3. determine whether the failure is transient or permanent;
4. retry only through the supported outbox/recovery path;
5. verify the event is not duplicated;
6. record the incident and final outcome.

Never bypass idempotency checks with manual duplicate inserts.

## 9. Degraded mode

When a dependency is unavailable:

- keep ingestion and read-only analysis running when safe;
- disable affected external side effects;
- surface the dependency failure to the operator;
- preserve raw/provider provenance where available;
- do not substitute unverified provider fields;
- do not bypass provider controls.

A provider outage is a reason to degrade, not an invitation to invent a scraper.

## 10. Provider blocker handling

For Lardi and other external providers, use only documented APIs and permitted mechanisms. A provider-side 403, Cloudflare block, rate-limit response, contract change, or missing capability must be recorded as a provider readiness blocker.

Do not implement browser-signature spoofing, anti-bot bypasses, credential workarounds, or autonomous publication to recover from a provider block.

## 11. Incident response

For an operational incident:

1. identify the affected component and tenant scope;
2. stop unsafe external side effects;
3. preserve logs, audit records, and delivery telemetry;
4. assess data integrity and duplicate risk;
5. restore service or enter degraded mode;
6. verify `/ready` and scheduler health;
7. verify queue/outbox state;
8. document root cause, impact, mitigation, and follow-up.

For suspected secret exposure, rotate the affected credential immediately through the secret-management system and invalidate the exposed credential.

## 12. Rollback

Rollback is permitted only to a known-good commit and compatible database state.

Before rollback:

- stop or isolate workers that could produce side effects;
- preserve current logs and telemetry;
- determine whether database migrations are backward-compatible;
- restore the previous application image/code;
- verify readiness and critical read paths;
- resume workers only after the rollback checks pass.

Never assume a code rollback can safely undo an irreversible database migration.

## 13. Release checklist

- [ ] CI is green for the release commit.
- [ ] Dependency audit is clean.
- [ ] SQL migrations pass from a fresh database.
- [ ] Unit/integration tests pass.
- [ ] Release smoke passes.
- [ ] Container build succeeds.
- [ ] Runtime uses a non-root API user.
- [ ] PostgreSQL is not publicly exposed.
- [ ] Required secrets fail closed when absent.
- [ ] Backup exists and restore rehearsal is current.
- [ ] Scheduler health is observable.
- [ ] Outbox telemetry and replay path are verified.
- [ ] Provider readiness has no unreviewed blocker.
- [ ] External publication/contact permissions are documented.
- [ ] Rollback target is known.

## 14. Go / no-go decision

**GO** only when the application pipeline is observable, recoverable, backed up, and all external side effects are explicitly authorized.

**NO-GO** when provider access is blocked or unverified, required secrets/configuration are missing, restore capability is unverified, migrations are unsafe, or any external side effect lacks explicit authorization.
