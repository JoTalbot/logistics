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

## cgroup capability probe

`cgroup_probe.py` is a read-only diagnostic for the target host. Run it as the same `logistics-agent` identity used by the service:

```bash
sudo -u logistics-agent /opt/logistics-agent/.venv/bin/python /opt/logistics/deploy/remote-agent/cgroup_probe.py
```

The JSON report records cgroup-v2 presence, the agent's own cgroup, required cgroup files, relevant write access, available controllers, enabled subtree controllers, execution identity, systemd/systemd-run availability, and a conservative `task_cgroup_creation_ready` gate. The probe only executes `--version` for local systemd tooling when present. It never creates transient units, modifies cgroups, moves processes, or kills processes.

`target_host_readiness` is a machine-readable prerequisite contract:

- `READY` means cgroup-v2 and `systemd-run` are present and the current identity can access the required cgroup parent. It means **rehearsal prerequisites are present**, not that runtime per-task isolation is implemented.
- `BLOCKED` means the host exposes the expected Linux/cgroup-v2/systemd contour but the current identity lacks a required capability, such as writable cgroup-parent access.
- `UNSUPPORTED` means the required Linux/cgroup-v2/systemd backend is not present.

`target_host_profile=linux_cgroup_v2_systemd` and `task_scope_backend_candidate=systemd-run-scope` identify the current implementation candidate only. They do not authorize mutation or prove that a transient scope can actually be created under the installed service policy.

## Target-host cgroup rehearsal

`cgroup_rehearsal.py` is the next, deliberately opt-in verification step. It is **not** run by normal CI and is not invoked by the remote agent. Run it only on an authorized Linux target host as the dedicated non-root `logistics-agent` identity:

```bash
sudo -u logistics-agent env LOGISTICS_CGROUP_REHEARSAL=1 \
  /opt/logistics-agent/.venv/bin/python /opt/logistics/deploy/remote-agent/cgroup_rehearsal.py
```

The rehearsal asks systemd for a transient scope, starts a real task, creates a deliberately detached session child, verifies that both processes resolve to the same task cgroup, writes `1` to that cgroup's `cgroup.kill`, and verifies that both processes disappear. It refuses to run as root and never falls back to the unsafe `fork/exec -> write PID to cgroup.procs` pattern. Failure to obtain an authorized scope, resolve the task cgroup, observe the detached descendant, or fence both processes is treated as a failed gate rather than silently falling back to weaker behavior.

This rehearsal is destructive only to its own temporary test processes. It does not alter controllers or persistent cgroup configuration. A successful rehearsal is evidence for the target host and identity only; it does not by itself enable runtime per-task containment in `agent.py`.

See `docs/REMOTE_AGENT_CGROUP_DESIGN.md` for the implementation decision gate and verification requirements.

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
