# Production Activation Runbook

This runbook converts the current software-verified state into a controlled production activation without weakening the repository's fail-closed safety boundary.

## 1. Preconditions

Do not enable autonomous external actions until every applicable gate below has evidence.

- [ ] Authorized non-root target host exists.
- [ ] Dedicated execution identity is exactly `logistics-agent`.
- [ ] Target host has cgroup v2 and required systemd/cgroup capabilities.
- [ ] Destructive cgroup rehearsal is explicitly opted in.
- [ ] Rehearsal produces machine-readable evidence and verifies detached-descendant containment, `cgroup.kill`, process death, and cleanup.
- [ ] Telegram source access is explicitly authorized and credentials are provisioned through secrets.
- [ ] Lardi access/mapping is authorized by the provider.
- [ ] Target infrastructure backup/restore rehearsal is completed.
- [ ] Vercel deployment/account integration is operational where required.
- [ ] Publication/contact permissions are explicitly authorized.
- [ ] Real booked/delivered outcome telemetry is available.

## 2. Cgroup gate

Run the existing gate as the dedicated non-root identity:

```bash
LOGISTICS_CGROUP_EVIDENCE_PATH=/var/lib/logistics/cgroup-rehearsal-evidence.json \
  sudo -u logistics-agent --preserve-env=LOGISTICS_CGROUP_REHEARSAL=1,LOGISTICS_CGROUP_EVIDENCE_PATH \
  python deploy/remote-agent/cgroup_gate.py
```

Use the repository's actual target-host configuration and preserve the fail-closed behavior. Do not run the destructive rehearsal in ordinary CI or as root.

Acceptance requires all machine-readable evidence fields to pass. A partial result is a failure, not permission to continue.

## 3. Runtime isolation promotion

Only after the target-host gate passes:

1. Design runtime per-task cgroup placement from the existing evidence contract.
2. Add lifecycle tests for start, restart, timeout, lease loss, detached descendants, and cleanup.
3. Keep process-group fencing as a secondary control.
4. Require normal CI, hardened Compose E2E, and Backup/Restore E2E on the final commit.
5. Do not promote runtime isolation merely because a capability probe succeeds.

## 4. Controlled commercial activation

Start in shadow/review mode:

`source → normalization → deduplication → opportunity scoring → human approval → permitted action → outcome → learning`

For the first production cohort:

- no autonomous financial action;
- no autonomous contracting outside explicitly approved limits;
- no provider protection bypass;
- no unapproved publication or contact;
- every material AI decision is auditable;
- kill switch remains available.

Promotion to broader autonomy requires observed outcomes, not synthetic success alone.

## 5. Evidence package

Archive:

- target-host identity and capability evidence;
- cgroup rehearsal result;
- CI run identifiers for the final commit;
- Compose E2E result;
- Backup/Restore E2E result;
- integration authorization records;
- publication/contact authorization;
- first controlled commercial outcomes;
- rollback/incident evidence.

## 6. Stop criteria

Stop and keep the system fail-closed when:

- execution identity is wrong;
- cgroup containment is incomplete;
- cleanup fails;
- provider access is ambiguous;
- authorization is missing;
- financial/legal limits are unclear;
- real-world outcome telemetry is absent;
- any safety regression appears.

## Current state

As of 2026-10-07, the repository remains software-verified but production-blocked. See `STATUS.md` and GitHub issue #21 for the authoritative external activation checklist.
