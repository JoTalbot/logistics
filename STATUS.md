# Project Status — AI Logistics OS

CURRENT_STEP: V43.18 — Remote-agent systemd startup fail-closed hardening
STATUS: blocked
UPDATED: 2026-09-17
AGENT: chatgpt-logistics-20260917
MACHINE: GitHub-connected execution environment
SCOPE: Continue remote-agent production hardening after fresh CI verification; preserve fail-closed activation boundaries and separate software verification from target-host containment evidence.
FILES: deploy/remote-agent/install.sh; tests/test_remote_agent_systemd.py; deploy/remote-agent/cgroup_rehearsal.py; deploy/remote-agent/cgroup_gate.py; tests/test_remote_agent_cgroup_gate.py; tests/test_remote_agent_cgroup_rehearsal_static.py; backend/logistics/remote_control.py; tests/test_remote_control.py; STATUS.md
RESEARCH: Linux kernel cgroup-v2 documentation; systemd resource-control documentation; repository cgroup design/evidence contract; existing remote-agent and remote-control implementation.
DECISIONS: Runtime per-task cgroup enforcement remains disabled. The destructive target-host rehearsal must be explicitly opted in, run non-root, report the dedicated `logistics-agent` execution identity, report READY capabilities, contain a deliberately detached descendant, fence through `cgroup.kill`, and clean up successfully. Post-spawn PID migration is not accepted as containment evidence. Autonomous Python tooling is argument-bounded rather than prefix-trusted. Remote-agent installation and every subsequent systemd service start fail closed when required credentials are missing, whitespace-only, or still set to known placeholders; control-plane URL/token must also be both configured or both absent.

## Verification state

**SOFTWARE CONTOUR: GREEN / FRESH CI VERIFIED** — commit `36e5bf253cbcb9595ce5bd47a27dbe48e394a102` passed CI #649. The completed test job passed the cgroup capability probe, dependency checks, `pip-audit`, SQL migrations, unit/integration tests, V20 commercial baseline replay, hardened Compose contract validation, release smoke checks, and hardened API image build.

**BACKUP/RESTORE E2E: GREEN / FRESH** — Backup Restore E2E #219 for commit `36e5bf253cbcb9595ce5bd47a27dbe48e394a102` completed successfully.

**REMOTE-AGENT STARTUP HARDENING: GREEN / CI VERIFIED** — `install.sh` rejects missing, whitespace-only, or known-placeholder values for `AGENT_AUTH_TOKEN` and `AI_GATEWAY_API_KEY`, and validates the configured control-plane URL/token pair. The installed systemd unit repeats the credential gate on every service start through `ExecStartPre`, so a later configuration regression cannot bypass the installer-time checks. The service remains installable while intentionally unconfigured, but startup is fail-closed until required configuration is valid.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is covered by regression testing; credential-generation lease fencing is enforced; deterministic lock fencing is covered; direct bootstrap reenrollment cancels active running leases; agent credential authentication requires an explicit `Bearer` scheme; local agent execution fences the POSIX process group on timeout/lease loss. The control-plane AUTO classifier rejects Python path traversal, absolute paths, arbitrary pytest configuration/plugin selectors, and unsupported compiler flags.

**CURRENT DESIGN STATE:** read-only cgroup capability probe, target-host evidence contract, opt-in transient-scope rehearsal, and a fail-closed gate are implemented. The gate and the rehearsal require the effective execution identity to be exactly `logistics-agent`. Static regression coverage protects direct rehearsal identity/readiness ordering, absence of post-spawn cgroup migration, cgroup.kill fencing, process-death verification, and cleanup verification. Runtime per-task cgroup isolation is not enabled.

## Latest hardening

- `36e5bf253cbcb9595ce5bd47a27dbe48e394a102`: added CI coverage for whitespace-only startup credentials; CI #649 and Backup Restore E2E #219 passed.
- `4d291ec0c1b5e165ccd3481eec3238026b91f82d`: strengthened the systemd startup credential gate to reject whitespace-only required values and preserve fail-closed control-plane pairing.
- `6e8378ea57411a3d54cd6caee71c9f35b6311428`: added regression coverage for missing credential fail-closed behavior; subsequent Compose E2E and Backup Restore E2E passed.
- `f90f8d2c90db298a7536fa47636925211be67d7a`: introduced fail-closed remote-agent startup behavior for missing credentials.
- `07c7cde25ef49806a7815aeed043457d83bac6f8`: removed an unused test placeholder variable; CI #642 and Backup Restore E2E #212 subsequently passed.
- `cb26594c9a3c5a16909cf65f0b695af1192a819c`: added regression coverage requiring install-time fail-closed handling of control-plane placeholders.
- `ec4747ff4852122551471139904d3dc9124a4bfe`: tightened remote-agent installation so known secret/control-plane placeholders prevent service startup.
- `24e3b85055e6ded38ec60327af57321fef6c32b4`: aligned the static cgroup rehearsal identity guard with the implementation; fresh CI subsequently passed.
- `5ee4cfa3914d76eb49004964e3e2d1f25e947c77`: added regression coverage for autonomous Python path/configuration boundaries.
- `b8b930403a013cfed42c13cb37d4b72b2a46d449`: tightened `_approval()` so AUTO Python execution validates all arguments instead of trusting only the module prefix.

## CI surface

The main CI workflow runs the read-only cgroup capability probe before package installation and executes the repository pytest suite. CI #649 for `36e5bf253cbcb9595ce5bd47a27dbe48e394a102` completed successfully. Backup Restore E2E #219 also completed successfully on that commit. The destructive cgroup rehearsal remains intentionally excluded from CI because it requires an authorized dedicated target host and is explicitly destructive.

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
