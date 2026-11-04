"""Read-only Odds API v4 adapter and strict offline imports. No betting endpoints."""
from pathlib import Path
from datetime import timedelta
import hashlib
import json
import os
import time
import uuid
import pandas as pd
import requests
from .ensemble import timestamp
from .market_math import decimal_odds
from .odds_matching import team,nfl_season
from .odds_store import append,rows,key,utc_now

ENDPOINT='https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds'
KINDS={'live','verified_archive','unverified','synthetic'}
RULE_DEFAULTS={'scope':'unknown','tie_rule':'unknown','cancel_rule':'manual_review','reschedule_rule':'manual_review','rules_reference':None}


def reference(value):
    value=str(value or '').strip()
    if not value:raise ValueError('A source reference is required')
    if any(token in value.casefold() for token in ['apikey=','api_key=','token=','authorization=']):raise ValueError('Source references must not contain credentials')
    return value


def normalized_pair(record,received_at,raw_fingerprint,source_kind):
    if source_kind not in KINDS:raise ValueError('Unknown odds provenance kind')
    f=dict(record);required=['provider','bookmaker','event_id','market','home_team','away_team','kickoff','snapshot_at','quote_at','season','source_reference','home_price','away_price','odds_format']
    if any(k not in f or f[k] is None or str(f[k]).strip()=='' for k in required):raise ValueError('Odds market requires identities, both sides, aware timestamps, season and provenance')
    if f['market']!='h2h':raise ValueError('Only two-sided h2h moneylines are supported')
    f['home_team']=team(f['home_team']);f['away_team']=team(f['away_team'])
    if f['home_team']==f['away_team']:raise ValueError('A market must contain two distinct teams')
    at={n:timestamp(f[n]) for n in ['kickoff','snapshot_at','quote_at']};received_at=timestamp(received_at)
    if at['quote_at']>at['snapshot_at'] or at['snapshot_at']>received_at:raise ValueError('Quote/snapshot timestamps cannot be later than their observation')
    if int(f['season'])!=nfl_season(at['kickoff']):raise ValueError('NFL season conflicts with kickoff')
    if f.get('availability','quoted') not in ['quoted','suspended','unavailable']:raise ValueError('Unknown market availability')
    rules={**RULE_DEFAULTS,**{k:f[k] for k in RULE_DEFAULTS if k in f and f[k] is not None}}
    if rules['scope'] not in ['unknown','game_including_overtime'] or rules['tie_rule'] not in ['unknown','push','void','loss'] or rules['cancel_rule'] not in ['manual_review','void_on_cancel'] or rules['reschedule_rule'] not in ['manual_review','void_on_change','action_after_reschedule']:raise ValueError('Unsupported market settlement rule')
    if any(rules[k]!=RULE_DEFAULTS[k] for k in ['scope','tie_rule','cancel_rule','reschedule_rule']):reference(rules['rules_reference'])
    result={k:str(f[k]).strip() for k in ['provider','bookmaker','event_id','market']}
    result.update({'home_team':f['home_team'],'away_team':f['away_team'],'season':int(f['season']),**{n:v.isoformat() for n,v in at.items()},'source_reference':reference(f['source_reference']),'source_kind':source_kind,'home_decimal':str(decimal_odds(f['home_price'],f['odds_format'])),'away_decimal':str(decimal_odds(f['away_price'],f['odds_format'])),'home_quoted':str(f['home_price']),'away_quoted':str(f['away_price']),'odds_format':f['odds_format'],'availability':f.get('availability','quoted'),'snapshot_scope':f.get('snapshot_scope','market_pair'),'closing_status':f.get('closing_status','unknown'),'closing_reference':f.get('closing_reference'),**rules})
    if result['closing_status'] not in ['unknown','last_observed','verified_final_pregame']:raise ValueError('Invalid closing classification')
    if result['closing_status']=='verified_final_pregame':reference(result['closing_reference'])
    result['pregame_quote']=at['quote_at']<at['kickoff'] and at['snapshot_at']<at['kickoff']
    result['quote_id']=key(result)
    result.update(received_at=received_at.isoformat(),created_at=received_at.isoformat(),raw_fingerprint=raw_fingerprint)
    return result


