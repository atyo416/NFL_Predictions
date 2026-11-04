"""One-unit simulation ledger. No accounts, bankrolls or sportsbook execution."""
from datetime import timedelta
import json
import pandas as pd
from .ensemble import timestamp
from .elo import eligible_at
from .market_math import payout,number,market_pair,value_at_probability
from .market_comparison import compare_at,priority
from .odds_store import append,rows,key,encoded,utc_now


def strategy(config,model='official_logistic',threshold=.03,cohort='manual'):
    if model not in ['official_logistic','boosting','ensemble'] or threshold not in config['thresholds'] or cohort not in ['manual']+list(config['cohorts']):raise ValueError('Use a predefined model, EV threshold and timing cohort')
    if config['stake_units']!=1:raise ValueError('M8 uses fixed one-unit simulated stakes only')
    definition={'protocol':config,'model':model,'threshold':threshold,'cohort':cohort,'stake_units':1.,'kind':'simulation_only','selection_rule':config['selection_rule']}
    definition['strategy_version']='m8-'+key(definition)[:24];return definition


def select(opportunities,definition,config,require_genuine=True):
    chosen=[]
    for gid in sorted({o['game_id'] for o in opportunities}):
        g=[o for o in opportunities if o['game_id']==gid and o['model']==definition['model'] and (o['paper_eligible'] or not require_genuine)]
        if not g:continue
        book=min({o['bookmaker'] for o in g},key=lambda b:priority(b,config));g=[o for o in g if o['bookmaker']==book]
        best=sorted(g,key=lambda o:(-o['ev_per_unit'],0 if o['side']=='home' else 1,o['quote_id']))[0]
        if best['ev_per_unit']>definition['threshold']:chosen.append(best)
    return chosen


def issue(db,schedules,forecasts,config,model='official_logistic',threshold=.03,cohort='manual',dry_run=False,cutoff=None):
    if cutoff is not None:raise ValueError('Paper decisions cannot be backdated or future-dated. Use historical comparison for reconstruction.')
    decision=timestamp(utc_now());definition=strategy(config,model,threshold,cohort)
    opportunities,exclusions=compare_at(db,schedules,forecasts,decision,config,'prospective',cohort)
    if cohort!='manual':
        spec=config['cohorts'][cohort]
        opportunities=[o for o in opportunities if timedelta(hours=spec['lead_hours'])<=timestamp(o['kickoff'])-decision<=timedelta(hours=spec['lead_hours'],minutes=spec['tolerance_minutes'])]
    eligible_games=set(schedules.loc[~schedules.completed,'game_id'])
    opportunities=[o for o in opportunities if o['game_id'] in eligible_games]
    chosen=select(opportunities,definition,config);result=[]
    if dry_run:return {'dry_run':True,'strategy':definition,'would_issue':chosen,'exclusions':exclusions,'saved':0}
    # Serialize opportunity insertion; UNIQUE(slot) enforces idempotence under concurrency.
    db.commit();db.execute('BEGIN IMMEDIATE')
    try:
        append(db,'strategies',definition,definition['strategy_version'])
        for opportunity in chosen:
            created=timestamp(utc_now())
            if created>=timestamp(opportunity['kickoff']):raise ValueError('Game started during paper-decision computation; nothing was issued')
            slot=key([opportunity['game_id'],definition['strategy_version'],cohort])
            existing=db.execute('SELECT payload FROM wagers WHERE slot=?',(slot,)).fetchone()
            if existing:result.append({'status':'already_saved','wager':json.loads(existing['payload'])});continue
            wager={**opportunity,'minimum_probability_for_threshold':value_at_probability(opportunity['model_probability'],opportunity['decimal_odds'],threshold)['minimum_probability_for_threshold'],'wager_id':slot,'strategy_version':definition['strategy_version'],'threshold':threshold,'stake_units':'1','created_at':created.isoformat(),'decision_at':decision.isoformat(),'status':'pending','classification':'genuine_prospective_paper_simulation','executable_price_claim':False}
            db.execute('INSERT INTO wagers VALUES(?,?,?,?)',(slot,slot,created.isoformat(),encoded(wager)))
            result.append({'status':'saved','wager':wager})
        db.commit()
    except Exception:db.rollback();raise
    return {'dry_run':False,'strategy':definition,'records':result,'saved':sum(r['status']=='saved' for r in result),'exclusions':exclusions}


