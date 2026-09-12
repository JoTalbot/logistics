# V23 — Commercial Opportunity Queue

## Purpose

V23 turns the deterministic commercial pipeline into a practical operator work queue. The queue exposes persisted opportunity economics together with canonical load context and commercial priority, without enabling external commitments.

## Operator flow

1. A permitted source produces a market observation.
2. The observation is normalized at the provider boundary.
3. A canonical load becomes an opportunity through deterministic pricing and scoring.
4. Commercial priority combines opportunity quality, carrier availability and recurring-demand signal.
5. The operator reads the highest-priority candidates from the review API.
6. The operator decides what to pursue using the displayed economics and explainable reasons.
7. Publication, outreach, negotiation and financial actions remain separately authorized workflows.

## Endpoint

`GET /api/v1/review/commercial-opportunities`

Parameters:

- `tenant_id` — required tenant scope.
- `status` — one of `candidate`, `reviewed`, `accepted`, `rejected`, `hold`; default `candidate`.
- `min_priority` — inclusive priority threshold from `0` to `1`; default `0`.
- `limit` — `1` to `100`; default `50`.
- `X-Operator-Token` — existing human operator credential.

The response includes load identity/context, offered price, estimated cost, estimated margin, risk-adjusted margin, opportunity score, priority score and their reasons.

## Safety

The endpoint is read-only and tenant-scoped. It does not publish a listing, contact a customer or carrier, negotiate, sign a contract, move money or bypass provider controls. Priority is a decision-support signal, not authorization.

## V23 verification target

CI must cover route registration, operator authentication, tenant scoping in SQL, ordering/threshold behavior and parameter validation. Production release remains gated by target-infrastructure rehearsal and provider authorization.