def parse_v4(payload,received_at,raw_fingerprint,source_kind='live',rules=None):
    """Current list or documented historical {timestamp,data} envelope."""
    rules=rules or {};archive_at=None
    if isinstance(payload,dict):
        if set(['timestamp','data'])-set(payload):raise ValueError('Expected Odds API event list or timestamp/data historical envelope')
        archive_at=timestamp(payload['timestamp']);events=payload['data']
    else:events=payload
    if not isinstance(events,list):raise ValueError('Provider events must be a JSON list')
    quotes=[];issues=[]
    for event in events:
        if not isinstance(event,dict) or set(['id','commence_time','home_team','away_team','bookmakers'])-set(event):raise ValueError('Provider event schema missing id, kickoff, teams or bookmakers')
        if event.get('sport_key','americanfootball_nfl')!='americanfootball_nfl':raise ValueError('Only NFL provider events are supported')
        if not isinstance(event['bookmakers'],list):raise ValueError('Bookmakers must be a list')
        if not event['bookmakers']:issues.append({'event_id':event['id'],'reason':'No bookmaker markets available'})
        for book in event['bookmakers']:
            if not isinstance(book,dict) or not book.get('key') or not isinstance(book.get('markets'),list):raise ValueError('Bookmaker schema missing key/markets')
            for market in book['markets']:
                if not isinstance(market,dict):
                    issues.append({'event_id':event['id'],'bookmaker':book['key'],'reason':'Malformed market object'});continue
                if market.get('key')!='h2h':continue
                try:
                    outcomes=market['outcomes']
                    if len(outcomes)!=2 or len({team(o['name']) for o in outcomes})!=2:raise ValueError('Expected exactly two team outcomes; draws/three-way markets unsupported')
                    by_team={team(o['name']):o['price'] for o in outcomes};home=team(event['home_team']);away=team(event['away_team'])
                    if set(by_team)!={home,away}:raise ValueError('Selections do not match event teams')
                    quote_at=market.get('last_update') or book.get('last_update')
                    if not quote_at:raise ValueError('No provider quote timestamp')
                    at=archive_at or timestamp(quote_at)
                    record={'provider':'synthetic_fixture_v4_schema' if source_kind=='synthetic' else 'the_odds_api_v4','bookmaker':book['key'],'event_id':str(event['id']),'market':'h2h','home_team':home,'away_team':away,'kickoff':event['commence_time'],'season':nfl_season(event['commence_time']),'snapshot_at':at.isoformat(),'quote_at':quote_at,'source_reference':'fixture://m8/provider_v4.json' if source_kind=='synthetic' else ENDPOINT if archive_at is None else 'https://api.the-odds-api.com/v4/historical/sports/americanfootball_nfl/odds','home_price':by_team[home],'away_price':by_team[away],'odds_format':'american','availability':'suspended' if market.get('active') is False else 'quoted','snapshot_scope':'archive' if archive_at is not None else ('market_last_update' if market.get('last_update') else 'bookmaker_last_update'),**rules.get(book['key'],{})}
                    quotes.append(normalized_pair(record,received_at,raw_fingerprint,source_kind))
                except (KeyError,TypeError,ValueError) as exc:issues.append({'event_id':event['id'],'bookmaker':book['key'],'reason':str(exc)})
    return quotes,issues


def parse_csv(content,received_at,raw_fingerprint,source_kind):
    from io import BytesIO
    frame=pd.read_csv(BytesIO(content),dtype=str,keep_default_na=False)
    required={'provider','bookmaker','event_id','market','selection','price','odds_format','home_team','away_team','kickoff','season','snapshot_at','quote_at','source_reference'}
    if required-set(frame):raise ValueError(f'Historical CSV missing columns: {sorted(required-set(frame))}')
    group_columns=sorted(required-{'selection','price'})
    extra=[c for c in list(RULE_DEFAULTS)+['availability','closing_status','closing_reference'] if c in frame]
    quotes=[]
    for _,g in frame.groupby(group_columns+extra,dropna=False,sort=False):
        if len(g)!=2:raise ValueError('Each CSV market pair needs exactly two coherent selection rows')
        f=g.iloc[0].to_dict();prices={team(r.selection):r.price for r in g.itertuples()}
        if len(prices)!=2 or set(prices)!={team(f['home_team']),team(f['away_team'])}:raise ValueError('CSV market selections must match the home and away team')
        f.update(home_price=prices[team(f['home_team'])],away_price=prices[team(f['away_team'])])
        kind='synthetic' if str(f['provider']).startswith('synthetic') or str(f['source_reference']).startswith('fixture://') else source_kind
        quotes.append(normalized_pair(f,received_at,raw_fingerprint,kind))
    return quotes,[]


