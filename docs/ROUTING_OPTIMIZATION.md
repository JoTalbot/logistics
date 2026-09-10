# Routing and Optimization Architecture

## Purpose

Provide a provider- and solver-independent optimization layer for the AI Logistics OS. The system separates economic/business decisions from physical route solving.

## Responsibility boundary

The Logistics OS decides **what is economically and operationally worth doing**:

- which loads to accept;
- which combinations form an opportunity portfolio;
- target revenue and carrier price;
- risk-adjusted profit;
- opportunity cost and price of refusal;
- service/SLA requirements;
- business and compliance constraints.

The optimization layer decides **how the selected work can be physically executed**:

- vehicle/load assignment;
- stop ordering;
- capacity feasibility;
- time-window feasibility;
- pickup/delivery sequencing;
- route distance/time;
- empty-mile reduction;
- multi-stop and multi-vehicle routing.

A solver result is therefore an input to business evaluation, not an authoritative business decision.

## Solver abstraction

```text
OptimizationService
  ├── VROOMAdapter
  ├── ORToolsAdapter
  ├── CommercialRouteOptimizerAdapter (optional)
  └── FutureSolverAdapter
```

### VROOM

Use VROOM as the initial general-purpose routing solver for standard VRP-family workloads. Keep it behind an internal adapter and do not expose VROOM request/response objects as domain models.

Good initial use cases:

- capacity-constrained VRP;
- time windows;
- pickup/delivery;
- multi-vehicle routing;
- skills/compatibility constraints;
- driver breaks and working constraints where supported by the selected version/configuration.

### OR-Tools

Use OR-Tools as the advanced/experimental solver for cases where the business requires unusual constraints, objective functions or combinatorial formulations that are awkward for the primary solver.

The architecture must allow side-by-side replay comparison between solvers.

## Routing provider abstraction

Solvers consume canonical matrices and routing data through a separate interface:

```python
class RoutingProvider(Protocol):
    def route(self, request: RouteRequest) -> RouteResult: ...
    def matrix(self, request: MatrixRequest) -> MatrixResult: ...
    def geocode(self, request: GeocodeRequest) -> GeocodeResult: ...
    def reverse_geocode(self, request: ReverseGeocodeRequest) -> ReverseGeocodeResult: ...
```

Initial provider candidates:

- OSRM;
- Valhalla;
- commercial providers where justified by coverage, traffic, restrictions or economics.

The domain must never depend on provider-specific route or matrix schemas.

## Geo intelligence pipeline

Raw addresses must pass through a canonicalization pipeline before optimization:

```text
raw address
  → language/format detection
  → parsing
  → normalization
  → entity resolution
  → geocoding
  → confidence assessment
  → canonical location
  → routing matrix
```

Persist provenance and confidence. Do not silently replace a high-confidence location with a lower-confidence geocode.

## Matrix caching

Introduce a `MatrixCache` abstraction. Cache keys must represent the complete calculation context rather than only coordinates.

A canonical cache fingerprint should include, as applicable:

- normalized locations and stable ordering;
- routing provider and provider version;
- map dataset/version or equivalent freshness marker;
- routing profile;
- vehicle/access restrictions;
- traffic/time mode;
- departure-time bucket for time-dependent routing;
- relevant country/road rules.

SHA-256 may be used as the fingerprint encoding, but the hash algorithm is not the architectural contract.

Cache entries must include creation time, source metadata and freshness/validity information. Cache is never authoritative state.

## Benchmark and replay system

Routing changes must be measurable, not judged only by unit-test success.

Each benchmark/replay case should capture:

- input scenario version;
- solver/provider/version;
- solve latency;
- route distance and duration;
- vehicle count;
- unserved jobs;
- constraint violations;
- operational cost;
- estimated gross margin;
- risk-adjusted margin;
- reproducibility metadata.

Compare:

1. current production candidate;
2. previous baseline;
3. alternative solver/provider;
4. historical/manual result where available.

No optimization engine is promoted because it is merely faster. Promotion considers feasibility, solution quality, business economics and reliability.

## Failure and fallback

Every routing/optimization request must tolerate:

- timeout;
- provider outage;
- incomplete matrix;
- invalid geocode;
- solver infeasibility;
- stale map data;
- rate limits;
- partial results.

Fallback order is configuration-dependent and may use another provider or solver. When no trustworthy result exists, the system must return an explicit `OPTIMIZATION_UNAVAILABLE` state rather than fabricate a route.

## Deployment profiles

Local development should not require downloading full geographic datasets.

Provide profiles such as:

- `routing-minimal`: external/remote routing provider;
- `routing-osrm`: local OSRM;
- `routing-valhalla`: local Valhalla;
- `routing-full`: solver + local routing + cache + benchmark fixtures.

Large regional map datasets are deployment assets, not source-controlled application dependencies.

## V1 implementation order

1. Canonical routing and optimization contracts.
2. Deterministic fake provider/solver for tests.
3. VROOM adapter.
4. OSRM/Valhalla-compatible matrix provider adapters.
5. Matrix cache.
6. Address normalization/geocoding pipeline.
7. Replay/benchmark fixtures.
8. OR-Tools adapter for validated special cases.

## Architectural invariants

1. Solver is replaceable.
2. Routing provider is replaceable.
3. Business objective is not encoded solely in a solver.
4. Provider schemas never become domain schemas.
5. Cached matrices are never authoritative.
6. Every optimization result is reproducible or has an explicit non-reproducibility reason.
7. No route is accepted without constraint validation.
8. Historical replay must be able to compare optimization strategies.
