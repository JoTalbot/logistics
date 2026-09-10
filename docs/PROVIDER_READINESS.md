# Provider Readiness Matrix

This matrix separates implemented integration code from capabilities that are actually authorized and verified.

| Provider | Access | API/contract | Verified data | Allowed actions | Publication | Evidence / blocker |
|---|---|---|---|---|---|---|
| Lardi-Trans | Credential configured | Official v2 API client implemented | Canonical mapping remains limited until real response samples are verified | Read-only discovery only | **NO-GO** | Latest smoke reached provider infrastructure but returned HTTP 403 Cloudflare Error 1010 (`browser_signature_banned`) |
| DELLA | Not verified | No supported production transport contract established | None | None beyond documented research | **NO-GO** | Provider/API access and terms require verification before implementation |

## Readiness states

- **READY**: access, contract, fields, error semantics, and permitted action are verified.
- **LIMITED**: some capabilities are verified, but side effects or fields remain restricted.
- **BLOCKED**: provider currently prevents reliable/authorized use.
- **UNVERIFIED**: insufficient evidence to implement safely.

## Lardi-Trans

Current state: **BLOCKED / read-only implementation only**.

The repository contains a client for the documented API endpoints used for cargo and transport discovery. The provider credential is injected at runtime through `LARDI_API_KEY`.

The current provider smoke test produced a provider-side 403 Cloudflare Error 1010 with `browser_signature_banned`. This is an external access blocker. It is not a signal to add browser automation, signature spoofing, anti-bot bypasses, or retry loops.

Before expanding the Lardi integration, obtain and record:

1. confirmed account/API access;
2. current API documentation or contractual scope;
3. representative successful response samples;
4. field definitions and pagination/filter semantics;
5. rate-limit and error semantics;
6. permission for each intended action;
7. explicit publication permissions if publishing is required.

Until these are verified, discovery remains read-only and publication stays disabled.

## DELLA

Current state: **UNVERIFIED**.

No production transport mechanism is assumed. Do not implement scraping or browser automation as a substitute for an official API or explicitly permitted integration mechanism.

## Change control

Every provider capability change should record:

- provider and endpoint;
- verification date;
- evidence/source;
- fields verified;
- rate-limit/error behavior;
- permitted side effects;
- authentication method;
- rollback or disable mechanism.

Provider readiness is a release gate. Green CI does not make an unverified provider contract safe.