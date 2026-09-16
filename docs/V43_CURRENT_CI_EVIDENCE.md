# V43 Current CI Evidence

Updated: 2026-09-16

This document records the current repository-level verification contour for the `main` branch. It is intentionally separate from historical V39 evidence so that historical provenance is preserved.

## Verified software head

The latest application-bearing software head covered by the current verification set is:

- SHA: `362968477c368f4efd1b263715f86109c957bb37`
- Change: `fix(compose-e2e): apply remote-control migrations before verification`

The subsequent `main` commit `68bba460a80e99243289e04d4b70b28265e804c6` is documentation-only and records the verified software head without changing the application implementation.

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

## Current `main` verification

The documentation head `68bba460a80e99243289e04d4b70b28265e804c6` was also exercised by fresh GitHub Actions runs:

| Workflow | Run | Result |
|---|---:|---|
| CI | `35140553576` (#592) | success |
| Compose E2E | `35140553628` (#164) | success |
| Backup Restore E2E | `35140553548` (#162) | success |

These runs confirm that the documentation reconciliation did not break the repository verification contour.

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
