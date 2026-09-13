# V25 — Commercial Outcomes & Learning

## Goal

V25 closes the commercial feedback loop:

`opportunity → operator decision → realized outcome → actual margin → KPI → shadow learning`

The system now measures whether opportunities that looked profitable actually produced revenue and margin. This is the missing bridge between a clever scoring function and evidence that the business makes money. Humanity has survived without it for centuries, but the database should probably know the difference.

## Outcome model

`commercial_outcome_history` is tenant-scoped and append-only from the application path. Supported outcomes:

- `won`
- `lost`
- `cancelled`
- `unknown`

Each event can retain offered price, actual revenue, actual cost, realized margin, currency, operator reference, reason and correlation ID.

For measured outcomes:

`actual_margin = actual_revenue - actual_cost`

The application never treats an outcome event as authorization for an external action.

## Operator API

### POST `/api/v1/review/opportunities/outcome`

Records an internal commercial outcome. Requires `X-Operator-Token`.

Required fields:
- `tenant_id`
- `opportunity_id`
- `outcome`
- `currency`
- `operator_ref`
- `reason`

Optional financial fields:
- `offered_price`
- `actual_revenue`
- `actual_cost`
- `correlation_id`

The opportunity must exist in the same tenant and the outcome currency must match the load currency.

### GET `/api/v1/review/commercial-outcomes/metrics`

Returns outcome counts, terminal win rate, realized revenue and realized margin for won opportunities, plus average prediction error.

### GET `/api/v1/review/opportunities/{opportunity_id}/outcomes`

Returns the tenant-scoped append-only outcome history.

### GET `/api/v1/review/commercial-outcomes/prediction-vs-actual`

Returns measured opportunities with priority score, predicted margin, actual margin and prediction error.

## Learning layer

`commercial_learning.py` evaluates historical cases by priority bands:

- `0.90-1.00`
- `0.70-0.89`
- `0.00-0.69`
- `unknown`

It reports terminal win rate and average prediction error by band.

The learning policy is explicitly `shadow-only-v25.1`:

- no automatic price changes;
- no automatic score-weight changes;
- no automatic autonomy-tier changes;
- no external action;
- policy changes require replay and human review.

This provides measurable calibration/drift evidence before any future policy adjustment.

## Safety

V25 does not publish listings, contact customers or carriers, negotiate, sign contracts, move money, bypass provider controls, or silently change commercial policy. Model confidence and observed learning metrics are inputs to review, never authorization.

## Exit criteria

V25 is technically complete when CI verifies:

1. migration 0025;
2. tenant-scoped outcome persistence;
3. realized-margin calculation;
4. authenticated outcome API;
5. history and KPI endpoints;
6. prediction-vs-actual reporting;
7. deterministic shadow learning;
8. Compose contract and production API image build.

Production remains gated on target infrastructure rehearsal, provider authorization and real operational outcome telemetry.
