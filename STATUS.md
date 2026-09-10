# Project Status — AI Logistics OS

> Общая точка синхронизации для параллельно работающих людей и AI-агентов.

CURRENT_STEP: Publication adapters V1
STATUS: implemented_pending_runtime_ci
AGENT: publication-adapters-v1
MACHINE: ChatGPT/GitHub connector
STARTED: 2026-09-10
UPDATED: 2026-09-10
SCOPE: Контракт публикации канонического груза, provider-neutral renderer, provenance, явная роль экспедитора, markup policy gates и human-on-critical-risk. Реальная внешняя публикация пока не подключается.

## Completed

- Product vision, V1→V10 autonomy model, product specification, human workflow и distributed agent protocol.
- Technical architecture, roadmap and ecosystem/integration strategy.
- Routing/Geo/Optimization architecture and canonical geo pipeline.
- V1 backend skeleton, canonical domain, deterministic normalize→score→opportunity workflow.
- Policy/authorization and audit primitives.
- PostgreSQL baseline plus Telegram ingestion migrations.
- Telegram collection, deterministic parsing, canonicalization, atomic persistence/checkpointing and transactional outbox.
- Replay fixtures, PostgreSQL integration tests and optional OpenTelemetry.
- Hosted CI run `34502076880` green for the completed Telegram ingestion batch.
- Publication adapter contract and provider-neutral renderer.
- Publication policy gate for autonomy role, bounded markup, cancelled-load rejection and human approval for critical risk.
- Publication payload preserves source provenance and explicitly represents the role as `forwarder`.

## Current implementation

`canonical Load → PublicationRequest → PolicyEngine → PublicationAdapter → PublicationPayload`

The renderer does not perform network publication. Provider-specific transport must be implemented separately through permitted official APIs or explicitly authorized mechanisms.

## Verification

- Telegram ingestion hosted CI run `34502076880` passed package installation, all three PostgreSQL migrations and unit/integration tests.
- Publication adapter tests are committed and will be verified by the next hosted CI run.
- Local runtime execution remains unavailable in the current environment.

## Next batch

1. Harden outbox delivery with retries, leases, idempotent publication intents and replay reporting.
2. Add authorized provider transport adapters only where official/contractually permitted interfaces exist.
3. Build demand discovery and customer-opportunity graph.
4. Build carrier matching, pricing, negotiation and human-on-exception workflows.

## Security

Credentials and provider sessions remain runtime secrets and must not be committed.

## Compliance

Provider publication is gated and transport-neutral. No claim is made that any marketplace permits automation. Each integration must verify current terms, API permissions, privacy/retention requirements and applicable law before activation.

## Handoff

DONE: Telegram ingestion V1 runtime-green; publication contract, rendering, provenance, role representation and policy gates implemented.
VERIFIED: Remote GitHub state.
NOT YET VERIFIED: Hosted CI for publication adapter batch.
NEXT_STEP: Verify CI → outbox delivery hardening → authorized provider transports → demand discovery.

## OCI collector deployment — 2026-09-10

Runtime prepared in /opt/logistics. PostgreSQL healthy; image built; unit tests 17 passed, 4 integration tests skipped. Manual GitHub workflow transfers Telegram configuration with a restricted SSH key. Collector is NOT running: awaiting interactive Telegram login. Commands: deploy/README.md. Existing publication work remains unchanged.
