from decimal import Decimal
from uuid import uuid4

from logistics.domain import Load, LoadStatus, LoadStop, CanonicalLocation
from logistics.policy import PolicyEngine
from logistics.publication import GenericFreightExchangeAdapter, PublicationEngine, PublicationRequest


def make_load(status=LoadStatus.NORMALIZED):
    return Load(
        tenant_id=uuid4(), cargo_type="зерно", weight_kg=20_000,
        offered_price=Decimal("1200"), currency="EUR", status=status,
        stops=[
            LoadStop(sequence=0, kind="pickup", location=CanonicalLocation(raw_address="Київ", normalized_address="Київ", confidence=1)),
            LoadStop(sequence=1, kind="delivery", location=CanonicalLocation(raw_address="Львів", normalized_address="Львів", confidence=1)),
        ],
    )


def test_publication_applies_markup_and_preserves_provenance():
    load = make_load()
    result = PublicationEngine().prepare(PublicationRequest(
        tenant_id=load.tenant_id, load=load, provider="freight_exchange",
        actor_roles=frozenset({"autonomy"}), markup_percent=Decimal("10"),
        source_provenance="telegram-regex-v1",
    ), GenericFreightExchangeAdapter())
    assert result.allowed
    assert result.payload is not None
    assert result.payload.price == Decimal("1320.00")
    assert result.payload.provenance == "telegram-regex-v1"
    assert result.payload.role == "forwarder"


def test_critical_publication_requires_human_operator():
    load = make_load()
    result = PublicationEngine().prepare(PublicationRequest(
        tenant_id=load.tenant_id, load=load, provider="freight_exchange",
        actor_roles=frozenset({"autonomy"}), risk_level="critical",
    ), GenericFreightExchangeAdapter())
    assert not result.allowed
    assert "human_operator" in result.policy.reason


def test_invalid_markup_is_denied():
    load = make_load()
    result = PublicationEngine().prepare(PublicationRequest(
        tenant_id=load.tenant_id, load=load, provider="freight_exchange",
        actor_roles=frozenset({"autonomy"}), markup_percent=Decimal("101"),
    ), GenericFreightExchangeAdapter())
    assert not result.allowed


def test_cancelled_load_is_denied():
    load = make_load(LoadStatus.CANCELLED)
    result = PublicationEngine().prepare(PublicationRequest(
        tenant_id=load.tenant_id, load=load, provider="freight_exchange",
        actor_roles=frozenset({"autonomy"}),
    ), GenericFreightExchangeAdapter())
    assert not result.allowed
