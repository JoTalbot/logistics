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
- Tests cover confidence bands, hard blocks, human-approval override, simulation mode, policy metadata, invalid bounds and replay metrics.

## Safety boundary

These modules only classify intended actions and evaluate historical/synthetic outcomes. They do not send messages, publish listings, negotiate, sign contracts, move money, call external providers or mutate business state.

Provider permissions, legal authorization, tenant policy and operational controls remain separate gates. A high confidence score is never treated as authorization.

## V21 remaining gates

1. Identify and extend the existing durable decision/audit persistence model rather than creating a parallel audit store.
2. Persist shadow decisions with policy version, reason, tenant and correlation identifiers once that existing model is confirmed.
3. Connect replay metrics to historical decision outcomes without changing production state.
4. Extend the existing operator review queue/API for `REVIEW`, `HIGH_RISK` and `BLOCK` records if a compatible queue exists.
5. Keep real external side effects disabled until provider and authorization gates are independently verified.

## Exit criterion

A simulated or shadow decision can be deterministically classified, explained, persisted/audited through the existing decision model, replayed against historical outcomes and surfaced to an operator before any production side effect is eligible for execution.
