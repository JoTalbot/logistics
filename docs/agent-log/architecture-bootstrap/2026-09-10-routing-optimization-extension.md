# Routing/Optimization Architecture Extension — 2026-09-10

## Task
Evaluate external recommendations about open-source TMS/VRP architecture and incorporate only the parts that materially improve AI Logistics OS.

## Accepted

- External VRP solver behind an internal optimization interface.
- VROOM as initial general-purpose solver candidate.
- OR-Tools as advanced/experimental solver for validated special cases.
- Separate routing/matrix provider abstraction with OSRM and Valhalla candidates.
- Canonical address parsing, normalization, entity resolution and geocoding before optimization.
- Confidence, provenance and freshness metadata for geospatial results.
- Context-aware matrix caching behind an abstraction.
- Routing/solver replay benchmarks measuring feasibility, quality, latency and business economics.
- Optional local routing deployment profiles rather than mandatory regional map datasets.

## Rejected or corrected

- No hard dependency on VROOM, OSRM, Valhalla, Redis or any single provider.
- No claim that solver latency equals end-to-end application latency.
- No matrix cache key based only on coordinates.
- No requirement to run large OSM datasets in every local development environment.
- No decision on project license based solely on this technical analysis.

## Architectural principle

The business optimizer decides whether a load/opportunity is worth pursuing. The routing/optimization layer finds a feasible physical execution plan. Solver output is validated and returned to economic/risk evaluation before a business decision is accepted.

## Files changed

- `docs/ROUTING_OPTIMIZATION.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/ECOSYSTEM_AND_INTEGRATIONS.md`
- `docs/agent-skills/architecture-bootstrap.md`
- `STATUS.md`

## Verification

All changes were written directly to `main` through GitHub and received commit SHAs.
