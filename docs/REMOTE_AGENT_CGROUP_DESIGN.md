# Remote-agent per-task cgroup design

## Purpose

This document defines the next hardening boundary for the Ubuntu remote agent: ensuring that a leased task and every descendant process remain inside a task-specific kernel cgroup until the task is terminated and its cgroup is cleaned up.

The current agent already creates a POSIX session/process group and kills that process group on lease loss or timeout. The systemd service also uses `KillMode=control-group` as a service-level safety net. Those mechanisms are intentionally retained; this document does not reinterpret them as per-task cgroup containment.

## Current repository evidence

- `deploy/remote-agent/install.sh` installs the agent as the dedicated `logistics-agent` user.
- The systemd unit uses `KillMode=control-group`, `TasksMax=512`, and `Delegate=yes`.
- `Delegate=yes` is preparation for a child cgroup hierarchy; it does not itself create one cgroup per task.
- `deploy/remote-agent/agent.py` starts commands in a new POSIX session and terminates the process group on lease loss or timeout.
- No `systemd-run`/scope implementation or direct cgroup filesystem task lifecycle was found in the repository search.
- `deploy/remote-agent/cgroup_probe.py` provides a read-only host capability probe; it reports cgroup-v2 files, controller visibility, relevant write access, and execution identity without mutating the host.
- `deploy/remote-agent/cgroup_rehearsal.py` is an opt-in target-host rehearsal. It exercises a systemd transient scope and real detached descendant fencing, but it does not enable runtime enforcement in the agent.
- `tests/test_remote_agent_systemd.py` deliberately checks that documentation does not overclaim per-task cgroup isolation.

## Required semantics

A future implementation is acceptable only if all of the following are true:

1. **One task, one containment boundary.** Every process created by the task starts in the task cgroup.
2. **Descendant retention.** Forked, exec'd, and deliberately detached descendants remain in that cgroup unless the kernel/system manager explicitly moves them.
3. **Lease fencing.** Server-side credential-generation/lease fencing remains authoritative. A local cgroup kill is a consequence of lost authority, not a replacement for server authorization.
4. **Kill-before-write.** On lease loss or timeout, the task cgroup is terminated before any lifecycle event or completion write can describe a successful/still-running task.
5. **Cleanup.** The task cgroup is removed after all processes exit. Failure to clean it up must be observable and must not silently recycle the same boundary for another task.
6. **Agent restart safety.** Restarting the service must not leave an orphan task cgroup that can later be mistaken for a newly leased task.
7. **Fail closed.** If a task-specific containment boundary cannot be created and verified, the task must not be executed under the stronger containment policy.
8. **No privilege expansion.** The implementation must work with the dedicated `logistics-agent` identity and the delegated subtree granted by the service manager; it must not require a general-purpose root shell from task execution.
9. **Bounded resource use.** The existing service-level `TasksMax=512` remains in force. Per-task limits must not make aggregate process limits unbounded.
10. **Cross-platform clarity.** Linux/cgroup-v2 behavior is the supported hardening target. The existing POSIX process-group fallback remains a separate mechanism and must not be described as equivalent containment.

## Candidate implementation models

### Model A: per-task systemd scope

A supervisor asks systemd to create a transient scope for each task and starts the command in that scope. This gives a system-manager-owned lifecycle and naturally groups descendants.

**Open deployment requirement:** the service user must be authorized to create and control the scopes it owns. `Delegate=yes` alone is not evidence that arbitrary scope creation is permitted. The installer must therefore probe the actual supported systemd/user-manager model before enabling this path.

### Model B: delegated cgroup-v2 filesystem

The agent creates a child cgroup below its delegated service subtree, moves the task leader into it, and starts the command so descendants inherit membership. Termination writes the appropriate PID(s) to `cgroup.kill` where supported, followed by cleanup after the cgroup becomes empty.

**Open deployment requirement:** the delegated subtree must expose the required controller/filesystem operations to `logistics-agent`. File ownership, controller availability, `cgroup.subtree_control`, and kernel support must be checked on the target host. A directory that merely exists is not sufficient evidence of containment.

**Important spawn invariant:** a naive `fork/exec -> write PID to cgroup.procs` sequence does **not** satisfy the one-task/one-boundary requirement. There is a race window before the leader is moved during which it can fork descendants in the parent cgroup; those descendants would not inherit the eventual task boundary. Model B therefore requires a spawn primitive or synchronization design that closes this pre-membership window, or it must remain disabled. A post-spawn PID move alone is insufficient evidence of containment.

## Decision gate

Do **not** select Model A or B solely from static configuration. Before runtime implementation, the deployment contract must establish:

- cgroup v2 is active;
- the service's delegated subtree is writable by `logistics-agent` for the operations actually required;
- the selected lifecycle API can create, terminate, inspect, and clean a task boundary without root escalation;
- descendants remain in the boundary across fork/exec and intentional session detachment;
- failure of creation or cleanup has a deterministic fail-closed behavior.

The read-only `deploy/remote-agent/cgroup_probe.py` can be run on a target host before enforcement is enabled. It reports facts only; it does not create cgroups, move processes, enable controllers, or kill anything. Its output is therefore diagnostic evidence rather than proof that the full containment lifecycle works.

The opt-in `deploy/remote-agent/cgroup_rehearsal.py` is the first executable target-host gate for Model A. It must be run explicitly as `logistics-agent`; it requests a transient systemd scope, creates a real detached descendant, verifies shared cgroup membership, and fences the entire scope through `cgroup.kill`. A successful rehearsal is target-host evidence, not runtime enforcement. If the service identity cannot create the scope or access the resulting cgroup as required, the rehearsal fails rather than falling back to a weaker spawn model.

## Verification plan

The implementation should add deterministic tests for:

- capability detection and fail-closed behavior;
- task boundary creation and cleanup;
- normal command completion;
- timeout termination;
- 401/409 lease fencing;
- forked child termination;
- detached-session child termination;
- agent restart with an active task;
- cleanup failure visibility;
- prevention of stale lifecycle writes after cgroup fencing;
- preservation of the service-level `KillMode=control-group` boundary.

At least one Linux integration rehearsal must create a real descendant process, deliberately detach it from the task's POSIX session, fence the task, and verify that the descendant is gone before the task lifecycle is considered fenced. A mocked `killpg()` test alone cannot prove this property. The new opt-in rehearsal provides this check for the systemd-scope model, but it still requires execution on the actual target host under the actual service identity.

## Non-goals

This hardening does not grant the remote agent new business permissions. It does not bypass provider protections, publish listings, contact counterparties, negotiate prices, book transport, or perform financial actions. It only constrains the lifetime of an already-authorized remote task.

## Status

Current state: **capability probe and opt-in target-host rehearsal implemented; runtime per-task cgroup isolation not yet implemented**.

The existing POSIX process-group fencing and systemd service-level containment remain the active mechanisms until the target-host rehearsal passes and the selected lifecycle model is promoted through a separate runtime-enforcement change with cleanup, restart, failure, and stale-write coverage.
