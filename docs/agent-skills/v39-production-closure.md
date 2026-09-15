# V39 — Production Closure Evidence Skill

## Goal

Verify repository-level transactional failure semantics for the Telegram ingestion contour and keep the release decision separate from external activation gates.

## Verification

1. Run the full repository CI workflow.
2. Confirm duplicate and changed-ad replay behavior.
3. Confirm rejected ads do not create canonical state.
4. Confirm an injected commit failure leaves no source, load, outbox, or checkpoint state.
5. Record the evidence without claiming external provider or infrastructure readiness.

## Safety

Evidence-only. Do not publish, contact, negotiate, contract, mutate pricing, book capacity, perform financial actions, or bypass provider protections.
