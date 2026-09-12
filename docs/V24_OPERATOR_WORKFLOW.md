# V24 — Operator Opportunity Workflow

## Goal

V24 turns the V23 read-only commercial queue into a controlled operator workflow. An authenticated human can move an opportunity through `candidate`, `reviewed`, `hold`, `accepted`, or `rejected` while every transition is retained in an immutable history table.

## Flow

1. V23 calculates economics and priority.
2. Operator reads `/api/v1/review/commercial-opportunities`.
3. Operator submits an explicit status decision through `/api/v1/review/opportunities/decision`.
4. The API verifies the operator token and tenant scope.
5. The opportunity is locked, updated, and audited in one database transaction.
6. Metrics expose queue distribution and terminal acceptance rate.
7. History exposes who made each decision, why, and when.

## Endpoints

### POST `/api/v1/review/opportunities/decision`

Body fields:
- `tenant_id`
- `opportunity_id`
- `status`
- `operator_ref`
- `reason`

Required header: `X-Operator-Token`.

This endpoint changes only the internal opportunity review status. It does not publish a load, contact a customer/carrier, negotiate, sign a contract, or move money.

### GET `/api/v1/review/opportunities/metrics`

Returns counts by current status plus accepted/rejected/hold transition counts and the acceptance rate among terminal decisions.

### GET `/api/v1/review/opportunities/{opportunity_id}/history`

Returns tenant-scoped status history, newest first, with previous status, new status, operator reference, reason, and timestamp.

## Safety

- Authentication remains mandatory.
- Every query is tenant-scoped.
- A decision cannot target an opportunity without a persisted priority score.
- Database row locking prevents concurrent operators from silently overwriting the same starting state.
- Audit history is append-only from the application path.
- External publication, outreach, negotiation, financial commitments, and provider bypasses remain outside V24.

## Commercial KPI interpretation

The acceptance rate is deliberately limited to explicit `accepted` versus `rejected` review transitions. It is not presented as revenue or profit. A later stage should connect accepted opportunities to booked/delivered outcomes before claiming realized commercial conversion.

## Verification

CI must apply migration 0024, run the full test suite, validate Compose, execute release smoke checks, and build the production API image before V24 is merged.
