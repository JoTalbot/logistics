# V30 — Readiness Gate Evaluation

## Purpose

V30 adds a deterministic, side-effect-free evaluator for explicit release evidence. It does not grant permissions or change runtime policy.

## Gate model

Each gate has:

- a unique name;
- `ready`, `pending`, or `blocked` status;
- evidence text for every non-ready state;
- a `required` flag separating release blockers from informational checks.

The evaluator returns total, ready, pending and blocked counts, the ordered names of required gates that are not ready, and a boolean `release_ready` result.

## Safety boundary

The evaluator is reporting-only. It cannot enable provider access, publication, outreach, negotiation, contracts, autonomy, or financial mutations. External provider and infrastructure verification remain separate operational gates.

## Determinism

The function accepts an iterable, materializes it once, rejects duplicate gate names, and derives the report only from supplied values. It performs no I/O and has no clock, network, database, or environment dependency.

## CI expectation

The normal CI pipeline remains authoritative for repository verification. A green CI result does not override pending or blocked operational/provider gates.
