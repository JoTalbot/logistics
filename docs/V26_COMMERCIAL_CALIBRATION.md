# V26 — Commercial Calibration & Feedback Loop

## Purpose

V26 measures whether commercial priority scores and predicted margins correspond to realized business outcomes. It is an evaluation layer, not an autonomous policy editor.

## Flow

`opportunity → priority score → operator decision → realized outcome → prediction error → calibration report`

Observations are grouped into deterministic priority bands:

- `very_high`: 0.90–1.00
- `high`: 0.75–0.8999
- `medium`: 0.50–0.7499
- `low`: 0.00–0.4999

For each band the system reports sample size, terminal outcomes, win rate, mean prediction error and mean absolute prediction error. A band is considered sufficiently sampled only when its terminal outcome count reaches the configured minimum.

## Drift signal

The evaluator compares adjacent sufficiently sampled bands. A drift signal is raised when either:

- win-rate separation reaches the configured threshold; or
- mean absolute prediction-error separation reaches the configured threshold.

This is intentionally a review signal, not proof that the scoring model is wrong. Small or incomplete samples remain explicitly marked as insufficient.

## API

`GET /api/v1/review/commercial-calibration`

Parameters:

- `tenant_id` — required tenant scope
- `limit` — outcome rows to inspect, 1–10000
- `min_sample` — minimum terminal observations per band
- `drift_win_rate_delta` — material win-rate gap threshold
- `drift_error_delta` — material absolute prediction-error gap threshold

Authentication uses the existing operator token.

The response includes a deterministic recommendation:

- no drift: `no scoring change recommended`
- drift: `review scoring calibration manually`

The response also exposes `policy_mutation: false` as an explicit safety invariant.

## Safety boundary

V26 never changes pricing, opportunity scoring, autonomy thresholds or external state. It does not publish listings, contact customers/carriers, negotiate, sign contracts or move money. Any future scoring change must be separately reviewed, tested against historical outcomes and explicitly deployed.

## Exit criteria

- deterministic calibration library covered by tests;
- tenant-scoped read-only aggregation over durable commercial outcomes;
- sample sufficiency visible per band;
- material drift signal covered by tests;
- authenticated operator endpoint;
- no automatic policy mutation;
- CI green before merge.
