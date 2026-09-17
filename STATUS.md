# Project Status — AI Logistics OS

CURRENT_STEP: V43.17 — Remote-agent startup fail-closed hardening
STATUS: blocked
UPDATED: 2026-09-17
AGENT: chatgpt-logistics-20260917
MACHINE: GitHub-connected execution environment
SCOPE: Continue remote-agent production hardening after fresh CI verification; preserve fail-closed activation boundaries and separate software verification from target-host containment evidence.
FILES: deploy/remote-agent/install.sh; tests/test_remote_agent_systemd.py; deploy/remote-agent/cgroup_rehearsal.py; deploy/remote-agent/cgroup_gate.py; tests/test_remote_agent_cgroup_gate.py; tests/test_remote_agent_cgroup_rehearsal_static.py; backend/logistics/remote_control.py; tests/test_remote_control.py; STATUS.md
RESEARCH: Linux kernel cgroup-v2 documentation; systemd resource-control documentation; repository cgroup design/evidence contract; existing remote-agent and remote-control implementation.
DECISIONS: Runtime per-task cgroup enforcement remains disabled. The destructive target-host rehearsal must be explicitly opted in, run non-root, report the dedicated `logistics-agent` execution identity, report READY capabilities, contain a deliberately detached descendant, fence through `cgroup.kill`, and clean up successfully. Post-spawn PID migration is not accepted as containment evidence. Autonomous Python tooling is argument-bounded rather than prefix-trusted. Remote-agent installation now fails closed when known secret or control-plane placeholders remain configured.

## Verification state

**SOFTWARE CONTOUR: GREEN / FRESH CI VERIFIED** — commit `07c7cde25ef49806a7815aeed043457d83bac6f8` passed CI #642. The completed test job passed the cgroup capability probe, dependency checks, `pip-audit`, SQL migrations, unit/integration tests, V20 commercial baseline replay, hardened Compose contract validation, release smoke checks, and hardened API image build.

**BACKUP/RESTORE E2E: GREEN / FRESH** — Backup Restore E2E #212 for commit `07c7cde25ef49806a7815aeed043457d83bac6f8` completed successfully, including disposable backup creation, restore, and schema/marker verification.

**REMOTE-AGENT STARTUP HARDENING: GREEN / CI VERIFIED** — `install.sh` now refuses to start the service when the protected environment still contains known placeholders for agent authentication, AI gateway configuration, production control-plane URL, or bootstrap control-plane token. The service remains installable while unconfigured, but startup is fail-closed until configuration is completed.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is covered by regression testing; credential-generation lease fencing is enforced; deterministic lock fencing is covered; direct bootstrap reenrollment cancels active running leases; agent credential authentication requires an explicit `Bearer` scheme; local agent execution fences the POSIX process group on timeout/lease loss. The control-plane AUTO classifier rejects Python path traversal, absolute paths, arbitrary pytest configuration/plugin selectors, and unsupported compiler flags.

**CURRENT DESIGN STATE:** read-only cgroup capability probe, target-host evidence contract, opt-in transient-scope rehearsal, and a fail-closed gate are implemented. The gate and the rehearsal require the effective execution identity to be exactly `logistics-agent`. Static regression coverage protects direct rehearsal identity/readiness ordering, absence of post-spawn cgroup migration, cgroup.kill fencing, process-death verification, and cleanup verification. Runtime per-task cgroup isolation is not enabled.

## Latest hardening

- `07c7cde25ef49806a7815aeed043457d83bac6f8`: removed an unused test placeholder variable; CI #642 and Backup Restore E2E #212 subsequently passed.
- `cb26594c9a3c5a16909cf65f0b695af1192a819c`: added regression coverage requiring install-time fail-closed handling of control-plane placeholders.
- `ec4747ff4852122551471139904d3dc9124a4bfe`: tightened remote-agent installation so known secret/control-plane placeholders prevent service startup.
- `9738c1c5e105c0afbf22902c687a6d19082ecb62`: previous fresh verification baseline; CI #638, Compose E2E #210, and Backup Restore E2E #208 passed.
- `24e3b85055e6ded38ec60327af57321fef6c32b4`: aligned the static cgroup rehearsal identity guard with the implementation; fresh CI subsequently passed.
- `5ee4cfa3914d76eb49004964e3e2d1f25e947c77`: added regression coverage for autonomous Python path/configuration boundaries.
- `b8b930403a013cfed42c13cb37d4b72b2a46d449`: tightened `_approval()` so AUTO Python execution validates all arguments instead of trusting only the module prefix.

## CI surface

The main CI workflow runs the read-only cgroup capability probe before package installation and executes the repository pytest suite. The destructive cgroup rehearsal remains intentionally excluded from CI. CI #642 is the current software verification evidence for the latest main commit. Backup Restore E2E #212 also passed on the latest main commit.

## External production gates

1. Backup/restore rehearsal: GREEN IN CI / PENDING TARGET INFRASTRUCTURE.
2. Hardened Compose end-to-end rehearsal: GREEN IN CI / PENDING TARGET INFRASTRUCTURE.
3. Lardi access/mapping: BLOCKED BY PROVIDER; no protection bypass is attempted.
4. Publication/contact permissions: PENDING EXPLICIT PROVIDER/LEGAL/OPERATOR AUTHORIZATION.
5. Real booked/delivered outcomes: PENDING OPERATIONAL DATA.
6. Vercel main deployment integration: BLOCKED BY VERCEL ACCOUNT STATUS; current deployment status remains externally blocked.
7. Authorized Telegram credentials/source access: PENDING EXTERNAL AUTHORIZATION.
8. Target-host cgroup rehearsal: BLOCKED until an authorized non-root `logistics-agent` target host is available.

## Safety boundary

Evidence-only. No provider protection bypass, autonomous publication, messaging/contact, negotiation, contracting, pricing mutation, booking, or financial action. Runtime cgroup enforcement must remain fail-closed until target-host rehearsal proves containment of a detached descendant with `cgroup.kill` and successful cleanup.

## Handoff

IN_PROGRESS: target-host cgroup enforcement gate and external production-readiness gates.
NEXT: obtain an authorized target host, run `deploy/remote-agent/cgroup_gate.py` as the dedicated non-root `logistics-agent` identity with explicit rehearsal opt-in, capture the machine-readable evidence artifact, review every acceptance field, and only then design/implement runtime per-task cgroup enforcement if the gate passes. After runtime implementation, require lifecycle tests for restart, timeout, lease loss, cleanup, and detached descendants plus normal CI, Compose E2E, and Backup Restore E2E verification.
BLOCKERS: no authorized target host in the current execution surface; Vercel account block; provider access/mapping; external publication/contact authorization; authorized Telegram source access; target production backup/restore rehearsal; real commercial outcome telemetry.

LOG: `docs/agent-log/chatgpt-logistics-20260917/research-20260917.md`; `docs/agent-log/chatgpt-logistics-20260917/command-policy-audit-20260917.md`
