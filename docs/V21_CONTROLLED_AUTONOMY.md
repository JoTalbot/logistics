# V21 — Controlled Autonomy Foundation

## Goal

Turn the roadmap's simulation/shadow-mode principle into a deterministic, reusable policy gate before any external side effect is enabled.

## Implemented

- `backend/logistics/autonomy_policy.py` defines the approval tiers `AUTO`, `REVIEW`, `HIGH_RISK`, and `BLOCK`.
- Confidence thresholds default to 0.90 for `AUTO` and 0.70 for `REVIEW`.
- Unauthorized actions always resolve to `BLOCK`.
- Critical-risk actions always resolve to `BLOCK`, regardless of model confidence.
- Explicit human approval requirements resolve to `REVIEW`, even with high confidence.
- Invalid confidence values and invalid threshold configuration fail closed with `ValueError`.
- Tests cover the default bands, hard blocks, human-approval override and bounds.

## Safety boundary

This module only classifies an intended action. It does not send messages, publish listings, negotiate, sign contracts, move money, call external providers or mutate business state.

Provider permissions, legal authorization, tenant policy and operational controls remain separate gates. A high confidence score is never treated as authorization.

## V21 next gates

1. Integrate this classifier with simulation/shadow decision records.
2. Persist policy version and classification reason alongside auditable decisions.
3. Add replay metrics comparing policy classifications with historical outcomes.
4. Add operator-visible exception queues for `REVIEW`, `HIGH_RISK` and `BLOCK` decisions.
5. Keep real external side effects disabled until provider and authorization gates are independently verified.

## Exit criterion

A simulated or shadow decision can be deterministically classified, explained and audited before any production side effect is eligible for execution.
