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

Runtime prepared in /opt/logistics. PostgreSQL healthy; image built; unit tests 17 passed, 4 integration tests skipped. Manual GitHub workflow transfers Telegram configuration with a restricted SSH key. Collector is running after operator login. Live verification: 400 source messages across all four configured chats, 10 canonical loads, zero container restarts. Historical backfill disabled at user request. Latest-100 bootstrap completed for all four sources; incremental-only collection verified. Existing historical data retained. Commands: deploy/README.md. Existing publication work remains unchanged.

Latest-100 mode: fixed resumable snapshot per source, persistent completion across restarts; 20 tests passed, 4 integration tests skipped. Live bootstrap complete for all 4 sources; new messages observed afterwards.

## Read-only quality audit — 2026-09-10

Latest 100 stored messages per source (400 total), 13 pass canonical rules; this is not measured accuracy. No parser exceptions on replay. Synthetic tests found dash-route, spaced-price, currency, weight-unit, cargo, vehicle/date limitations. 47 normalized-text duplicate groups, 106 excess copies; no duplicate source/message keys. Report: docs/agent-log/oci-collector-deployment/quality-audit-2026-09-10.md. Runtime unchanged. Next: currency/price correctness, regression tests and locally human-labelled quality evaluation before reparsing production data.

## Local LLM normalization — 2026-09-10

Operator requested local LLM processing. Added separate PostgreSQL queue + Ollama qwen2.5:1.5b worker (installed model, digest pinned). Latest 100 stored messages/source queued once, then newly stored messages. Loopback-only Ollama and DB, restricted DB role, strict schema, source-evidence checks, deterministic unit/currency/date normalization; ALL outputs require human review and remain separate from loads. 29 unit tests passed, 4 integration tests skipped. Synthetic live extraction verified route/weight/price/currency but model falsely flagged multiple_ads; no accuracy claim. First live job completed successfully. CPU inference may create backlog; collector continues independently. Details: deploy/LOCAL_LLM.md. Next: local labelled evaluation and review UI; no auto-publication.

## Batch local LLM — 2026-09-10

Requested up to 100 pending messages/file/request, separate normalized DB records. Implemented context-bounded packing, protected JSON inputs, keyed required output IDs, per-record validation/persistence and retries, batch audit table (migration 0005). No raw text exported. 35 tests passed, 4 skipped. Live test: 3 ads / 1 inference / 3 saved, 139.5 sec; not an accuracy or speedup claim. Limit now 100; active batch contains 31 ads and is not yet verified complete. Raw files retained 24h after batch termination then cleaned by worker. Existing review-only policy retained. Details: deploy/BATCH_PROCESSING.md.

## Batch quality check — 2026-09-10 17:32 UTC snapshot

Read-only audit: 31-item batch still processing after 477s, not verified complete. Queue completed31/pending447/processing31/skipped6; 50 newly stored messages not yet enqueued because scheduling waits on inference. Collector saved61 messages in preceding10min. Host memory available about1.3GiB; 1min load11.94 on4CPU. Completed sample31 records =15 unique texts, all one source, only5 batch-mode records; no representative accuracy claim. Routes25, normalized weight3, price11/currency0, required fields complete0; 29 records had unsupported fields rejected. Need weight extraction/normalization review, independent enqueue, matched small-batch benchmark and human-labelled evaluation. Runtime unchanged. Report docs/agent-log/oci-collector-deployment/batch-quality-audit-2026-09-10.md.

## Enqueue and numeric V2 — 2026-09-10

User approved items1–3. Independent enqueuer now runs every10s; verified0 unqueued with normalizer paused. Version2 source-grounded weight units/ranges and monetary labels/currencies; pending478 jobs upgraded, completedV1 preserved. Read-only numeric replay on31 previous results: weight3→15; sums11→6 (unsupported removed), currency remains0; no accuracy claim. 56 tests passed,4 skipped. Matched benchmark on same10 unique real short ads running in order5/3/10; batch5 completed10/10 in243.99s, other cases pending. Inference paused only for benchmark, collector/enqueuer continue; wrapper restores selected limit and normalizer automatically. See deploy/QUEUE_AND_NUMBERS_V2.md.

## Completed: queue/numbers/benchmark V2

Matched10-ad benchmark completed: size3=176.71s/4requests, size5=243.99s/2requests, size10=187.31s/1request; all returned10/10 schema-valid outputs. Selected size3 provisionally; one fixed-order pass on short ads/shared host, no semantic accuracy claim. Normalizer restored; first production V2 batch saved3 in56.07s, later6 completedV2 including cache. Enqueuer heartbeat fresh and unqueued0 during benchmark. Original content never exported. Full results: docs/agent-log/oci-collector-deployment/queue-v2-benchmark-results.md and batch-benchmark-2026-09-10.json. All three requested items complete; backlog remains, throughput monitoring and human review still needed.

## Current backend: AIOS LLMBalancer cloud-only

User explicitly requested server LLMBalancer instead of local model. Existing AIOS bridge9600 now supports opt-in cloud_only/json_mode with backward-compatible defaults; cloud-only excludes Ollama/RPA/emergency fallbacks and disables prompt cache. Increased structured response budget to4096 for opt-in requests after JSON truncation errors; retried affected18 jobs. Pipeline logistics-extract-v3 retains source-grounded normalization and review-only records;752 pending jobs migrated, old completed results preserved. Actual provider stored per normalized result; model_digest is now route fingerprint for cloud jobs. Qwen1.5B unloaded (~1.8GB); other embedding model retained, available RAM~4.2GiB at check.62 tests passed/4 skipped, AIOS cloud-only tests passed,52 cloud results observed with Groq/Gemini routing and recent3-ad batches2–11s. IMPORTANT: text now leaves host to configured cloud providers by user opt-in. See deploy/LLMBALANCER.md and infrastructure patch.
