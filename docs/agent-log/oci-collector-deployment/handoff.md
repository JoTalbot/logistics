# OCI collector deployment

Added manual secret-transfer workflow and independent Docker Compose runtime. Restricted forced-command SSH key; host key pinned; runtime secrets excluded from Git; database has no published ports. PostgreSQL migrations checked, unit tests 17 passed / 4 skipped. Live Telegram access pending interactive operator login. Follow deploy/README.md. This deployment does not alter publication adapters. Existing telegram-load-ingestion-v1 skill was used.

## Live verification

Operator completed Telegram login and started collector. Both containers running; PostgreSQL healthy; restart policy unless-stopped, zero restarts. First live check: 100 persisted messages from each of four sources (400 total), 10 canonical loads. Historical backfill begins at oldest available messages; current-message catch-up not yet verified. No raw messages or credentials were printed during verification.
