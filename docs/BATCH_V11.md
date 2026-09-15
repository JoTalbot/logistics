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

This document records the V11 implementation state from 2026-09-10. Later V38/V39 work superseded the verification notes below.

- PostgreSQL integration coverage is now part of the repository test suite, including tenant-isolation, market-observation, outbox-recovery and Telegram-store integration tests.
- CI provisions PostgreSQL 17 as a GitHub Actions service, applies all migrations in order, and runs the unit/integration test suite. The current V39 status records the authoritative successful CI verification.
- Lardi provider-specific field mapping remains blocked by the previously observed provider-edge Cloudflare 403 and is not guessed around.

## Superseded next-batch items

The original V11 next-batch list is retained as historical context. Its PostgreSQL integration-harness item is complete; subsequent V12-V39 work delivered the later reliability, observability, commercial-learning, controlled-autonomy, Telegram-ingestion and production-readiness increments.

Current execution priority is therefore governed by `STATUS.md` and the V39 production-closure evidence, not this historical batch note.

Remaining work is primarily external production activation: target-infrastructure backup/restore rehearsal, provider access/mapping, explicitly authorized contact/publication permissions, authorized Telegram source access, real commercial outcome telemetry, and Vercel account remediation.