def latest_events(db):
    events=[e for e in rows(db,'events') if e['kind'] in ['settlement','manual_void']]
    superseded={e.get('supersedes') for e in events};latest={}
    for event in events:
        if event['event_id'] in superseded:continue
        if event['wager_id'] in latest:raise ValueError('Conflicting settlement revision heads require review')
        latest[event['wager_id']]=event
    return latest


def void_wager(db,wager_id,reason):
    if not str(reason).strip():raise ValueError('A traceable correction reason is required')
    if not db.execute('SELECT 1 FROM wagers WHERE id=?',(wager_id,)).fetchone():raise ValueError('Unknown paper wager')
    now=timestamp(utc_now()).isoformat();latest=latest_events(db).get(wager_id)
    if latest and latest['kind']=='manual_void' and latest['reason']==reason:return latest
    event={'kind':'manual_void','wager_id':wager_id,'status':'void','profit_units':'0','reason':reason,'created_at':now,'available_at':now,'supersedes':latest['event_id'] if latest else None}
    event['event_id']=key({k:v for k,v in event.items() if k!='created_at'})
    with db:append(db,'events',event,event['event_id'])
    return event


def settle(db,schedules,config):
    now=timestamp(utc_now());games=schedules.set_index('game_id');events=[]
    db.commit();db.execute('BEGIN IMMEDIATE')
    try:
        latest=latest_events(db)
        for w in rows(db,'wagers'):
            old=latest.get(w['wager_id'])
            if old and old['kind']=='manual_void':continue
            if w['game_id'] not in games.index:continue
            g=games.loc[w['game_id']];rules=w['rules'];state=str(g.get('status','')).lower();status=None;available=None
            moved=abs((timestamp(g.kickoff)-timestamp(w['kickoff'])).total_seconds())>config['kickoff_tolerance_seconds']
            if state in ['canceled','cancelled']:
                status='void' if rules['cancel_rule']=='void_on_cancel' else 'review';available=now
            elif moved and rules['reschedule_rule']!='action_after_reschedule':
                status='void' if rules['reschedule_rule']=='void_on_change' else 'review';available=now
            else:
                available=eligible_at(g.to_dict())
                if pd.isna(available) or available>=now:continue
                if g.home_team!=w['home_team'] or g.away_team!=w['away_team']:status='review'
                elif g.home_score==g.away_score:status=rules['tie_rule'] if rules['tie_rule'] in ['push','void'] else 'review'
                else:
                    winner=g.home_team if g.home_score>g.away_score else g.away_team
                    status='win' if w['selection']==winner else 'loss'
            result={'kind':'settlement','wager_id':w['wager_id'],'status':status,'profit_units':str(payout(w['stake_units'],w['decimal_odds'],status)) if status!='review' else None,'home_score':float(g.home_score) if pd.notna(g.home_score) else None,'away_score':float(g.away_score) if pd.notna(g.away_score) else None,'result_kickoff':timestamp(g.kickoff).isoformat(),'available_at':timestamp(available).isoformat(),'rules_reference':rules['rules_reference']}
            # Review/cancel observations use actual capture time but idempotence is semantic.
            comparable=lambda e:{k:v for k,v in e.items() if k not in ['created_at','event_id','supersedes','available_at']}
            if old and comparable(old)==comparable(result):continue
            result.update(created_at=now.isoformat(),supersedes=old['event_id'] if old else None)
            result['event_id']=key({k:v for k,v in result.items() if k!='created_at'})
            append(db,'events',result,result['event_id']);events.append(result)
        db.commit()
    except Exception:db.rollback();raise
    return events


