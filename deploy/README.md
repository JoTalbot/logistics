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

Restart policy: unless-stopped. Four default source chats from `logistics.telegram.DEFAULT_CHATS`; 100 messages per source per pass, 60-second interval. Initial collection captures the latest 100 messages per source once, persists the fixed snapshot in /var/lib/logistics/telegram/latest100-v1.json and ingests it oldest-to-newest. Subsequent passes use durable checkpoints and fetch only newer messages, in batches of 100 without skipping bursts. Bootstrap completion persists across restarts; do not delete the state file. Previously collected historical records are retained. Flood waits are respected. No outbound posting. Use only sources the account is authorized to access and respect retention/content terms.

## Current verification

Image built for ARM64; PostgreSQL healthy, migrations created 10 public tables. Repository unit tests: 17 passed, 4 database integration tests skipped in standalone run. Live Telegram authorization and ingestion verified after operator login: 400 messages from all four sources, 10 canonical loads, zero container restarts at the first check. Initial historical backfill is in progress; current-message catch-up not yet verified.

## Latest-100 mode verification

All four sources completed their initial 100-message snapshot. Subsequent incremental pass collected 14 and 3 new messages from two sources and zero from the other two. Tests: 20 passed, 4 integration tests skipped. Zero weight, volume and price tokens are treated as missing values rather than blocking ingestion.

## Local LLM normalization

A separate local-only `normalizer` service now enriches stored messages using installed Ollama qwen2.5:1.5b. Results are review-only in telegram_llm_jobs, not automatic canonical loads. See [LOCAL_LLM.md](LOCAL_LLM.md) for resource limits, queue status, rights/terms, validation and recovery. PostgreSQL now binds 127.0.0.1:15439 for the host-network normalizer; it is not publicly exposed.
