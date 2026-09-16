# V43 Current CI Evidence

Updated: 2026-09-16

This document records the current repository-level verification contour for the `main` branch. It is intentionally separate from historical V39 evidence so that historical provenance is preserved.

## Verified software head

The latest application-bearing software head covered by the current verification set is:

- SHA: `362968477c368f4efd1b263715f86109c957bb37`
- Change: `fix(compose-e2e): apply remote-control migrations before verification`

The subsequent test-only `main` commit `9a9f7f064000e21521bd2eeac7a3dbbb91f4c6f7` changes only `tests/test_remote_agent_install.py`: it strengthens the regression so the installer is explicitly asserted not to invoke or opt into the destructive cgroup rehearsal. This does not change application behavior.

## GitHub Actions verification

For software head `362968477c368f4efd1b263715f86109c957bb37`:

| Workflow | Run | Result |
|---|---:|---|
| CI | `35138822808` (#591) | success |
| Compose E2E | `35138822797` (#163) | success |
| Backup Restore E2E | `35138822766` (#161) | success |

The CI run completed its dependency checks, migrations, unit/integration tests, commercial-baseline replay, hardened Compose contract, local release smoke checks, hardened API image build, and cleanup successfully.

The Backup Restore E2E run completed migrations, disposable seed, PostgreSQL 17 logical backup, restore, marker/schema verification, and cleanup successfully.

The Compose E2E run verifies the remote-control credential-generation/idempotency schema after explicitly applying migrations `0028` and `0029` on the clean test database. This explicit migration ordering fixes the earlier clean-database verification failure.

## Current `main` test-head verification

The current `main` test head `9a9f7f064000e21521bd2eeac7a3dbbb91f4c6f7` was exercised by fresh GitHub Actions checks:

| Workflow | Run | Result |
|---|---:|---|
| CI | `35145045520` (#593) | success |
| Compose E2E | `35145045527` (#165) | success |
| Backup Restore E2E | `35145045536` (#163) | success |

The CI job's `Run unit and integration tests` step completed successfully, so the repository pytest suite covered the test-only change. The same run also completed cgroup probing, dependency consistency/audit, migrations, V20 baseline replay, hardened Compose validation, release smoke checks, API image build, and cleanup successfully.

## External status boundary

GitHub commit status for the current `main` head remains externally blocked by Vercel:

- `Vercel`: `failure`, description `Account is blocked.`
- `Vercel Deployments – fgfgggg`: `pending`.

No successful Vercel deployment is claimed by this document.

Other external readiness blockers remain outside GitHub CI, including target-host cgroup rehearsal, provider-authorized Lardi access/mapping, authorized Telegram source access, publication/contact permissions, and operational booked/delivered outcome evidence.

## Cgroup boundary

The repository currently implements read-only cgroup capability probing, an explicit opt-in destructive target-host rehearsal, an evidence contract, and regression tests. It does **not** activate per-task cgroup runtime containment merely because a host reports `READY`.

Production activation remains gated on successful target-host rehearsal with a detached descendant, consistent cgroup membership, successful `cgroup.kill`, cleanup, machine-readable evidence, and subsequent lifecycle/regression verification.

## Historical evidence

`docs/V39_CURRENT_CI_EVIDENCE.md` is retained as historical V39 evidence. Its older verification SHA and run numbers describe the V39 verification point and are not presented as the current V43 software head.
