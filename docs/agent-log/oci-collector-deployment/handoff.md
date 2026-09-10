# OCI collector deployment

Added manual secret-transfer workflow and independent Docker Compose runtime. Restricted forced-command SSH key; host key pinned; runtime secrets excluded from Git; database has no published ports. PostgreSQL migrations checked, unit tests 17 passed / 4 skipped. Live Telegram access pending interactive operator login. Follow deploy/README.md. This deployment does not alter publication adapters. Existing telegram-load-ingestion-v1 skill was used.
