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


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
