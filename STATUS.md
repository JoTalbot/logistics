# Project Status — AI Logistics OS

CURRENT_STEP: V43.13 — Direct cgroup rehearsal identity hardening
STATUS: blocked
UPDATED: 2026-09-17
AGENT: chatgpt-logistics-20260917
MACHINE: GitHub-connected execution environment
SCOPE: Continue V43.12 cgroup hardening, audit direct rehearsal invocation paths, and preserve fail-closed activation boundaries.
FILES: deploy/remote-agent/cgroup_rehearsal.py; deploy/remote-agent/cgroup_gate.py; tests/test_remote_agent_cgroup_gate.py; STATUS.md; docs/agent-log/chatgpt-logistics-20260917/research-20260917.md
RESEARCH: Linux kernel cgroup-v2 documentation; systemd resource-control documentation; repository cgroup design/evidence contract; existing remote-agent and remote-control implementation.
DECISIONS: Runtime per-task cgroup enforcement remains disabled. The destructive target-host rehearsal must be explicitly opted in, run non-root, report the dedicated `logistics-agent` execution identity, report READY capabilities, contain a deliberately detached descendant, fence through `cgroup.kill`, and clean up successfully. Post-spawn PID migration is not accepted as containment evidence.

## Verification state

**SOFTWARE CONTOUR: GREEN AS RECORDED** — the latest verified application-bearing change remains `bb9bb7f449eb73af0b376fe23d34162c9e98d5fd`. Subsequent regression coverage reaches `b881ecce78896fc2b20770d40e99e671bd8d5ba8`, including direct reenrollment fencing and explicit Bearer authentication.

**CURRENT TEST EVIDENCE: GREEN AS RECORDED** — `b881ecce78896fc2b20770d40e99e671bd8d5ba8` is documented as having successful `test`, `compose-e2e`, and `backup-restore-e2e` runs (`35159690286`, `35159690256`, `35159690279`). This execution surface has not independently rerun those workflows, so they are not presented as fresh results.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is covered by regression testing; credential-generation lease fencing is enforced; deterministic lock fencing is covered; direct bootstrap reenrollment cancels active running leases; agent credential authentication requires an explicit `Bearer` scheme; local agent execution fences the POSIX process group on timeout/lease loss.

**CURRENT DESIGN STATE:** read-only cgroup capability probe, target-host evidence contract, opt-in transient-scope rehearsal, and a fail-closed gate are implemented. The gate and the rehearsal itself now require the effective execution identity to be exactly `logistics-agent`. Runtime per-task cgroup isolation is not enabled.

## Latest hardening

- `7fc29710229fbb38d0ccc6243aca28ebd193a51f`: direct rehearsal invocation now independently rejects an unexpected execution identity, so the gate cannot be bypassed by invoking the rehearsal script directly.
- `1fc95b8d8f5f6c9092d6ca33fcc2af07b0b8975d`: regression coverage verifies direct invocation is refused for the wrong identity.
- `3a12b3d3c4027b0a466d57453be1e5478d929aa7`: rehearsal gate rejects unexpected execution identities before destructive execution.
- `adfbe65f2802e9ece9540a6ff5690149a0067c6c`: regression tests cover the dedicated-identity boundary.

## CI surface

The main CI workflow runs the read-only cgroup capability probe before package installation and executes the repository pytest suite. The new identity regression is therefore part of the normal unit-test surface, while the destructive rehearsal remains intentionally excluded from CI.

## External production gates

1. Backup/restore rehearsal: GREEN IN CI / PENDING TARGET INFRASTRUCTURE.
2. Hardened Compose end-to-end rehearsal: GREEN IN CI / PENDING TARGET INFRASTRUCTURE.
3. Lardi access/mapping: BLOCKED BY PROVIDER; no protection bypass is attempted.
4. Publication/contact permissions: PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION.
5. Real booked/delivered outcomes: PENDING OPERATIONAL DATA.
6. Vercel main deployment integration: BLOCKED BY VERCEL ACCOUNT STATUS; latest checked commit status reports `Vercel = failure`.
7. Authorized Telegram credentials/source access: PENDING EXTERNAL AUTHORIZATION.
8. Target-host cgroup rehearsal: BLOCKED until an authorized non-root `logistics-agent` target host is available.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Runtime cgroup enforcement must remain fail-closed until target-host rehearsal proves containment of a detached descendant with `cgroup.kill` and successful cleanup.

## Handoff

IN_PROGRESS: target-host cgroup enforcement gate and external production-readiness gates.
NEXT: execute `deploy/remote-agent/cgroup_gate.py` on an authorized target host as the dedicated `logistics-agent` identity, capture the machine-readable evidence artifact, review every acceptance field, and only then design/implement runtime per-task cgroup enforcement if the gate passes.
BLOCKERS: no authorized target host in the current execution surface; Vercel account block; provider access/mapping; external publication/contact authorization; authorized Telegram source access; target production backup/restore rehearsal; real commercial outcome telemetry.

LOG: `docs/agent-log/chatgpt-logistics-20260917/research-20260917.md`
