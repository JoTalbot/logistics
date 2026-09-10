# OCI collector deployment

Added manual secret-transfer workflow and independent Docker Compose runtime. Restricted forced-command SSH key; host key pinned; runtime secrets excluded from Git; database has no published ports. PostgreSQL migrations checked, unit tests 17 passed / 4 skipped. Live Telegram access pending interactive operator login. Follow deploy/README.md. This deployment does not alter publication adapters. Existing telegram-load-ingestion-v1 skill was used.

## Live verification

Operator completed Telegram login and started collector. Both containers running; PostgreSQL healthy; restart policy unless-stopped, zero restarts. First live check: 100 persisted messages from each of four sources (400 total), 10 canonical loads. Historical backfill begins at oldest available messages; current-message catch-up not yet verified. No raw messages or credentials were printed during verification.

## Latest-100 mode

User requested one-time latest 100 per source, then new messages only. Added atomic persistent snapshot and completion state; replay on interruption uses idempotent store. All four snapshots completed, subsequent new messages verified. Existing historical data retained. Fixed parser zero weight/volume/price validation failures found during live verification. Tests 20 passed, 4 skipped. Files: deploy/collector.py, backend/logistics/telegram.py, tests/test_collector_bootstrap.py and deployment documentation.

## Read-only quality audit

Used repeatable-read PostgreSQL snapshot, latest 100 stored messages per source. Only aggregates and synthetic examples exported, no raw Telegram content or contacts. Script deploy/audit_quality.py can be run by piping into docker exec -i logistics-collector-collector-1 python -. Found 13/400 records passing gates, 7/9 targeted synthetic cases expose gaps. See quality-audit-2026-09-10.md. No production parser or collection changes made during this audit.

## Local LLM worker

Read existing Telegram skill/status and Ollama structured output documentation (https://docs.ollama.com/capabilities/structured-outputs). Explicit operator opt-in expands regex-only policy to local-only inference, no training/cloud. Resource check: 4 CPU, 23 GiB total, 3.4 GiB available before load. Selected existing qwen2.5:1.5b; 7B not loaded. Separate persistent jobs, replay/retries/cache, schema/evidence validation, restricted DB role. Migration 0004 applied. PostgreSQL exposed ONLY on 127.0.0.1:15439 for host-network worker; Ollama remains 127.0.0.1:11434. Collector unaffected. 29 unit tests passed / 4 integration tests skipped, synthetic and initial real local inference completed. Synthetic multiple_ads false positive remains a documented limitation. Review-only normalized candidates in telegram_llm_jobs; no updates to loads/outbox. Files and commands: deploy/LOCAL_LLM.md. Runtime secrets /etc/logistics/llm.env not committed.

## File-based batch extraction

Operator requested up to 100 unprocessed ads in one file/inference, separate normalized persistence. Inspected existing worker/schema and server resources. Implemented local_llm_batch.py, replaced worker loop, migration 0005 and volume mount. Original array response omitted 2/3 items in live smoke test; strengthened schema to required ID-keyed objects. Next live batch saved all 3 records from 1 request (139.5s). Larger requests do not yet have verified accuracy or speedup. Conservative UTF-8 byte input budget + output reserve, context32768, limit100, no truncation; first full-limit batch selected31 and is processing. Interrupted jobs replay; good committed jobs excluded. Tests35 passed/4 skipped. No credentials/raw Telegram text committed. See deploy/BATCH_PROCESSING.md for retention, diagnostics and limitations.

## Read-only batch and result audit

Ran aggregate audit via collector container administrative DB connection after normalizer restricted role correctly denied access to baseline parse table; no permissions expanded. Script deploy/audit_llm_results.py. No source text exported. Sample31 completed records,15 unique texts,one source; mixed old/batch/cache outputs. Large31-ad batch still processing at snapshot, no speed/accuracy success claim. 29 records had unsupported fields removed,21 missing normalized weight despite raw weight markers,11 sums without currency; normalizer protects financial use. Host resource pressure observed; no runtime settings changed. Full report batch-quality-audit-2026-09-10.md.

## Independent queue + numbers V2

Inspected current repo/runtime before changes; user approved1–3. Stopped only normalizer; interrupted31-item batch did not produce a final result. Added enqueuer + heartbeat migration0006; initial catchup123+7, no unqueued messages at check. Source numeric matching prevents phone-as-price, recovers explicit unit spans, retains ranges/multiple values for review; no currency guesses. Pending jobs migratedV2, completed baseline preserved. Unit tests56 passed/4 skipped. Read-only31-record numeric comparison weight3→15, price11→6; not ground truth. Matched10-real-ad benchmark uses same source hashes, contexts/options, no application cache, shared host and one fixed-order pass. Batch5=243.99s,10/10 returned so far. Wrapper will choose fastest full10/10 case or fallback3 and restore normalizer; collector/enqueuer never paused. Files/docs: deploy/QUEUE_AND_NUMBERS_V2.md.

## Benchmark completed and runtime verified

Same10 unique short ads from4 sources; size3=176.71s, size5=243.99s, size10=187.31s. All schema-valid10/10. Output field presence varies and many unsupported fields were removed; no ground-truth accuracy claim. Shared host/order/cache caveats documented. Runtime limit3 set by wrapper, normalizer restarted. First production V2 batch saved3 in56.07s; DB check6 completedV2 including cached results. Enqueuer heartbeat3s. Bench input files removed after each call; only manifest IDs/hashes and aggregate metrics committed. Core a11ce0b; final docs in queue-v2-benchmark-results.md.
