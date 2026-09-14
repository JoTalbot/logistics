# V30/V31 — Readiness Gate Evaluation

## Purpose

V30 adds a deterministic, side-effect-free evaluator for explicit release evidence. V31 connects that evaluator to the local release smoke path and emits machine-readable evidence. Neither change grants permissions or changes runtime policy.

## Gate model

Each gate has:

- a unique name;
- `ready`, `pending`, or `blocked` status;
- evidence text for every non-ready state;
- a `required` flag separating release blockers from informational checks.

The evaluator returns total, ready, pending and blocked counts, the ordered names of required gates that are not ready, and a boolean `release_ready` result.

## Release smoke integration

`scripts/release_smoke.py` records explicit evidence for the local checks it performs:

- API health;
- database failure handling;
- operator authentication rejection;
- tenant-scoped audit reporting.

The smoke path calls the same readiness evaluator used by the application code and emits a JSON object with schema `logistics.release-readiness.v1`. If any required gate is not ready, the evidence helper fails closed with a non-zero error instead of reporting a successful release readiness state.

The evidence is generated only from checks already performed by the smoke process. It does not claim that external provider access, production backups, deployment accounts, publication permissions, or target-infrastructure rehearsals are ready.

## Safety boundary

The evaluator and smoke evidence are reporting-only. They cannot enable provider access, publication, outreach, negotiation, contracts, autonomy, or financial mutations. External provider and infrastructure verification remain separate operational gates.

## Determinism

The evaluator accepts an iterable, materializes it once, rejects duplicate gate names, and derives the report only from supplied values. It performs no I/O and has no clock, network, database, or environment dependency. The smoke script uses deterministic/fake dependencies for its verification path.

## CI expectation

The normal CI pipeline remains authoritative for repository verification. A green CI result does not override pending or blocked operational/provider gates.
