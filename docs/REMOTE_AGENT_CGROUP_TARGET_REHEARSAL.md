# Remote-agent cgroup target-host rehearsal runbook

## Purpose

This runbook defines the authorized target-host procedure for validating the per-task cgroup hardening gate before any runtime enforcement is enabled.

The rehearsal is deliberately destructive **only inside its disposable transient systemd scope**. It must be executed on the intended Linux target host under the dedicated `logistics-agent` identity. It must not be run as root and must not be treated as a substitute for the repository CI suite.

## Preconditions

- Linux host with cgroup v2 mounted at `/sys/fs/cgroup`.
- `/usr/bin/systemd-run` and `/usr/bin/systemctl` available.
- The actual service identity is the dedicated non-root `logistics-agent` user.
- The installed agent checkout contains:
  - `deploy/remote-agent/cgroup_probe.py`
  - `deploy/remote-agent/cgroup_rehearsal.py`
- The host is authorized for a destructive rehearsal of a disposable transient systemd scope.
- No production task should depend on the host during the rehearsal window.

The rehearsal must not be run as root. Root execution would validate a different privilege model and therefore would not prove the deployment contract.

## Step 1 — Capture read-only capability evidence

Run as `logistics-agent`:

```bash
cd /opt/logistics
auto_probe=deploy/remote-agent/cgroup_probe.py
python3 "$auto_probe"
```

Record the machine-readable output. The expected target-host state for the selected model is `READY`.

`READY` is only a capability gate. It is not proof that a real task boundary works.

## Step 2 — Execute the destructive rehearsal

Create an evidence destination writable by `logistics-agent`, for example:

```bash
mkdir -p /var/lib/logistics-agent/evidence
```

Then run:

```bash
cd /opt/logistics
export LOGISTICS_CGROUP_REHEARSAL=1
export LOGISTICS_CGROUP_EVIDENCE_PATH=/var/lib/logistics-agent/evidence/cgroup-rehearsal.json
python3 deploy/remote-agent/cgroup_rehearsal.py
```

The script creates a disposable transient systemd scope containing a task process and a deliberately detached descendant. It verifies that both processes resolve to the same cgroup, writes `1` to that cgroup's `cgroup.kill`, verifies that both processes disappear, and confirms transient-scope cleanup.

The expected process exit status is `0` and the terminal result is `PASS`.

## Step 3 — Validate evidence

The JSON artifact must contain, at minimum:

- `schema_version`
- `timestamp_utc`
- `host`
- `execution_identity`
- `uid`, `euid`, `gid`, `egid`
- `kernel`
- cgroup-v2 and `systemd-run` facts
- `readiness.target_host_readiness`
- transient scope unit
- task PID and detached descendant PID
- task and descendant cgroup paths
- `same_cgroup_before_fence=true`
- `cgroup_kill_write=true`
- both processes alive before fencing
- both processes absent after fencing
- `cleanup=true`
- `result=PASS`

The acceptance condition is **all required properties**, not merely a successful command exit or `READY` probe.

## Step 4 — Preserve provenance

Copy the evidence artifact into the approved operational evidence store together with:

- target host identity;
- execution identity;
- repository commit SHA installed on the target;
- timestamp;
- exact rehearsal command;
- probe output;
- rehearsal JSON artifact;
- any systemd error output if the rehearsal fails.

Do not edit a successful evidence artifact after capture. If metadata is missing, rerun the rehearsal rather than rewriting the observation.

## Failure handling

The following outcomes are blocking and must leave runtime per-task cgroup enforcement disabled:

- `NOT_OPTED_IN`
- `ROOT_REFUSED`
- cgroup v2 unavailable
- `SYSTEMD_RUN_UNAVAILABLE`
- `READINESS_BLOCKED`
- scope creation failure
- task or descendant marker failure
- unresolved cgroup
- descendant in a different cgroup
- `cgroup.kill` unavailable or not writable
- task survives fencing
- detached descendant survives fencing
- transient scope cleanup cannot be confirmed

There is no post-spawn PID-move fallback. Such a fallback has a pre-membership race and does not satisfy the containment contract.

## Promotion gate

A successful rehearsal authorizes **evidence that the target host can support the selected containment model**. It does not itself activate runtime enforcement.

Before promotion to runtime enforcement, the repository must add and pass implementation-specific coverage for:

1. task-boundary creation;
2. normal completion;
3. timeout fencing;
4. 401/409 lease fencing;
5. forked descendants;
6. detached descendants;
7. restart with an active task;
8. cleanup failure visibility;
9. stale lifecycle-write prevention after fencing;
10. preservation of service-level `KillMode=control-group` containment;
11. CI, Compose E2E, and Backup Restore regression suites.

Until that separate promotion change is merged and verified, the active production mechanisms remain POSIX process-group fencing plus service-level systemd containment.

## Safety boundary

This procedure only validates process-lifetime containment for an already-authorized task. It does not grant business permissions and must not be used to bypass provider protections, access controls, publication restrictions, contact permissions, negotiation controls, booking controls, or financial safeguards.
