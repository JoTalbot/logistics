# V32 — Operational Observability Contract

V32 adds a deterministic, side-effect-free evidence layer for operational telemetry.

## Signals

- **Provider latency:** per-provider sample count and mean latency in milliseconds.
- **Route quality:** mean absolute error between expected and observed route scores, plus a directional regression count.
- **Cost attribution:** explicit component units multiplied by unit cost.

## Contract

`build_observability_report()` accepts already-collected observations and returns a stable `OperationalObservabilityReport`. It performs no provider calls, database writes, pricing mutations, publication, negotiation, contract or financial actions.

All provider names are unique, latency/cost values are non-negative, and route scores are bounded to `[0, 1]`. Invalid input fails closed with `ValueError`.

The default route regression threshold is a **downward** score change of `0.10` or more. Improvements are not regressions. This is an operational signal, not an automatic policy decision.

## Production boundary

V32 does not enable autonomous commercial activity. Provider latency can be recorded even while a provider remains externally blocked, but a measurement must never be interpreted as proof of provider authorization or availability.

## Next step

Wire these deterministic signals into the existing ingestion/KPI and release-evidence paths, then add bounded time-windowed operational reporting without coupling observability to business mutations.