def ingest(db,content,format='json',source_kind='verified_archive',rules=None):
    if isinstance(content,str):content=content.encode()
    raw_fingerprint=hashlib.sha256(content).hexdigest();received_at=utc_now()
    if format=='csv':quotes,issues=parse_csv(content,received_at,raw_fingerprint,source_kind)
    elif format=='json':
        payload=json.loads(content)
        if isinstance(payload,dict) and payload.get('synthetic') is True:
            source_kind='synthetic';rules=rules or payload.get('rules');payload=payload['data']
        quotes,issues=parse_v4(payload,received_at,raw_fingerprint,source_kind,rules)
    else:raise ValueError('Only JSON and CSV odds imports are supported')
    if quotes and all(q['source_kind']=='synthetic' for q in quotes):source_kind='synthetic'
    # Validation completes before publishing any active normalized records.
    with db:
        db.execute('INSERT OR IGNORE INTO raw VALUES(?,?)',(raw_fingerprint,content))
        for q in quotes:append(db,'quotes',q,q['quote_id'],ignore_fields=['created_at','received_at','raw_fingerprint'])
        receipt={'receipt_id':uuid.uuid4().hex,'provider':'local_import','created_at':received_at.isoformat(),'raw_fingerprint':raw_fingerprint,'source_kind':source_kind,'quote_ids':[q['quote_id'] for q in quotes],'issues':issues,'status':'imported'}
        append(db,'receipts',receipt,receipt['receipt_id'])
    return {'raw_fingerprint':raw_fingerprint,'quote_ids':[q['quote_id'] for q in quotes],'issues':issues,'source_kind':source_kind}


class OddsAPIv4:
    def __init__(self,session=None,sleep=time.sleep):self.session=session or requests.Session();self.sleep=sleep

    def fetch(self,db,config,rules=None):
        if config['max_http_attempts'] not in [1,2] or config['minimum_fetch_interval_seconds']<60 or not 0<=config['max_retry_delay_seconds']<=1:
            raise ValueError('M8 fetch policy allows 1–2 attempts, at least 60 seconds between operations, and at most one-second retry waits')
        credential=os.environ.get('ODDS_API_KEY')
        if not credential:raise RuntimeError('ODDS_API_KEY is not configured. Set it locally or import saved CSV/JSON; no request was sent.')
        now=timestamp(utc_now());db.commit();db.execute('BEGIN IMMEDIATE')
        try:
            attempts=[r for r in rows(db,'receipts') if r.get('provider') in ['the_odds_api_v4','odds_rate_guard']]
            if attempts:
                earliest=max(timestamp(r['created_at'])+timedelta(seconds=max(config['minimum_fetch_interval_seconds'],r.get('retry_after_seconds',0))) for r in attempts)
                if now<earliest:raise RuntimeError('Odds fetch cooldown/rate limit is active; inspect quota and wait before explicitly fetching again.')
            reservation={'receipt_id':uuid.uuid4().hex,'provider':'odds_rate_guard','created_at':now.isoformat(),'status':'request_reserved'}
            append(db,'receipts',reservation,reservation['receipt_id']);db.commit()
        except Exception:db.rollback();raise
        for attempt in range(config['max_http_attempts']):
            receipt={'receipt_id':uuid.uuid4().hex,'provider':'the_odds_api_v4','created_at':timestamp(utc_now()).isoformat(),'attempt':attempt+1,'status':'transport_error','quota':{}}
            response=None
            try:
                response=self.session.get(ENDPOINT,params={'apiKey':credential,'regions':'us','markets':'h2h','oddsFormat':'american','dateFormat':'iso'},timeout=(5,20))
                receipt['status_code']=response.status_code
                for header in ['x-requests-remaining','x-requests-used','x-requests-last']:
                    value=response.headers.get(header)
                    if value is not None and str(value).isdigit():receipt['quota'][header]=int(value)
                retry=response.headers.get('Retry-After','0')
                receipt['retry_after_seconds']=min(int(retry),86400) if str(retry).isdigit() else 300 if response.status_code==429 else 0
                if response.status_code==200:
                    if credential.encode() in response.content:raise ValueError('Provider response unexpectedly contains credential material')
                    result=ingest(db,response.content,'json','live',rules)
                    receipt.update(status='success',raw_fingerprint=result['raw_fingerprint'],issues=result['issues'])
                else:receipt['status']='http_error'
            except requests.RequestException:
                pass  # Never log an exception URL, which can contain the API credential.
            except (ValueError,TypeError):receipt['status']='schema_error'
            with db:append(db,'receipts',receipt,receipt['receipt_id'])
            if receipt['status']=='success':return receipt
            retryable=response is None or response.status_code in [429,500,502,503,504]
            delay=max(1,receipt.get('retry_after_seconds',0))
            if not retryable or delay>config['max_retry_delay_seconds'] or attempt+1>=config['max_http_attempts']:break
            self.sleep(delay)
        raise RuntimeError(f"Odds provider fetch failed ({receipt['status']}, HTTP {receipt.get('status_code','unavailable')}); cached quotes remain intact. Check credentials, network and quota.")
