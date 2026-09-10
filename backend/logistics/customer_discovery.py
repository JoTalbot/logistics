from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse


@dataclass(frozen=True)
class DiscoverySource:
    source: str
    url: str
    captured_at: datetime
    permitted: bool = True


@dataclass(frozen=True)
class Prospect:
    organization_name: str
    source: DiscoverySource
    country: str | None = None
    city: str | None = None
    website: str | None = None
    contact: str | None = None
    signal: str | None = None


@dataclass(frozen=True)
class QualificationSignals:
    lane_fit: bool = False
    cargo_fit: bool = False
    recurring_demand: bool = False
    geography_fit: bool = False
    economic_fit: bool = False
    fresh_signal: bool = False
    existing_relationship: bool = False


@dataclass(frozen=True)
class QualificationResult:
    score: float
    tier: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ContactPlan:
    channel: str
    target: str
    authorized: bool = False
    suppressed: bool = False
    requires_human_approval: bool = True


def validate_public_source(source: DiscoverySource) -> None:
    """Reject malformed or explicitly unpermitted discovery sources."""
    parsed = urlparse(source.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("discovery source must be an absolute HTTP(S) URL")
    if not source.permitted:
        raise PermissionError("discovery source is not permitted")


def discover_prospect(
    organization_name: str,
    source: DiscoverySource,
    *,
    country: str | None = None,
    city: str | None = None,
    website: str | None = None,
    contact: str | None = None,
    signal: str | None = None,
) -> Prospect:
    """Create a provenance-first prospect from already obtained public data.

    This module deliberately does not fetch, scrape, enrich, or contact external
    parties. Acquisition belongs to an explicitly authorized source adapter.
    """
    validate_public_source(source)
    name = organization_name.strip()
    if not name:
        raise ValueError("organization_name is required")
    return Prospect(
        organization_name=name,
        source=source,
        country=country.strip() if country else None,
        city=city.strip() if city else None,
        website=website.strip() if website else None,
        contact=contact.strip() if contact else None,
        signal=signal.strip() if signal else None,
    )


def qualify_prospect(signals: QualificationSignals) -> QualificationResult:
    """Score only explicit, non-sensitive business signals deterministically."""
    weights = {
        "lane_fit": 0.20,
        "cargo_fit": 0.15,
        "recurring_demand": 0.20,
        "geography_fit": 0.10,
        "economic_fit": 0.20,
        "fresh_signal": 0.10,
        "existing_relationship": 0.05,
    }
    reasons = tuple(name for name, enabled in vars(signals).items() if enabled)
    score = round(sum(weights[name] for name in reasons), 4)
    tier = "A" if score >= 0.75 else "B" if score >= 0.50 else "C"
    return QualificationResult(score=score, tier=tier, reasons=reasons)


def prepare_contact_plan(
    prospect: Prospect,
    *,
    channel: str,
    authorized: bool,
    suppressed: bool = False,
    human_approval: bool = True,
) -> ContactPlan:
    """Prepare an auditable contact intent; never send anything externally."""
    if not prospect.contact:
        raise ValueError("contact target is required")
    channel_name = channel.strip().casefold()
    if not channel_name:
        raise ValueError("contact channel is required")
    if suppressed:
        authorized = False
    return ContactPlan(
        channel=channel_name,
        target=prospect.contact,
        authorized=authorized,
        suppressed=suppressed,
        requires_human_approval=human_approval,
    )


def contact_is_sendable(plan: ContactPlan) -> bool:
    """Return whether a contact intent passes local policy, without performing it."""
    return plan.authorized and not plan.suppressed and plan.requires_human_approval


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
