from decimal import Decimal
from uuid import uuid4

from logistics.demand import DemandProfile, rank_demand, score_customer_demand
from logistics.domain import CanonicalLocation, Load, LoadStop


def make_load(cargo_type="general", weight_kg=10000, price="1500"):
    return Load(
        tenant_id=uuid4(), cargo_type=cargo_type, weight_kg=weight_kg,
        offered_price=Decimal(price), currency="EUR",
        stops=[
            LoadStop(sequence=0, kind="pickup", location=CanonicalLocation(raw_address="Kyiv", normalized_address="Kyiv", country_code="UA")),
            LoadStop(sequence=1, kind="delivery", location=CanonicalLocation(raw_address="Lviv", normalized_address="Lviv", country_code="UA")),
        ],
    )


def test_demand_score_rewards_matching_preferences():
    load = make_load()
    profile = DemandProfile(customer_id=str(uuid4()), preferred_countries=frozenset({"UA"}), preferred_cargo=frozenset({"general"}), min_weight_kg=5000, max_weight_kg=20000, min_price=Decimal("1000"), max_price=Decimal("2000"))
    signal = score_customer_demand(load, profile)
    assert signal.score == 1.0
    assert set(signal.reasons) >= {"cargo_match", "weight_match", "price_match", "geography_match"}


def test_demand_rank_is_descending():
    load = make_load()
    good = DemandProfile(customer_id="good", preferred_cargo=frozenset({"general"}), min_price=Decimal("1000"))
    weak = DemandProfile(customer_id="weak", preferred_cargo=frozenset({"refrigerated"}), min_price=Decimal("3000"))
    ranked = rank_demand(load, [weak, good])
    assert ranked[0].customer_id == "good"
    assert ranked[0].score >= ranked[1].score
