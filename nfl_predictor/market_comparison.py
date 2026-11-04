"""As-of paired markets and forecasts. Missing data is excluded, never invented."""
from datetime import timedelta
import pandas as pd
from .ensemble import timestamp
from .market_math import market_pair,value_at_probability
from .odds_matching import match
from .odds_store import append,rows,key,utc_now
from .market_forecasts import FAMILIES


def audit_matches(db,schedules,config,asof=None,mode='prospective'):
    quotes=rows(db,'quotes');event_sets={}
    for q in quotes:
        if asof is not None and (timestamp(q['snapshot_at'])>timestamp(asof) or (mode=='prospective' and timestamp(q['received_at'])>timestamp(asof))):continue
        signature=(q['provider'],q['season'],q['home_team'],q['away_team'],q['kickoff'])
        event_sets.setdefault(signature,set()).add(q['event_id'])
    result=[]
    with db:
        for q in quotes:
            audit=match(q,schedules,config['kickoff_tolerance_seconds'])
            signature=(q['provider'],q['season'],q['home_team'],q['away_team'],q['kickoff'])
            if len(event_sets.get(signature,set()))>1:audit.update(status='duplicate_provider_events_review',game_id=None)
            audit['match_id']=key({k:v for k,v in audit.items() if k!='match_id'})
            audit['created_at']=timestamp(utc_now()).isoformat()
            saved=append(db,'matches',audit,audit['match_id'],ignore_fields=['created_at']);result.append(saved)
    return result


def quote_issues(q,decision,config,mode='prospective'):
    decision=timestamp(decision);issues=[]
    if not q['pregame_quote'] or timestamp(q['kickoff'])<=decision:issues.append('not_pregame')
    if timestamp(q['quote_at'])>decision or timestamp(q['snapshot_at'])>decision:issues.append('future_quote_or_snapshot')
    if mode=='prospective' and timestamp(q['received_at'])>decision:issues.append('not_observed_by_decision')
    if mode=='reconstructed' and q['source_kind']=='live' and timestamp(q['received_at'])>decision:issues.append('live_quote_not_observed_by_decision')
    if mode=='reconstructed' and q['source_kind'] not in ['live','verified_archive','synthetic']:issues.append('unverified_historical_provenance')
    if mode=='prospective' and q['source_kind'] in ['synthetic','unverified']:issues.append('not_genuine_verified_odds')
    if decision-timestamp(q['quote_at'])>timedelta(minutes=config['max_quote_age_minutes']):issues.append('stale_quote')
    if q['availability']!='quoted':issues.append('market_'+q['availability'])
    return issues


def forecast_issues(f,decision,kickoff,config,mode='prospective'):
    decision=timestamp(decision);kickoff=timestamp(kickoff);issues=[]
    if timestamp(f['data_cutoff'])>decision:issues.append('future_forecast_information')
    if timestamp(f['training_cutoff'])>=timestamp(f['data_cutoff']):issues.append('in_sample_or_late_model')
    if f['classification']=='genuine_saved_forecast' and timestamp(f['created_at'])>decision:issues.append('not_known_by_decision')
    if mode=='prospective' and (f['classification']!='genuine_saved_forecast' or timestamp(f['created_at'])>decision):issues.append('not_genuinely_issued_by_decision')
    if f['classification']=='genuine_saved_forecast' and not timestamp(f['data_cutoff'])<=timestamp(f['created_at'])<timestamp(f['kickoff']):issues.append('invalid_forecast_issuance_times')
    if decision-timestamp(f['data_cutoff'])>timedelta(hours=config['max_forecast_age_hours']):issues.append('stale_forecast')
    if abs((timestamp(f['kickoff'])-kickoff).total_seconds())>config['kickoff_tolerance_seconds']:issues.append('forecast_schedule_changed')
    return issues


def priority(book,config):
    order=config['bookmaker_priority'];return (order.index(book) if book in order else len(order),book)


