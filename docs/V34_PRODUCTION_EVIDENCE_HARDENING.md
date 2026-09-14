# V34 — Production Evidence Hardening

## Scope

V34 strengthens release-readiness evidence integrity without enabling autonomous external actions.

## Delivered

- `readiness_evidence()` now emits a deterministic `content_sha256` fingerprint.
- The fingerprint is calculated from the canonical JSON representation of the evidence payload before the fingerprint field is added.
- Canonical serialization uses sorted keys, compact separators and UTF-8 encoding.
- Required unready gates still fail closed before evidence is fingerprinted.
- Existing `logistics.release-readiness.v1` schema remains backward-compatible; the fingerprint is additive evidence.
- Focused tests verify deterministic output and fail-closed behavior.

## Integrity contract

For identical readiness gates, the evidence payload and `content_sha256` are identical regardless of whether the input is a list or tuple. Any change to gate status, evidence, requirement, ordering, report values or schema changes the fingerprint.

The fingerprint provides traceability and tamper-detection for evidence snapshots. It is not a signature, authorization proof, provider availability proof, or permission to publish, negotiate, contract, change pricing or move money.

## Safety boundary

V34 remains evidence-only. No provider calls, publication, negotiation, contracting, pricing mutation or financial action is introduced.
