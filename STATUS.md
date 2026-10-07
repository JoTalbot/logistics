# Project Status — AI Logistics OS

CURRENT_STEP: V43.38 — Current production verification synchronized
STATUS: blocked
UPDATED: 2026-10-08
AGENT: chatgpt-logistics-20260917
MACHINE: GitHub-connected execution environment
SCOPE: Continue production readiness from the latest green verification; preserve fail-closed activation boundaries and separate software verification from target-host containment evidence.
FILES: deploy/remote-agent/install.sh; tests/test_remote_agent_systemd.py; deploy/remote-agent/cgroup_probe.py; deploy/remote-agent/cgroup_rehearsal.py; deploy/remote-agent/cgroup_gate.py; tests/test_remote_agent_cgroup_gate.py; tests/test_remote_agent_cgroup_rehearsal_static.py; backend/logistics/remote_control.py; tests/test_remote_control.py; STATUS.md; docs/PRODUCTION_ACTIVATION_RUNBOOK.md
RESEARCH: Linux kernel cgroup-v2 documentation; systemd resource-control documentation; repository cgroup design/evidence contract; existing remote-agent and remote-control implementation.
DECISIONS: Runtime per-task cgroup enforcement remains disabled. The destructive target-host rehearsal must be explicitly opted in, run non-root, report the dedicated `logistics-agent` execution identity, report READY capabilities, contain a deliberately detached descendant, fence through `cgroup.kill`, and clean up successfully. Post-spawn PID migration is not accepted as containment evidence. Autonomous Python tooling is argument-bounded rather than prefix-trusted. Remote-agent installation and every subsequent systemd service start fail closed when required credentials are missing, whitespace-only, or still set to known placeholders; control-plane URL/token must also be both configured or both absent.

## Verification state

**SOFTWARE CONTOUR: GREEN / FRESH CI VERIFIED** — commit `0253821075b47b9b1fb62edaa6029e2ed907879f` passed CI #670.

**HARDENED COMPOSE E2E: GREEN / FRESH** — Compose E2E #242 for commit `0253821075b47b9b1fb62edaa6029e2ed907879f` completed successfully.

**BACKUP/RESTORE E2E: GREEN / FRESH** — Backup Restore E2E #240 for commit `0253821075b47b9b1fb62edaa6029e2ed907879f` completed successfully.

**REMOTE-AGENT STARTUP HARDENING: GREEN / CI VERIFIED** — `install.sh` rejects missing, whitespace-only, or known-placeholder values for `AGENT_AUTH_TOKEN` and `AI_GATEWAY_API_KEY`, and validates the configured control-plane URL/token pair. The installed systemd unit repeats the credential gate on every service start through `ExecStartPre`, so a later configuration regression cannot bypass the installer-time checks. The service remains installable while intentionally unconfigured, but startup is fail-closed until required configuration is valid.

**CURRENT FUNCTIONAL IMPLEMENTATION:** remote-agent lifecycle context management is covered by regression testing; credential-generation lease fencing is enforced; deterministic lock fencing is covered; direct bootstrap reenrollment cancels active running leases; agent credential authentication requires an explicit `Bearer` scheme; local agent execution fences the POSIX process group on timeout/lease loss. The control-plane AUTO classifier rejects Python path traversal, absolute paths, arbitrary pytest configuration/plugin selectors, and unsupported compiler flags.

**CURRENT DESIGN STATE:** read-only cgroup capability probe, target-host evidence contract, opt-in transient-scope rehearsal, and a fail-closed gate are implemented. The gate and the rehearsal require the effective execution identity to be exactly `logistics-agent`. Static regression coverage protects direct rehearsal identity/readiness ordering, absence of post-spawn cgroup migration, cgroup.kill fencing, process-death verification, and cleanup verification. Runtime per-task cgroup isolation is not enabled.

## Latest hardening

- `e3c502101cd9ca60ca50c6fa8e13e1a7a2b86ff2`: fixed remote-agent installer systemd environment expansion and added regression coverage so credential variables remain runtime-expanded rather than being consumed by the installer shell.
- `e8e4c7039c519d5f6831a114f14902f835f3c0a2`: corrected systemd environment expansion in the generated service unit.
- `0196b5f502a8d482d0d1ff78a5e28b36a996e868`: fixed cgroup gate regression fixtures so evidence-path configuration exists only in tests that reach the evidence-validation path.
- `cadaa315c5576c51f519a9bfe9f0291c938bdc48`: added regression coverage that the cgroup gate accepts activation only when archived machine-readable evidence proves `result=PASS` and successful cleanup.
- `b4629a2591c1ec737ec01e6ae9fa7e08e6d751ee`: added negative regression coverage for missing evidence and evidence that reports `cleanup=false`; both must fail closed.
- `8ef4fc64c44a984041d75e32d3bc2759bb7cc9e2`: clarified that the target-host evidence directory must be created writable by `logistics-agent` before running the gate.
- `0cd40ead06a0fd6be3856d9f4700b021fb1765b1`: strengthened the cgroup gate to require an explicit evidence archive path and validate rehearsal evidence before reporting PASS.
- `c2ed91515098db46486de957a1180a215dd38e08`: documented the evidence archive requirement in the controlled production activation runbook.
- `4c847c3b1f5bda8d354f93a4878459a14ccf197f`: added `docs/PRODUCTION_ACTIVATION_RUNBOOK.md` with the controlled activation sequence, evidence package, and explicit stop criteria.

## CI surface

The main CI workflow runs the read-only cgroup capability probe before package installation and executes the repository pytest suite. CI #670 for `0253821075b47b9b1fb62edaa6029e2ed907879f` completed successfully. Compose E2E #242 and Backup Restore E2E #240 also completed successfully on that commit. The destructive cgroup rehearsal remains intentionally excluded from CI because it requires an authorized dedicated target host and is explicitly destructive.

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
NEXT: use the corrected runbook command on an authorized target host, obtain the machine-readable cgroup evidence, run `deploy/remote-agent/cgroup_gate.py` as the dedicated non-root `logistics-agent` identity with explicit rehearsal opt-in, capture the machine-readable evidence artifact, review every acceptance field, and only then design/implement runtime per-task cgroup enforcement if the gate passes. After runtime implementation, require lifecycle tests for restart, timeout, lease loss, cleanup, and detached descendants plus normal CI, Compose E2E, and Backup Restore E2E verification.
BLOCKERS: no authorized target host in the current execution surface; Vercel account block; provider access/mapping; external publication/contact authorization; authorized Telegram source access; target production backup/restore rehearsal; real commercial outcome telemetry.

LOG: `docs/agent-log/chatgpt-logistics-20260917/research-20260917.md`; `docs/agent-log/chatgpt-logistics-20260917/command-policy-audit-20260917.md`
