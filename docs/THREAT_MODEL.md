# AI Logistics OS Threat Model

## Trust boundaries

- **Operator → API:** untrusted network request; protected by `REVIEW_OPERATOR_TOKEN`.
- **API → PostgreSQL:** privileged application connection; every business query must be tenant-scoped.
- **Application → provider:** external boundary; only official/permitted adapters may cross it.
- **Scheduler/outbox → external side effect:** explicitly gated; current release records intent/telemetry but does not autonomously publish or contact.

## Assets

- tenant-isolated loads, opportunities and review data;
- provider credentials and database credentials;
- review decisions and audit history;
- outbox event identity and delivery state;
- customer/contact provenance and suppression state.

## Abuse cases and controls

| Threat | Control | Release evidence |
|---|---|---|
| Cross-tenant read | `tenant_id` predicates and isolation tests | CI integration tests |
| Unauthorized review action | operator token, fail-closed configuration | API tests |
| Secret leakage | runtime environment/secrets only | source/config review |
| Duplicate side effect | canonical outbox event UUID + attempt telemetry | recovery tests |
| Provider abuse/bypass | official adapters and capability gates | provider docs/status |
| Accidental outreach | contact intent is separate from sending; human approval | API/domain review |
| Migration drift | ordered SQL execution in CI and fresh bootstrap | CI migration job |
| Dependency vulnerability | release-time dependency audit | release checklist |
| Scheduler failure | durable run status + health endpoint | scheduler tests |

## Residual risks

- Provider contracts can change outside the repository and require re-verification.
- Production infrastructure can differ from CI and must be checked against the deployment runbook.
- Probabilistic duplicate groups are intentionally not a hard identity constraint.
- External publication/contact remains a human-gated future capability.

## Security decision

The current release boundary favors fail-closed behavior and observability over autonomy. No external side effect is enabled merely because an internal recommendation is high-confidence.
