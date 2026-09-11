# Ubuntu Remote Agent

This directory defines the deployment boundary for the future Vercel Android GUI control plane.

## Principle

Install a dedicated `logistics-agent` service on Ubuntu. The service owns local execution and maintains an authenticated outbound control connection to the Vercel application.

Do **not** put SSH private keys, GitHub tokens, provider keys or other credentials in this directory or in Git.

## Bootstrap checklist

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin logistics-agent
sudo install -d -o logistics-agent -g logistics-agent /opt/logistics-agent
sudo install -d -o logistics-agent -g logistics-agent /var/lib/logistics-agent
```

The actual service implementation must be added before enabling a systemd unit. Do not run a placeholder service in production.

## Required capabilities

- outbound HTTPS/WSS to the Vercel control plane;
- authenticated registration and heartbeat;
- task queue with idempotency keys;
- bounded subprocess execution;
- optional PTY sessions;
- stdout/stderr streaming;
- cancellation and timeout handling;
- audit events;
- workspace allowlist;
- privileged-operation approval gate.

## Workspace policy

The first allowed workspace should be the checked-out `logistics` repository. Additional projects must be explicitly registered rather than accepting arbitrary paths from the browser.

## SSH

If the agent needs to access another SSH host, configure that host locally on Ubuntu using a dedicated key/account with least privilege. The Vercel GUI must never receive or store that private key.
