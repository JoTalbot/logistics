from datetime import datetime, timezone

import pytest

from logistics.customer_discovery import DiscoverySource, discover_prospect


def source(*, permitted=True, url="https://example.com/public"):
    return DiscoverySource(
        source="public_business_catalog",
        url=url,
        captured_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        permitted=permitted,
    )


def test_discovery_preserves_provenance_and_minimizes_optional_data():
    prospect = discover_prospect(
        " Example Logistics LLC ",
        source(),
        country=" UA ",
        city=" Kropyvnytskyi ",
        signal="recurring outbound freight",
    )
    assert prospect.organization_name == "Example Logistics LLC"
    assert prospect.country == "UA"
    assert prospect.city == "Kropyvnytskyi"
    assert prospect.contact is None
    assert prospect.source.source == "public_business_catalog"


def test_discovery_rejects_unpermitted_source():
    with pytest.raises(PermissionError):
        discover_prospect("Example", source(permitted=False))


def test_discovery_rejects_invalid_source_url():
    with pytest.raises(ValueError):
        discover_prospect("Example", source(url="not-a-url"))


def test_discovery_rejects_blank_organization():
    with pytest.raises(ValueError):
        discover_prospect("   ", source())
