# Commercial Batch V11

Date: 2026-09-10

## Completed

- Added PostgreSQL indexes supporting tenant-scoped duplicate-load candidate queries.
- Kept duplicate identity intentionally query-derived rather than enforcing a potentially unsafe database-level uniqueness constraint. Price remains excluded from duplicate identity because reposted offers can change price.
- Added durable `recurring_demand_runs` history for scheduler heartbeat/status, tenant count, pattern count and failure diagnostics.
- Scheduler now records running/succeeded/failed executions and preserves the existing `recompute_all_tenants()` return contract.
- Added authenticated operator visibility for likely duplicate-load groups.
- Added authenticated operator visibility for recurring-demand scheduler health.
- Docker Compose now mounts migrations 0018 and 0019.
- Runtime API image loads the review extensions so the new review endpoints are exposed.
- Added unit coverage for scheduler health persistence helpers.

## Verification boundary

The latest direct commits are present on `main`. GitHub currently reports no workflow runs for the latest direct test commit, so CI is **not** claimed as green.

A real PostgreSQL tenant-isolation integration suite is still pending because the repository's current automated environment does not expose a verified integration database run from this connector. Tenant scoping remains enforced in the application SQL paths.

Lardi provider-specific field mapping remains blocked by the previously observed provider-edge Cloudflare 403 and is not guessed around.

## Next batch

1. Add a real PostgreSQL integration harness with isolated tenant fixtures and run it in CI.
2. Harden duplicate grouping into connected components and add deterministic false-positive fixtures.
3. Add operator-level metrics for duplicate volume and recurring-demand freshness.
4. Resume Lardi canonical mapping only after verified provider response samples or provider-side access restoration.
5. Add only explicitly authorized provider contact adapters, with autonomous sending disabled.
6. Keep external publication gated until provider permission, terms, privacy/retention and legal requirements are verified.
