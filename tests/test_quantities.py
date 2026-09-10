import pytest
from logistics.quantities import normalize_quantities

@pytest.mark.parametrize('source,expected',[('Вага 22 тон',22000),('20 тонн',20000),('Вес: 22 тн',22000),('22000 кг',22000),('22 t',22000),('22,5т',22500),('12 500 kg',12500)])
def test_weight_units(source,expected):
    result,_=normalize_quantities(source)
    assert result['weight_kg']==expected

def test_omitted_unit_recovered_from_own_source():
    r,_=normalize_quantities('Вага: 22 тон. Київ — Львів',weight_hint='22')
    assert r['weight_kg']==22000 and r['weight_evidence']=='22 тон'

def test_weight_range_not_guessed():
    r,reasons=normalize_quantities('Вес 20-22 т')
    assert r['weight_kg'] is None
    assert r['weight_min_kg']=='20000' and r['weight_max_kg']=='22000'
    assert 'weight_range_requires_review' in reasons

def test_multiple_weights_do_not_merge():
    r,reasons=normalize_quantities('А: 20 т; Б: 22 т')
    assert r['weight_kg'] is None and 'multiple_weight_values' in reasons

@pytest.mark.parametrize('text,amount,cur',[('25 000 грн','25000','UAH'),('USD 500','500','USD'),('500 доллар','500','USD'),('1000000 сум','1000000','UZS'),('1000 RUB','1000','RUB'),('Ставка: 500','500',None)])
def test_money(text,amount,cur):
    r,_=normalize_quantities(text)
    assert r['price']==amount and r['currency']==cur

def test_currency_not_invented():
    r,_=normalize_quantities('$500')
    assert r['price']=='500' and r['currency'] is None

def test_bare_phone_or_amount_not_price():
    r,_=normalize_quantities('Телефон 380501234567',price_hint='380501234567')
    assert r['price'] is None

def test_ambiguous_thousands_not_silently_decimal():
    r,reasons=normalize_quantities('25,000 USD')
    assert r['price'] is None and 'ambiguous_or_invalid_price' in reasons

def test_two_prices_not_merged():
    r,reasons=normalize_quantities('500 USD или 20000 грн')
    assert r['price'] is None and 'multiple_price_values' in reasons

def test_rate_basis():
    r,reasons=normalize_quantities('30 грн/км')
    assert r['price']=='30' and r['price_basis']=='per_km'
    assert 'unit_rate_not_trip_total' in reasons
