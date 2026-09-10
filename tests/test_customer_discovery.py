from datetime import datetime, timezone

import pytest

from logistics.customer_discovery import (
    DiscoverySource,
    QualificationSignals,
    contact_is_sendable,
    discover_prospect,
    prepare_contact_plan,
    qualify_prospect,
)


def source(*, permitted=True, url="https://example.com/public"):
    return DiscoverySource(
        source="public_business_catalog",
        url=url,
        captured_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
        permitted=permitted,
    )


def test_discovery_preserves_provenance_and_minimizes_optional_data():
    prospect = discover_prospect(
        " Example Logistics LLC ", source(), country=" UA ", city=" Kropyvnytskyi", signal="recurring outbound freight"
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


def test_qualification_is_deterministic_and_explainable():
    result = qualify_prospect(
        QualificationSignals(
            lane_fit=True,
            cargo_fit=True,
            recurring_demand=True,
            geography_fit=True,
            economic_fit=True,
            fresh_signal=True,
        )
    )
    assert result.score == 0.95
    assert result.tier == "A"
    assert "economic_fit" in result.reasons


def test_suppression_blocks_contact_even_when_authorized():
    prospect = discover_prospect("Example", source(), contact="ops@example.com")
    plan = prepare_contact_plan(prospect, channel=" email ", authorized=True, suppressed=True)
    assert plan.channel == "email"
    assert not plan.authorized
    assert not contact_is_sendable(plan)


def test_contact_plan_requires_target_and_human_gate():
    prospect = discover_prospect("Example", source(), contact="ops@example.com")
    plan = prepare_contact_plan(prospect, channel="email", authorized=True)
    assert plan.target == "ops@example.com"
    assert plan.requires_human_approval
    assert contact_is_sendable(plan)


def test_contact_plan_rejects_missing_target():
    prospect = discover_prospect("Example", source())
    with pytest.raises(ValueError):
        prepare_contact_plan(prospect, channel="email", authorized=True)
