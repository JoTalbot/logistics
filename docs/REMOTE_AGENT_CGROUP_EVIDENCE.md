# Remote-agent cgroup target-host evidence contract

## Purpose

This document defines the evidence artifact produced by an authorized target-host rehearsal. It is a verification record, not a runtime configuration and not a substitute for provider, infrastructure, or operator authorization.

The artifact must describe one concrete rehearsal run and must be sufficient to answer five questions without inference:

1. Which host and execution identity performed the rehearsal?
2. Which cgroup-v2/systemd capability was observed before mutation?
3. Which transient scope contained the real task and detached descendant?
4. Did `cgroup.kill` terminate both processes?
5. Was the temporary scope cleaned up without leaving the runtime enabled?

## Evidence fields

A future machine-readable JSON artifact should contain these top-level fields:

- `schema_version`: stable evidence schema version.
- `timestamp_utc`: UTC timestamp for the rehearsal start.
- `host`: non-secret host identity sufficient to distinguish the target machine; do not include credentials or private keys.
- `execution_identity`: effective account used for the rehearsal; expected value is the dedicated non-root `logistics-agent` identity.
- `uid`, `euid`, `gid`, `egid`: numeric execution identity values.
- `kernel`: kernel/profile information relevant to cgroup-v2 support.
- `cgroup_v2_mount`: boolean proving the cgroup-v2 hierarchy was observed.
- `systemd_run`: path and version observed before the rehearsal.
- `readiness`: the complete read-only capability result, including `target_host_readiness`, `cgroup_kill_available`, `cgroup_kill_writable`, parent access, controllers and backend candidate.
- `scope`: transient unit name and the observed task cgroup path.
- `task_pid`: PID of the real task used for the rehearsal.
- `detached_descendant_pid`: PID of the deliberately detached-session child.
- `task_cgroup`: cgroup path resolved from `/proc/<pid>/cgroup` before fencing.
- `detached_descendant_cgroup`: cgroup path resolved from `/proc/<pid>/cgroup` before fencing.
- `same_cgroup_before_fence`: boolean; must be true.
- `cgroup_kill_write`: boolean; must be true.
- `task_alive_before_fence`: boolean; must be true.
- `detached_descendant_alive_before_fence`: boolean; must be true.
- `task_alive_after_fence`: boolean; must be false.
- `detached_descendant_alive_after_fence`: boolean; must be false.
- `cleanup`: whether the transient scope was collected and no rehearsal process remained.
- `result`: `PASS` or a specific failure category.

PIDs and transient unit names are evidence for the single rehearsal instance. They must not be treated as stable identifiers across runs.

## Acceptance criteria

A rehearsal is accepted only when all of the following are true:

- execution is non-root and uses the intended dedicated identity;
- cgroup v2 and the expected systemd backend are present;
- read-only readiness reports `READY`;
- a transient task scope is actually created under the service policy;
- the real task has a resolvable cgroup;
- a deliberately detached-session descendant remains in that exact cgroup;
- `cgroup.kill` is writable by the rehearsal identity;
- writing `1` to `cgroup.kill` terminates both the task and detached descendant;
- no process-group-only fallback is used;
- the temporary scope is cleaned up;
- the evidence artifact is internally consistent.

`READY` without a successful destructive rehearsal is not sufficient evidence of containment.

## Failure handling

Failures are fail-closed. A missing permission, unauthorized transient scope, unresolved cgroup, escaped descendant, failed `cgroup.kill`, surviving process, or incomplete cleanup must produce a non-pass result and must not enable runtime per-task containment.

Do not weaken the test to make an unsupported host pass. In particular, do not replace cgroup fencing with `killpg`, a post-spawn PID move, or another weaker mechanism and label the result as equivalent evidence.

## Runtime activation rule

This evidence contract does not activate per-task cgroup enforcement. Runtime implementation remains a separate change requiring:

1. architecture selection (`systemd-run --scope` or an explicitly justified delegated cgroup-v2 backend);
2. target-host rehearsal evidence satisfying this contract;
3. implementation-specific lifecycle tests, including restart, timeout, lease loss, cleanup and detached descendants;
4. regression verification across the normal CI, Compose E2E and Backup Restore E2E contours.

Until those gates pass, the remote agent must retain its existing process-group and service-level cgroup behavior.
