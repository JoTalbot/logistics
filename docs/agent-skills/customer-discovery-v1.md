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

Every externally obtained observation must preserve source, URL/reference, capture time and permission/provenance metadata.

## Qualification

Rank prospects using deterministic signals such as lane fit, cargo fit, shipment frequency, geography, estimated economics, freshness and existing relationship. Do not infer sensitive attributes or fabricate contacts.

## Contact policy

Contact is a separate stage. It must use an authorized channel and applicable legal/commercial rules. Suppression and opt-out state must be respected before outreach.

## Safety

No autonomous outreach is enabled by this skill. No source may be activated merely because it is technically accessible. Provider terms, API permissions, privacy/retention requirements and applicable law must be verified before activation.