def ledger_view(db):
    events=latest_events(db);result=[]
    for w in rows(db,'wagers'):
        event=events.get(w['wager_id'])
        result.append({**w,'status':event['status'] if event else 'pending','profit_units':event.get('profit_units') if event else None,'settlement':event})
    return result


def performance(wagers):
    settled=[w for w in wagers if w['status'] in ['win','loss','push','void']]
    stake=sum(float(w['stake_units']) for w in settled);profits=sum(float(w['profit_units']) for w in settled)
    batches={}
    for w in settled:batches.setdefault(w['settlement']['available_at'],0.);batches[w['settlement']['available_at']]+=float(w['profit_units'])
    equity=peak=drawdown=0.
    for at,profit in sorted(batches.items()):equity+=profit;peak=max(peak,equity);drawdown=max(drawdown,peak-equity)
    longest=streak=0
    for w in sorted(settled,key=lambda w:(w['settlement']['available_at'],w['game_id'],w['wager_id'])):
        if w['status']=='loss':streak+=1;longest=max(longest,streak)
        elif w['status']=='win':streak=0
    return {'wagers':len(wagers),'unique_games':len({w['game_id'] for w in wagers}),'wins':sum(w['status']=='win' for w in wagers),'losses':sum(w['status']=='loss' for w in wagers),'pushes':sum(w['status']=='push' for w in wagers),'voids':sum(w['status']=='void' for w in wagers),'pending':sum(w['status']=='pending' for w in wagers),'review':sum(w['status']=='review' for w in wagers),'total_stake_units':sum(float(w['stake_units']) for w in wagers),'settled_stake_units':stake,'net_simulated_profit_units':profits if settled else None,'realized_roi':profits/stake if stake else None,'average_model_ev':sum(w['ev_per_unit'] for w in wagers)/len(wagers) if wagers else None,'maximum_drawdown_units':drawdown if settled else None,'longest_losing_streak':longest if settled else None,'roi_convention':'Settled stake includes refunded push/void entries; pending stakes excluded','drawdown_convention':'Aggregate equal availability timestamps before equity updates; losing streak ties use game ID; pushes do not reset streak'}


def closing_line(wager,quotes,matched,config):
    valid=[];kickoff=timestamp(wager['kickoff'])
    for q in quotes:
        if q['source_kind']=='synthetic' and wager.get('source_kind')!='synthetic':continue
        if q['provider']!=wager['provider'] or q['bookmaker']!=wager['bookmaker'] or matched.get(q['quote_id'])!=wager['game_id']:continue
        if q['availability']!='quoted':continue
        if q['closing_status']!='verified_final_pregame' or not q['closing_reference']:continue
        if q['scope']!=wager['rules']['scope'] or q['tie_rule']!=wager['rules']['tie_rule']:continue
        at=timestamp(q['snapshot_at'])
        if not timestamp(wager['snapshot_at'])<=at<kickoff or kickoff-at>timedelta(minutes=config['closing_window_minutes']) or not q['pregame_quote']:continue
        valid.append(q)
    if not valid:return {'wager_id':wager['wager_id'],'status':'unavailable_verified_closing'}
    close=max(valid,key=lambda q:(q['snapshot_at'],q['quote_id']));side='home' if close['home_team']==wager['selection'] else 'away'
    entry=number(wager['decimal_odds']);price=number(close[side+'_decimal']);pair=market_pair(close['home_decimal'],close['away_decimal'])
    return {'wager_id':wager['wager_id'],'status':'verified_same_book_closing','entry_at':wager['decision_at'],'closing_at':close['snapshot_at'],'entry_decimal':float(entry),'closing_decimal':float(price),'price_improvement_ratio':float(entry/price-1),'decimal_difference':float(entry-price),'no_vig_movement':pair['no_vig_'+side]-wager['market_no_vig_probability'],'closing_quote_id':close['quote_id'],'closing_reference':close['closing_reference'],'interpretation':'Descriptive CLV, not evidence of profitability'}
