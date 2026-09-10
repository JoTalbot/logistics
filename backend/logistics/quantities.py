"""Source-grounded numbers; no guessed currencies or range midpoints."""
import re
from decimal import Decimal

NUM=r'\d+(?:[ \u00a0\u202f]\d{3})*(?:[.,]\d+)?'
WEIGHT_UNIT=r'(?:килограмм(?:а|ов)?|кілограм(?:и|ів)?|тонн(?:а|ы|у)?|тон(?:а|и)?|tons?|кг|kg|тн|т|t)'
CURRENCY=r'(?:USD|EUR|UAH|RUB|UZS|KZT|TRY|PLN|GBP|грн\.?|грив(?:ень|ен|на|ні)?|доллар(?:ов|а)?|долар(?:ів|и|а)?|долл\.?|евро|євро|руб(?:лей|ля)?\.?|сум|тенге|злот(?:ых|их)|₴|€|\$|£|zł)'
WEIGHTS=re.compile(r'(?<![\w.,+\-])(?P<a>'+NUM+r')(?:\s*[-–—/]\s*(?P<b>'+NUM+r'))?\s*(?P<unit>'+WEIGHT_UNIT+r')(?!\w)',re.I)
PRICES=re.compile(r'(?<![\w.,+\-])(?P<amount>'+NUM+r')\s*(?P<currency>'+CURRENCY+r')(?!\w)(?P<basis>\s*(?:/|за\s+|per\s+)(?:км|km|тонн[уы]?|т|t|tons?)(?!\w))?',re.I)
PREFIX_PRICES=re.compile(r'(?<!\w)(?P<currency>'+CURRENCY+r')\s*(?P<amount>'+NUM+r')(?![\w.,])(?P<basis>\s*(?:/|за\s+|per\s+)(?:км|km|тонн[уы]?|т|t|tons?)(?!\w))?',re.I)
LABEL_PRICE=re.compile(r'(?:ставка|ціна|цена|оплата|price|rate)\s*[:=]?\s*(?P<amount>'+NUM+r')(?![\w.,])',re.I)

def folded(s):return re.sub(r'\s+',' ',s).strip().casefold()

def number(s, money=False):
    s=re.sub(r'\s+','',s)
    # A lone separator with three trailing digits is ambiguous for money.
    if money and re.fullmatch(r'\d+[.,]\d{3}',s):return None
    try:return Decimal(s.replace(',','.'))
    except Exception:return None

def currency(s):
    u=s.upper().strip('.'); l=s.casefold().strip('.')
    if u in {'USD','EUR','UAH','RUB','UZS','KZT','TRY','PLN','GBP'}:return u
    for code,pat in [('UAH',r'грн|грив|₴'),('USD',r'долл|долар'),('EUR',r'евро|євро|€'),('RUB',r'руб'),('UZS',r'сум'),('KZT',r'тенге'),('PLN',r'злот|zł'),('GBP',r'£')]:
        if re.search(pat,l):return code
    return None  # $ alone does not identify a national currency.

def select(candidates,hint):
    unique={folded(x['quote']):x for x in candidates}
    options=list(unique.values())
    if len(options)==1:return options[0]
    if hint:
        # Match an actual quoted span, not equality of bare numbers across offers.
        matching=[x for x in options if folded(hint)==folded(x['quote'])]
        if len(matching)==1:return matching[0]
    return None

def normalize_quantities(text,weight_hint=None,price_hint=None):
    out={'weight_kg':None,'weight_min_kg':None,'weight_max_kg':None,
         'price':None,'currency':None,'price_basis':'unspecified','weight_evidence':None,'price_evidence':None}
    reasons=[]; weights=[]
    for m in WEIGHTS.finditer(text):
        a=number(m['a']);b=number(m['b']) if m['b'] else None
        factor=1 if re.match(r'кг|kg|килограмм|кілограм',m['unit'],re.I) else 1000
        if a is None or a<=0 or (b is not None and b<=0):continue
        weights.append({'quote':m[0],'a':a*factor,'b':b*factor if b is not None else None})
    w=select(weights,weight_hint)
    if w:
        out['weight_evidence']=w['quote']
        if w['b'] is not None:
            out['weight_min_kg']=str(min(w['a'],w['b']));out['weight_max_kg']=str(max(w['a'],w['b']))
            reasons.append('weight_range_requires_review')
        elif w['a']==int(w['a']):out['weight_kg']=int(w['a'])
        else:reasons.append('fractional_kg_requires_review')
        if max(w['a'],w['b'] or w['a'])>60000:reasons.append('weight_over_60t')
    elif weights:reasons.append('multiple_weight_values')
    prices=[]
    for regex in (PRICES,PREFIX_PRICES):
        for m in regex.finditer(text):
            amount=number(m['amount'],money=True)
            prices.append({'quote':m[0],'amount':amount,'currency':currency(m['currency']),'basis':m['basis'] or ''})
    # Label-only amounts are used only if no explicitly-currencied amount exists.
    if not prices:
        for m in LABEL_PRICE.finditer(text):
            prices.append({'quote':m[0],'amount':number(m['amount'],money=True),'currency':None,'basis':''})
    p=select(prices,price_hint)
    if p:
        out['price_evidence']=p['quote'];out['currency']=p['currency']
        if p['amount'] is not None and p['amount']>0:out['price']=str(p['amount'])
        else:reasons.append('ambiguous_or_invalid_price')
        if re.search(r'км|km',p['basis'],re.I):out['price_basis']='per_km'
        elif p['basis'].strip():out['price_basis']='per_tonne'
        if out['price_basis']!='unspecified':reasons.append('unit_rate_not_trip_total')
        if not out['currency']:reasons.append('currency_missing_or_ambiguous')
    elif prices:reasons.append('multiple_price_values')
    elif price_hint:reasons.append('unlabelled_amount_not_a_confirmed_price')
    return out,reasons
