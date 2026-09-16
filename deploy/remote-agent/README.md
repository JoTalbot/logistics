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

Use `install.sh` to create the systemd service. The generated unit runs as the dedicated `logistics-agent` user, uses `NoNewPrivileges`, `ProtectSystem`, `ProtectHome`, and a service-level `KillMode=control-group` boundary. The unit also enables cgroup delegation for a future per-task supervisor.

## Lease/process fencing

Leased control tasks use a bounded heartbeat watchdog. A 401/409 lease rejection fences the local task, terminates its POSIX process group, waits for the subprocess, and suppresses stale event/completion writes. Normal `/v1/exec` timeouts use the same process-group termination path.

The POSIX process-group boundary is intentionally not described as a complete containment boundary: a command that deliberately creates an independent session/process group can escape `killpg`. The systemd service cgroup is therefore retained as the service-level safety net, while true per-task cgroup containment remains a separate hardening step. Do not claim lease fencing as an absolute guarantee against arbitrary daemonization until per-task cgroup supervision is deployed and tested.

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
