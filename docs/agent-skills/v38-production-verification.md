# V38 — Production Verification Evidence Gate

## Goal

Verify the already-implemented Telegram ingestion → persistence → commercial discovery contour without pretending that external provider access or target infrastructure is available.

## Verification layers

1. **Static/code verification** — imports, typing, deterministic data flow and safety boundary.
2. **Focused tests** — parser/validation, discovery ranking, ingestion idempotency and orchestration ordering.
3. **Database integration** — PostgreSQL transaction, canonical load persistence, outbox idempotency and source checkpoints.
4. **Replay verification** — repeated source messages must not create duplicate canonical state or duplicate outbox effects.
5. **Operational evidence** — failures are observable and do not advance checkpoints past a failed persistence operation.
6. **External gates** — live Telegram credentials/source authorization, target infrastructure rehearsal, provider access and Vercel account status remain explicit gates.

## Acceptance boundary

V38 may declare the software contour verified only from reproducible repository/CI evidence. A green code/test gate does not imply live provider authorization, successful Lardi access, production backup readiness, or permission to publish/contact/negotiate.

## Safety

Evidence-only. No autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, financial action, or Cloudflare/provider-control bypass is permitted.
