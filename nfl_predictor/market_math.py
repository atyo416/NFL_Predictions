"""Controlled decimal moneyline mathematics; no wagering execution."""
from decimal import Decimal,InvalidOperation,localcontext
import math


def number(value):
    if isinstance(value,bool) or value is None:raise ValueError('A finite numeric value is required')
    try:n=Decimal(str(value))
    except (InvalidOperation,ValueError):raise ValueError('Invalid numeric representation') from None
    if not n.is_finite():raise ValueError('A finite numeric value is required')
    return n


def decimal_odds(value,odds_format='american'):
    n=number(value)
    if odds_format=='american':
        if n!=n.to_integral_value() or abs(n)<100:raise ValueError('American odds must be canonical integers <= -100 or >= +100')
        with localcontext() as context:
            context.prec=28;result=1+n/100 if n>0 else 1+100/abs(n)
    elif odds_format=='decimal':result=n
    else:raise ValueError('Only American and decimal moneylines are supported')
    if result<=1 or not math.isfinite(float(result)):raise ValueError('Decimal odds must be finite and exceed one')
    return result


def implied(value,odds_format='american'):return float(1/decimal_odds(value,odds_format))


def market_pair(home_decimal,away_decimal):
    h=decimal_odds(home_decimal,'decimal');a=decimal_odds(away_decimal,'decimal')
    if h<=1 or a<=1:raise ValueError('A valid two-sided market is required')
    raw_h=1/h;raw_a=1/a;overround=raw_h+raw_a
    return {'implied_home':float(raw_h),'implied_away':float(raw_a),'overround':float(overround),'bookmaker_margin':float(overround-1),'no_vig_home':float(raw_h/overround),'no_vig_away':float(raw_a/overround),'underround':overround<1}


def value_at_probability(probability,price,threshold=0):
    p=number(probability);d=decimal_odds(price,'decimal');threshold=number(threshold)
    if not 0<=p<=1 or d<=1:raise ValueError('Probability must lie in [0,1] and price must exceed one')
    ev=p*d-1;break_even=1/d
    result={'ev_per_unit':float(ev),'expected_roi_percent':float(100*ev),'break_even_probability':float(break_even),'probability_minus_break_even':float(p-break_even),'minimum_probability_for_threshold':float((1+threshold)/d)}
    if not all(math.isfinite(v) for v in result.values()):raise ValueError('Moneyline calculation exceeds supported finite numeric range')
    return {**result,'interpretation':'Conditional binary/no-tie model scenario; not verified profitability or executable pricing'}


def payout(stake,price,status):
    stake=number(stake);price=decimal_odds(price,'decimal')
    if stake<=0 or price<=1:raise ValueError('Positive stake and valid price required')
    if status=='win':return stake*(price-1)
    if status=='loss':return -stake
    if status in ['push','void']:return Decimal(0)
    raise ValueError('Unsettled or unknown payout status')
