# Data Governance

## Principles

Logistics OS should collect only data needed for the commercial pipeline, preserve provenance, isolate tenants, minimize personal data, and make operational decisions auditable.

## Provenance

Every provider-derived observation should retain enough provenance to answer:

- where the observation came from;
- when it was collected;
- which provider/account or integration produced it, where appropriate;
- which raw payload or evidence supports the normalized fields;
- which transformation produced the canonical representation.

Unverified provider fields must not be presented as verified facts.

## Tenant isolation

All commercial/customer data and derived scores must remain tenant-scoped. Queries, metrics, review queues, recurring-demand signals, opportunities, and audit reports must never mix tenants.

Tenant identifiers are authorization boundaries, not merely reporting labels.

## Personal and contact data

Minimize personal data in ingestion and derived records. Store contact information only when necessary for an authorized workflow. Do not harvest contacts for unrelated prospecting or bulk outreach.

Contact actions require a concrete target, channel, human-reviewed draft, explicit authorization, suppression/opt-out checks, and auditability.

## Retention

Retention should be based on business and legal need rather than indefinite accumulation. Define retention periods per data class before production rollout, including:

- raw provider observations;
- normalized loads and opportunities;
- customer/contact records;
- audit records;
- delivery telemetry;
- operational logs;
- backups.

Backups inherit the sensitivity of the data they contain and require equivalent access protection.

## Secrets

Never store API keys, passwords, operator tokens, session cookies, or other credentials in source files, fixtures, logs, or documentation. Runtime secrets belong in protected deployment configuration.

## Auditability

Decisions affecting prioritization, contact, publication, negotiation, delivery, or other external side effects should be attributable to a tenant, actor/process, timestamp, and source data where technically applicable.

## Deletion and correction

Data deletion or correction must preserve the integrity of required audit records. Where a record is removed from operational storage, retain only the minimum audit evidence required by applicable policy or law.

## Production review

Before production activation, document concrete retention periods, access roles, backup retention, incident handling, and applicable legal/contractual requirements. Until those are approved, treat the corresponding policy as a release gate rather than silently choosing permanent retention.