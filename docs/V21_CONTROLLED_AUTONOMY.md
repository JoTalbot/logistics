# V21 — Controlled Autonomy Integration

## Goal

Turn the roadmap's simulation/shadow-mode principle into a deterministic, reusable policy gate before any external side effect is enabled.

## Implemented

- `backend/logistics/autonomy_policy.py` defines the approval tiers `AUTO`, `REVIEW`, `HIGH_RISK`, and `BLOCK`.
- Confidence thresholds default to 0.90 for `AUTO` and 0.70 for `REVIEW` and remain configurable.
- Unauthorized actions always resolve to `BLOCK`.
- Critical-risk actions always resolve to `BLOCK`, regardless of model confidence.
- Explicit human approval requirements resolve to `REVIEW`, even with high confidence.
- `backend/logistics/shadow_decisions.py` wraps classification in explicit `SIMULATION` and `SHADOW` records.
- Each shadow/simulation record carries a policy version and human-readable classification reason alongside tenant, action and confidence metadata.
- `backend/logistics/policy_replay.py` provides deterministic replay metrics for policy tiers and historical outcomes, including AUTO failure rate.
- `migrations/0022_autonomy_decisions.sql` adds a durable tenant-scoped decision record for simulation/shadow classifications. It is a decision store, not a replacement for the existing human `review_audit` trail.
- `backend/logistics/autonomy_store.py` connects classification to durable persistence idempotently and exposes a tenant-scoped exception queue for `REVIEW`, `HIGH_RISK` and `BLOCK` decisions.
- `backend/logistics/historical_policy_replay.py` joins durable autonomy decisions to durable outbox delivery telemetry and derives `SUCCESS`, `FAILURE` or `UNKNOWN` outcomes without writing state.
- Historical replay is aggregated by policy version so AUTO failure rates can be compared between policy revisions.
- `GET /api/v1/review/autonomy-exceptions` exposes the exception queue through the existing authenticated operator review boundary.
- `GET /api/v1/review/autonomy-replay` exposes tenant-scoped historical replay metrics grouped by policy version through the same authenticated boundary.
- Tests cover confidence bands, hard blocks, human-approval override, simulation mode, policy metadata, durable persistence, tenant isolation, invalid bounds, replay metrics and authenticated API access.

## Safety boundary

These modules only classify intended actions and read durable historical telemetry. They do not send messages, publish listings, negotiate, sign contracts, move money, call external providers or mutate business state.

Provider permissions, legal authorization, tenant policy and operational controls remain separate gates. A high confidence score is never treated as authorization.

Historical outcome rules are conservative: a correlated decision is `SUCCESS` when a matching delivery attempt succeeded, `FAILURE` when no success exists but a delivery attempt failed, and otherwise `UNKNOWN`. Missing telemetry is never treated as success.

## V21 remaining gates

1. Validate historical aggregation against real production-shaped outcomes after target infrastructure telemetry is available.
2. Establish sufficient historical sample size before using policy-version metrics for threshold changes or autonomy expansion.
3. Keep real external side effects disabled until provider and authorization gates are independently verified.

## Exit criterion

A simulated or shadow decision can be deterministically classified, explained, durably persisted, replayed against historical outcomes, compared by policy version and surfaced to an authenticated operator before any production side effect is eligible for execution.