def compare_at(db,schedules,forecasts,decision,config,mode='prospective',cohort='manual',game_ids=None):
    if mode not in ['prospective','reconstructed']:raise ValueError('Comparison mode must be prospective or explicitly reconstructed')
    decision=timestamp(decision);audits=audit_matches(db,schedules,config,decision,mode);by_quote={a['quote_id']:a for a in audits}
    quotes=rows(db,'quotes');exclusions=[];eligible=[]
    for q in quotes:
        audit=by_quote[q['quote_id']]
        if audit['status']!='matched':exclusions.append({'quote_id':q['quote_id'],'reasons':[audit['status']]});continue
        gid=audit['game_id']
        if game_ids is not None and gid not in game_ids:continue
        issues=quote_issues(q,decision,config,mode)
        if cohort in config['cohorts']:
            spec=config['cohorts'][cohort];target=timestamp(q['kickoff'])-timedelta(hours=spec['lead_hours'])
            if timestamp(q['snapshot_at'])<target-timedelta(minutes=spec['tolerance_minutes']) or timestamp(q['snapshot_at'])>target:issues.append('outside_cohort_window')
        if issues:exclusions.append({'quote_id':q['quote_id'],'game_id':gid,'reasons':issues});continue
        eligible.append({**q,'game_id':gid,'match_id':audit['match_id']})
    # One latest coherent market per game and bookmaker. Distinct same-time prices
    # are an ambiguity, not an opportunity to choose the more favorable version.
    markets=[]
    groups={}
    for q in eligible:groups.setdefault((q['game_id'],q['bookmaker']),[]).append(q)
    for (gid,book),g in groups.items():
        newest=max((q['snapshot_at'],q['quote_at']) for q in g);current=[q for q in g if (q['snapshot_at'],q['quote_at'])==newest]
        if len({(q['home_decimal'],q['away_decimal'],q['scope'],q['tie_rule']) for q in current})>1:
            exclusions.append({'game_id':gid,'bookmaker':book,'reasons':['conflicting_market_versions']});continue
        markets.append(sorted(current,key=lambda q:(q['provider'],q['quote_id']))[0])
    opportunities=[]
    for q in markets:
        pair=market_pair(q['home_decimal'],q['away_decimal'])
        for family in FAMILIES:
            candidates=[f for f in forecasts if f['game_id']==q['game_id'] and f['model']==family]
            valid=[];candidate_reasons=set()
            for f in candidates:
                reasons=forecast_issues(f,decision,q['kickoff'],config,mode)
                if f['home_team']!=q['home_team'] or f['away_team']!=q['away_team']:reasons.append('forecast_team_mismatch')
                if f['classification']=='synthetic_oos' and q['source_kind']!='synthetic':reasons.append('synthetic_forecast_with_real_market')
                candidate_reasons.update(reasons)
                if not reasons:valid.append(f)
            if not valid:
                exclusions.append({'game_id':q['game_id'],'bookmaker':q['bookmaker'],'model':family,'reasons':['no_valid_asof_forecast']+sorted(candidate_reasons)});continue
            f=max(valid,key=lambda f:(f['data_cutoff'],f['created_at'],f['forecast_id']))
            rules_ok=q['scope']=='game_including_overtime' and q['tie_rule'] in ['push','void'] and bool(q['rules_reference'])
            for side in ['home','away']:
                p=float(f['home_probability']) if side=='home' else 1-float(f['home_probability'])
                value=value_at_probability(p,q[side+'_decimal'])
                sensitivity=[{'probability_shift':shift,'probability':max(0.,min(1.,p+shift)),'ev_per_unit':value_at_probability(max(0.,min(1.,p+shift)),q[side+'_decimal'])['ev_per_unit']} for shift in config['sensitivity_probability_shifts']]
                opportunities.append({'game_id':q['game_id'],'season':q['season'],'week':int(schedules.loc[schedules.game_id.eq(q['game_id']),'week'].iloc[0]),'home_team':q['home_team'],'away_team':q['away_team'],'kickoff':q['kickoff'],'bookmaker':q['bookmaker'],'provider':q['provider'],'source_kind':q['source_kind'],'quote_id':q['quote_id'],'match_id':q['match_id'],'forecast_id':f['forecast_id'],'model':family,'model_version':f['model_version'],'artifact_sha256':f['artifact_sha256'],'forecast_created_at':f['created_at'],'forecast_cutoff':f['data_cutoff'],'quote_at':q['quote_at'],'snapshot_at':q['snapshot_at'],'quote_received_at':q['received_at'],'decision_at':decision.isoformat(),'classification':'prospective_comparison' if mode=='prospective' else 'reconstructed_comparison','cohort':cohort,'side':side,'selection':q[side+'_team'],'decimal_odds':q[side+'_decimal'],'quoted_odds':q[side+'_quoted'],'odds_format':q['odds_format'],'model_probability':p,'market_no_vig_probability':pair['no_vig_'+side],'probability_edge_pp':100*(p-pair['no_vig_'+side]),**pair,**value,'paper_eligible':rules_ok and q['source_kind']!='synthetic' and mode=='prospective','positive_ev_after_minus2pp':value_at_probability(max(0.,p-.02),q[side+'_decimal'])['ev_per_unit']>0,'positive_ev_after_minus5pp':value_at_probability(max(0.,p-.05),q[side+'_decimal'])['ev_per_unit']>0,'ev_threshold_minimum_probabilities':{str(t):value_at_probability(p,q[side+'_decimal'],t)['minimum_probability_for_threshold'] for t in config['thresholds']},'rules_warning':None if rules_ok else 'Unknown/incompatible market scope or tie rules; EV is a conditional scenario only','sensitivity':sensitivity,'source_fingerprints':{'odds_raw':q['raw_fingerprint'],'forecast':f['source_fingerprint'],'artifact':f['artifact_sha256']},'rules':{k:q[k] for k in ['scope','tie_rule','cancel_rule','reschedule_rule','rules_reference']}})
    probabilities_by_matchup={}
    for o in opportunities:probabilities_by_matchup.setdefault((o['game_id'],o['bookmaker'],o['side']),[]).append(o['model_probability'])
    for o in opportunities:
        peers=probabilities_by_matchup[(o['game_id'],o['bookmaker'],o['side'])]
        o['model_disagreement_range_pp']=100*(max(peers)-min(peers))
    return opportunities,exclusions


def choose_books(opportunities,config):
    result=[]
    for gid in sorted({o['game_id'] for o in opportunities}):
        g=[o for o in opportunities if o['game_id']==gid]
        book=min({o['bookmaker'] for o in g},key=lambda b:priority(b,config))
        result.extend(o for o in g if o['bookmaker']==book)
    return result
