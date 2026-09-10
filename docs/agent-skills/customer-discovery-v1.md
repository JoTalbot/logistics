# Customer Discovery V1

## Goal
Build a provenance-first pipeline for finding potential shippers/customers without unauthorized scraping, bulk harvesting or unsolicited automation.

## Pipeline

`Discovery → Qualification → Contact → First Load → Recurring Customer`

## Allowed acquisition boundary

Use only data obtained through an explicitly permitted adapter or source workflow, such as public business directories, manufacturer/distributor sites, public tenders, permitted APIs, inbound requests, referrals and the system's own transaction history.

The discovery core must not itself fetch websites, scrape pages, harvest contact lists, send messages, or enrich people with opaque third-party data.

## Canonical objects

- Organization
- Facility
- DemandSignal
- BusinessContact
- CustomerOpportunity
- DiscoverySource
- Prospect
- QualificationResult
- ContactPlan

Every externally obtained observation must preserve source, URL/reference, capture time and permission/provenance metadata.

## Qualification

`qualify_prospect()` uses only explicit, non-sensitive business signals and produces a deterministic 0–1 score, tier and reason list. The current weights are:

- lane fit: 20%
- cargo fit: 15%
- recurring demand: 20%
- geography fit: 10%
- economic fit: 20%
- fresh signal: 10%
- existing relationship: 5%

Tiers are A (≥0.75), B (≥0.50) and C (<0.50). No sensitive attributes are inferred and no contacts are fabricated.

## Contact policy

`prepare_contact_plan()` creates an internal contact intent only. It requires an explicit target, channel and authorization state. Suppression/opt-out forces authorization off. `contact_is_sendable()` never sends a message and requires the human-approval gate to remain enabled.

Contact is a separate stage and must use an authorized channel plus applicable legal/commercial rules. Suppression and opt-out state must be respected before outreach.

## Safety

No autonomous outreach is enabled by this skill. No source may be activated merely because it is technically accessible. Provider terms, API permissions, privacy/retention requirements and applicable law must be verified before activation.
