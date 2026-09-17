# Project Status — AI Logistics OS

CURRENT_STEP: V43.16 — Target-host cgroup enforcement gate
STATUS: blocked
UPDATED: 2026-09-17
AGENT: chatgpt-logistics-20260917
MACHINE: GitHub-connected execution environment
SCOPE: Continue V43.15 cgroup hardening after fresh CI verification; preserve fail-closed activation boundaries and separate software verification from target-host containment evidence.
FILES: backend/logistics/remote_control.py; tests/test_remote_control.py; deploy/remote-agent/cgroup_rehearsal.py; deploy/remote-agent/cgroup_gate.py; tests/test_remote_agent_cgroup_gate.py; tests/test_remote_agent_cgroup_rehearsal_static.py; STATUS.md; docs/agent-log/chatgpt-logistics-20260917/command-policy-audit-20260917.md
RESEARCH: Linux kernel cgroup-v2 documentation; systemd resource-control documentation; repository cgroup design/evidence contract; existing remote-agent and remote-control implementation.
DECISIONS: Runtime per-task cgroup enforcement remains disabled. The destructive target-host rehearsal must be explicitly opted in, run non-root, report the dedicated `logistics-agent` execution identity, report READY capabilities, contain a deliberately detached descendant, fence through `cgroup.kill`, and clean up successfully. Post-spawn PID migration is not accepted as containment evidence. Autonomous Python tooling is argument-bounded rather than prefix-trusted.

## Verification state

**SOFTWARE CONTOUR: GREEN / FRESH CI VERIFIED** — commit `9738c1c5e105c0afbf22902c687a6d19082ecb62` passed CI run #638. The completed test job passed the cgroup capability probe, dependency checks, `pip-audit`, SQL migrations, unit/integration tests, V20 commercial baseline replay, hardened Compose contract validation, release smoke checks, and hardened API image build.

**COMPOSE E2E: GREEN / FRESH** — Compose E2E run #210 for commit `9738c1c5e105c0afbf22902c687a6d19082ecb62` completed successfully, including the hardened Compose stack rehearsal.

**BACKUP/RESTORE E2E: GREEN / FRESH** — Backup Restore E2E run #208 for commit `9738c1c5e105c0afbf22902c687a6d19082ecb62` completed successfully, providing fresh CI evidence for the backup/restore rehearsal on the current main commit.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is covered by regression testing; credential-generation lease fencing is enforced; deterministic lock fencing is covered; direct bootstrap reenrollment cancels active running leases; agent credential authentication requires an explicit `Bearer` scheme; local agent execution fences the POSIX process group on timeout/lease loss. The control-plane AUTO classifier rejects Python path traversal, absolute paths, arbitrary pytest configuration/plugin selectors, and unsupported compiler flags.

**CURRENT DESIGN STATE:** read-only cgroup capability probe, target-host evidence contract, opt-in transient-scope rehearsal, and a fail-closed gate are implemented. The gate and the rehearsal require the effective execution identity to be exactly `logistics-agent`. Static regression coverage protects direct rehearsal identity/readiness ordering, absence of post-spawn cgroup migration, cgroup.kill fencing, process-death verification, and cleanup verification. Runtime per-task cgroup isolation is not enabled.

## Latest hardening

- `9738c1c5e105c0afbf22902c687a6d19082ecb62`: updated status after fresh verification; CI, Compose E2E, and Backup Restore E2E subsequently passed on the same commit.
- `24e3b85055e6ded38ec60327af57321fef6c32b4`: aligned the static cgroup rehearsal identity guard with the implementation; fresh CI subsequently passed.
- `5ee4cfa3914d76eb49004964e3e2d1f25e947c77`: added regression coverage for autonomous Python path/configuration boundaries.
- `b8b930403a013cfed42c13cb37d4b72b2a46d449`: tightened `_approval()` so AUTO Python execution validates all arguments instead of trusting only the module prefix.
- `daa5441e73efd2ee17f8ab71f6547c0ecb291f67`: recorded the command-policy audit and its residual symlink limitation.
- `044d23ce86e9ec6b454d2a4d3ffba95dee42ae8c8`: added static regression coverage for direct rehearsal safety invariants.
- `7fc29710229fbb38d0ccc6243aca28ebd193a51f`: direct rehearsal invocation independently rejects an unexpected execution identity.
- `1fc95b8d8f5f6c9092d6ca33fcc2af07b0b8975d`: regression coverage verifies direct invocation is refused for the wrong identity.
- `3a12b3d3c4027b0a466d57453be1e5478d929aa7`: rehearsal gate rejects unexpected execution identities before destructive execution.

## CI surface

The main CI workflow runs the read-only cgroup capability probe before package installation and executes the repository pytest suite. The new command-policy tests are part of the normal unit-test surface, while the destructive cgroup rehearsal remains intentionally excluded from CI. Fresh CI #638 is the current software verification evidence.

## External production gates

1. Backup/restore rehearsal: GREEN IN CI / PENDING TARGET INFRASTRUCTURE.
2. Hardened Compose end-to-end rehearsal: GREEN IN CI / PENDING TARGET INFRASTRUCTURE.
3. Lardi access/mapping: BLOCKED BY PROVIDER; no protection bypass is attempted.
4. Publication/contact permissions: PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION.
5. Real booked/delivered outcomes: PENDING OPERATIONAL DATA.
6. Vercel main deployment integration: BLOCKED BY VERCEL ACCOUNT STATUS; current commit has a Vercel failure status pointing to the account deployment-block guidance.
7. Authorized Telegram credentials/source access: PENDING EXTERNAL AUTHORIZATION.
8. Target-host cgroup rehearsal: BLOCKED until an authorized non-root `logistics-agent` target host is available.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Runtime cgroup enforcement must remain fail-closed until target-host rehearsal proves containment of a detached descendant with `cgroup.kill` and successful cleanup.

## Handoff

IN_PROGRESS: target-host cgroup enforcement gate and external production-readiness gates.
NEXT: obtain an authorized target host, run `deploy/remote-agent/cgroup_gate.py` as the dedicated non-root `logistics-agent` identity with explicit rehearsal opt-in, capture the machine-readable evidence artifact, review every acceptance field, and only then design/implement runtime per-task cgroup enforcement if the gate passes. After runtime implementation, require lifecycle tests for restart, timeout, lease loss, cleanup, and detached descendants plus normal CI, Compose E2E, and Backup Restore E2E verification.
BLOCKERS: no authorized target host in the current execution surface; Vercel account block; provider access/mapping; external publication/contact authorization; authorized Telegram source access; target production backup/restore rehearsal; real commercial outcome telemetry.

LOG: `docs/agent-log/chatgpt-logistics-20260917/research-20260917.md`; `docs/agent-log/chatgpt-logistics-20260917/command-policy-audit-20260917.md`
