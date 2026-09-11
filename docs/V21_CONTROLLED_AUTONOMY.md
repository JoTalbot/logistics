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
- `GET /api/v1/review/autonomy-exceptions` exposes that queue through the existing authenticated operator review boundary.
- Tests cover confidence bands, hard blocks, human-approval override, simulation mode, policy metadata, durable persistence, tenant isolation, invalid bounds, replay metrics and authenticated API access.

## Safety boundary

These modules only classify intended actions and evaluate historical/synthetic outcomes. They do not send messages, publish listings, negotiate, sign contracts, move money, call external providers or mutate business state.

Provider permissions, legal authorization, tenant policy and operational controls remain separate gates. A high confidence score is never treated as authorization.

## V21 remaining gates

1. Connect replay metrics to persisted historical decision outcomes without changing production state.
2. Add policy-version-aware outcome aggregation when enough real historical outcomes exist to make it meaningful.
3. Keep real external side effects disabled until provider and authorization gates are independently verified.

## Exit criterion

A simulated or shadow decision can be deterministically classified, explained, durably persisted, replayed against historical outcomes and surfaced to an authenticated operator before any production side effect is eligible for execution.
