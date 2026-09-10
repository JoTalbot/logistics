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
