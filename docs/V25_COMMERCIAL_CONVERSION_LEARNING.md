# V25 — Commercial Conversion & Learning

V25 closes the measurement loop:

`opportunity → operator decision → outcome → actual economics → KPI → shadow learning`

## What is implemented

- Tenant-scoped durable commercial outcomes: `won`, `lost`, `cancelled`, `unknown`.
- Actual revenue, cost and realized margin capture.
- Immutable outcome history for every recorded correction/change.
- Operator-authenticated outcome recording.
- Conversion and realized-economics metrics.
- Predicted-versus-actual margin error metrics.
- Deterministic learning evaluation and drift gate.

## API

- `POST /api/v1/review/opportunities/outcome`
- `GET /api/v1/review/commercial-outcomes/metrics`
- `GET /api/v1/review/opportunities/{opportunity_id}/outcomes`

All endpoints are tenant-scoped and require the operator token.

## Learning boundary

V25 measures whether the scoring/pricing system was right. It does **not** automatically rewrite pricing, scoring or autonomy policy. The learning gate can report `INSUFFICIENT_DATA`, `REVIEW_DRIFT` or `SHADOW_READY`, but policy changes remain an explicit engineering/operator action followed by replay/shadow verification.

## Commercial interpretation

The most important numbers become:

1. accepted → won conversion;
2. realized revenue;
3. realized margin;
4. predicted margin error;
5. mean absolute prediction error;
6. loss/cancellation rate.

This allows the system to optimize for actual clean profit rather than merely producing attractive-looking opportunity scores.

## Safety boundary

Recording an outcome is internal accounting/evaluation state. V25 does not publish listings, contact customers or carriers, negotiate, sign contracts, dispatch vehicles, move money, or bypass provider controls.

## Exit criteria

V25 is technically complete when migration, API registration, unit tests, replay/learning evaluation, Compose validation, release smoke and production image build pass in CI. Production release remains separately gated by infrastructure rehearsal and provider authorization.
