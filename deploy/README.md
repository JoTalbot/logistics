# Telegram collector deployment

Installed at `/opt/logistics` on the OCI host. Runtime files are under `deploy/`.

## Configuration

Run GitHub Actions workflow **Configure Telegram collector** manually. It transfers repository secrets `TG_API_ID` and `TG_API_HASH` to `/etc/logistics/telegram.json` (root, 0600) using a forced-command SSH key. Secrets `LOGISTICS_CONFIG_SSH_KEY` and `LOGISTICS_SSH_KNOWN_HOSTS` hold this restricted key and pinned host keys. Receiver: `/usr/local/sbin/logistics-receive-config`.

Database credentials are generated on the server and stored only in `/etc/logistics/{postgres,collector}.env`. No database ports are published. Do not commit credentials or Telegram sessions.

## One-time login (interactive SSH terminal on the server)

```bash
cd /opt/logistics
docker compose -f deploy/compose.collector.yml run --rm --no-deps collector python /runtime/collector.py --login
```

Enter the account phone number, login code and optional 2FA password locally. Session stored under `/var/lib/logistics/telegram/collector.session`. Never log in concurrently with a running collector; stop it before reauthorization.

## Start after login

```bash
cd /opt/logistics
docker compose -f deploy/compose.collector.yml up -d collector
docker compose -f deploy/compose.collector.yml logs --tail=50 collector
```

Restart policy: unless-stopped. Four default source chats from `logistics.telegram.DEFAULT_CHATS`; 100 messages per source per pass, 60-second interval. Initial collection starts at oldest available history; subsequent passes use durable checkpoints. Flood waits are respected. No outbound posting. Use only sources the account is authorized to access and respect retention/content terms.

## Current verification

Image built for ARM64; PostgreSQL healthy, migrations created 10 public tables. Repository unit tests: 17 passed, 4 database integration tests skipped in standalone run. Live Telegram authorization and ingestion are pending operator login. No claim of successful live collection yet.
