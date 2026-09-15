# V39 Rollback Evidence

The Telegram ingestion integration test injects a failure at commit time after all ingestion statements have executed. The connection context rolls the transaction back, and the test verifies that source message, canonical load, outbox event, and source checkpoint state are absent afterward.

This proves the repository transaction boundary under the injected failure model. It does not prove production infrastructure readiness or external provider authorization.
