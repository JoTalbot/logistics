# V38 Production Verification Checklist

## Software contour

- [ ] Repository CI executes the complete test and release-gate workflow.
- [ ] Telegram parser and fail-closed validation remain deterministic.
- [ ] Ingestion persists source message, parsed ad, canonical load, outbox event and checkpoint transactionally.
- [ ] Duplicate/replay processing is idempotent.
- [ ] Commercial discovery consumes the accepted current batch and produces deterministic evidence.
- [ ] Failure paths do not advance source checkpoints beyond failed persistence.
- [ ] Observability records accepted, duplicate and failed ingestion outcomes.

## External production gates

- [ ] Authorized Telegram credentials and source access.
- [ ] Target infrastructure backup/restore rehearsal.
- [ ] Hardened Compose end-to-end rehearsal.
- [ ] Lardi provider authorization/access mapping.
- [ ] Explicit publication/contact authorization.
- [ ] Real booked/delivered outcome telemetry.
- [ ] Vercel account/integration remediation.

## Release rule

Do not label the system production-ready solely because repository tests pass. Production readiness requires both software evidence and completion of the applicable external gates.

## Safety rule

No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action is introduced by V38.
