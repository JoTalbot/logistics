# Remote agent

The remote agent is a small, least-privilege worker that polls the logistics control plane for leased tasks and reports lifecycle events. It is intentionally separate from the control-plane service and is expected to run under the dedicated non-root `logistics-agent` identity.

## Install

Run the installer from the repository checkout on the target host:

```bash
sudo ./deploy/remote-agent/install.sh
```

The installer:

- creates `/opt/logistics-agent` and its Python virtual environment;
- installs the agent runtime as `/opt/logistics-agent/agent.py`;
- installs the systemd unit as `logistics-remote-agent.service`;
- runs the service as `logistics-agent` with `NoNewPrivileges=true`, `ProtectSystem=strict`, `ProtectHome=true`, and `KillMode=control-group`;
- sets `Delegate=yes` and a bounded `TasksMax=512` as preparation for a future per-task cgroup boundary;
- keeps the listener bound to `127.0.0.1:8787`.

The installer does **not** copy the cgroup probe, gate, or rehearsal helpers into `/opt/logistics-agent`. Those verification tools remain in the repository under `deploy/remote-agent/` and should be run from the repository checkout.

## Credentials

The agent uses separate credentials for bootstrap/enrollment and ordinary control-plane requests:

- `CONTROL_TOKEN` is used only for enrollment/heartbeat bootstrap;
- `CONTROL_AGENT_TOKEN` is the agent-scoped credential used for ordinary polling, event reporting, and task completion.

The agent does not fall back to the bootstrap token for ordinary task operations. A stale or revoked agent credential causes the local lease to be treated as lost and the running task process group to be terminated before stale lifecycle writes are attempted.

## Cgroup readiness probe

The read-only readiness probe can be run on an authorized target host without enabling destructive rehearsal:

```bash
sudo -u logistics-agent /opt/logistics-agent/.venv/bin/python /opt/logistics/deploy/remote-agent/cgroup_probe.py
```

The probe reports Linux/cgroup-v2 availability, controller and filesystem capabilities, systemd-run availability, execution identity, and a conservative target-host readiness state. `READY` is required before the destructive rehearsal can be attempted.

## Target-host cgroup rehearsal

`cgroup_rehearsal.py` is the next, deliberately opt-in verification step. It is **not** run by normal CI and is not invoked by the remote agent. Run it only on an authorized Linux target host as the dedicated non-root `logistics-agent` identity:

```bash
sudo -u logistics-agent env LOGISTICS_CGROUP_REHEARSAL=1 \
  /opt/logistics-agent/.venv/bin/python /opt/logistics/deploy/remote-agent/cgroup_rehearsal.py
```

The rehearsal creates a transient systemd scope, starts a task that creates a real detached `setsid()` descendant, verifies that both processes are in the same cgroup, writes `1` to `cgroup.kill`, verifies that both processes are gone, and cleans up the transient scope. It deliberately refuses the unsafe post-spawn PID-move fallback.

A successful rehearsal is target-host evidence only. It does **not** by itself activate per-task cgroup containment in the remote-agent runtime.

### Machine-readable evidence

For an auditable target-host result, set `LOGISTICS_CGROUP_EVIDENCE_PATH` to a writable path owned by the agent identity:

```bash
sudo -u logistics-agent env \
  LOGISTICS_CGROUP_REHEARSAL=1 \
  LOGISTICS_CGROUP_EVIDENCE_PATH=/var/lib/logistics-agent/cgroup-rehearsal.json \
  /opt/logistics-agent/.venv/bin/python /opt/logistics/deploy/remote-agent/cgroup_rehearsal.py
```

The evidence artifact records the execution identity, cgroup-v2/systemd capabilities, transient scope, task and detached-descendant PIDs, cgroup membership, fence result, liveness checks, and cleanup result. See `docs/REMOTE_AGENT_CGROUP_EVIDENCE.md` for the acceptance contract.

## Current isolation boundary

The current runtime uses POSIX process-group fencing plus the systemd service cgroup as a service-level safety net. It does **not** yet claim one cgroup per leased task. Per-task cgroup containment remains gated on an authorized target-host rehearsal, architecture selection, lifecycle/regression coverage, and production evidence.

The server-side lease and credential-generation fence remains authoritative. The target-host cgroup mechanism is an execution containment layer, not a replacement for server-side authorization.
