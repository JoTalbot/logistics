from logistics.local_llm import ExtractedAd, normalize, extract
import pytest

def ad(**changes):
    d=dict(kind='load',multiple_ads=False,origin=None,destination=None,cargo=None,weight=None,volume=None,price=None,vehicle=None,date=None)
    d.update(changes)
    return ExtractedAd(**d)

def test_amount_weight_date_and_provenance():
    text='Київ - Львів. Зерно 22 т, 25 000 грн, 11.09.2026'
    r=normalize(text,ad(origin='Київ',destination='Львів',cargo='Зерно',weight='22 т',price='25 000 грн',date='11.09.2026'))
    assert r['price']=='25000' and r['currency']=='UAH'
    assert r['weight_kg']==22000 and r['loading_date']=='2026-09-11'
    assert r['review_required'] and not r['autopublish_allowed']

def test_hallucinated_fields_removed():
    r=normalize('Київ - Львів',ad(origin='Київ',destination='Одеса',price='500 USD'))
    assert r['destination'] is None and r['price'] is None
    assert 'unsupported_destination' in r['review_reasons']

def test_currency_dollar_word_and_ambiguous_symbol():
    assert normalize('500 доллар',ad(price='500 доллар'))['currency']=='USD'
    assert normalize('500 $',ad(price='500 $'))['currency'] is None

def test_unknown_currency_not_default_uah():
    assert normalize('500 XYZ',ad(price='500 XYZ'))['currency'] is None

def test_no_date_guessing_or_mixed_offers():
    r=normalize('завтра 22 t',ad(date='завтра',weight='22 t',multiple_ads=True))
    assert r['loading_date'] is None and r['weight_kg']==22000
    assert 'multiple_ads_do_not_merge' in r['review_reasons']

def test_kg_and_per_km_not_total():
    r=normalize('22000 кг, 30 грн/км',ad(weight='22000 кг',price='30 грн/км'))
    assert r['weight_kg']==22000 and r['price_basis']=='per_km'
    assert 'unit_rate_not_trip_total' in r['review_reasons']

def test_external_endpoint_blocked_before_request():
    with pytest.raises(ValueError):extract('test',endpoint='https://example.com',model='qwen2.5:1.5b')

def test_cloud_model_blocked_before_request():
    with pytest.raises(ValueError):extract('test',endpoint='http://127.0.0.1:11434',model='cloud-model')

def test_unknown_keys_rejected():
    with pytest.raises(ValueError):ad(shell='run something')
