"""Manual 24-hour checkpoint operations, isolated from prior forecast ledgers."""
from pathlib import Path
import json
import uuid
import numpy as np
import pandas as pd
from .ensemble import timestamp
from .ensemble_forecasts import _append, _read, records, grade, probabilities, utc_now
from .ensemble_registry import load_ensemble
from .elo import regular_games
from .feature_engineering import build
from .market_forecasts import ForecastRepository
from .odds_store import key, read_only_rows
from .evaluation import evaluate, buckets
from .analysis import paired_intervals
from .reporting import table


def checkpoint(kickoff,now,tolerance=60):
    if not 0<=tolerance<=1440:raise ValueError('Tolerance must be 0–1440 minutes')
    kickoff=timestamp(kickoff);now=timestamp(now);target=kickoff-pd.Timedelta(hours=24)
    state='upcoming' if now<target-pd.Timedelta(minutes=tolerance) else 'on_time' if now<=target else 'missed'
    if now>=kickoff:state='started'
    return target,state


def plan(schedules,directory,tolerance=60):
    now=utc_now();saved=records(directory);rows=[]
    for g in regular_games(schedules).to_dict('records'):
        if g['completed']:continue
        target,state=checkpoint(g['kickoff'],now,tolerance)
        prior=[f for f in saved if f['game_id']==g['game_id']]
        same=[f for f in prior if timestamp(f['kickoff'])==g['kickoff']]
        rows.append({'game_id':g['game_id'],'kickoff':g['kickoff'].isoformat(),'target_checkpoint':target.isoformat(),
                     'state':state,'issued_cohorts':','.join(sorted({f['cohort'] for f in same})),
                     'schedule_changed':bool(prior and not same)})
    return rows


def infer(root,data,schedules,metrics,game,cutoff):
    """Use current champion and the previously issued frozen M7 policy, never refit."""
    root=Path(root);data=Path(data);result={};issues=[];repo=ForecastRepository(root,data)
    try:
        from .model import load
        champion=load(root/'models/production.joblib')
        if timestamp(champion['training_cutoff'])>=cutoff:raise ValueError('Champion training cutoff is too late')
        f=build(schedules[schedules.season.ge(2018)],metrics,cutoff,game_ids=[game['game_id']])
        p=float(champion['pipeline'].predict_proba(f[champion['features']])[0,1])
        _,path,sha=repo.artifact(champion['version'])
        result['official_logistic']={'probability':p,'version':champion['version'],'artifact_path':path,'artifact_sha256':sha}
    except (ValueError,FileNotFoundError,KeyError) as exc:issues.append('official_logistic: '+str(exc))
    try:
        pinned=json.loads((root/'config/m8_protocol.json').read_text())['frozen_m7_policy']
        prior=[f for f in records(data/'m7/experimental_forecasts') if f['ensemble_method']==pinned and f['season']==game['season']]
        if not prior:raise ValueError('No previously issued artifact for the frozen policy/season; no historical substitution')
        version=max(prior,key=lambda f:f['created_at'])['ensemble_version']
        ensemble,bases,_=load_ensemble(root/'models/registry',version)
        config=json.loads((root/'config/m7_protocol.json').read_text())
        frame,_=probabilities(schedules,metrics,ensemble,bases,config,cutoff,cutoff,game['game_id'])
        row=frame.iloc[0]
        for name,p,v in [('boosting',row.p_boosting,bases['boosting']['version']),('ensemble',row.ensemble_probability,version)]:
            _,path,sha=repo.artifact(v);result[name]={'probability':float(p),'version':v,'artifact_path':path,'artifact_sha256':sha}
    except (ValueError,FileNotFoundError,KeyError,IndexError) as exc:issues.append('experimental artifacts: '+str(exc))
    return result,issues


def issue(root,data,schedules,metrics,directory,tolerance=60,late=False,inference=None):
    inference=inference or infer;run=uuid.uuid4().hex;actions=[]
    for g in regular_games(schedules).to_dict('records'):
        if g['completed'] or str(g.get('status','')).lower() in ['postponed','suspended','canceled','cancelled','in_progress','in progress']:continue
        now=utc_now();target,state=checkpoint(g['kickoff'],now,tolerance)
        cohort='24h' if state=='on_time' else 'late' if state=='missed' and late else None
        slot=key([g['game_id'],g['kickoff'].isoformat(),cohort])
        if cohort and (Path(directory)/'forecasts'/(slot+'.json')).exists():continue
        if state in ['missed','started']:
            _append(Path(directory)/'checkpoints',key([g['game_id'],g['kickoff'].isoformat(),'missed']),
                    {'game_id':g['game_id'],'kickoff':g['kickoff'].isoformat(),'target_checkpoint':target.isoformat(),'state':'missed','created_at':now.isoformat()}) if not any(f['game_id']==g['game_id'] and f['cohort']=='24h' and f['kickoff']==g['kickoff'].isoformat() for f in records(directory)) else None
        if not cohort:continue
        values,issues=inference(root,data,schedules,metrics,g,now)
        created=utc_now();_,final_state=checkpoint(g['kickoff'],created,tolerance)
        if created>=g['kickoff'] or (cohort=='24h' and final_state!='on_time'):issues.append('Issuance window closed during computation');values={}
        actions.append({'game_id':g['game_id'],'models':list(values),'issues':issues})
        if not values:continue
        for value in values.values():
            if not np.isfinite(value['probability']) or not 0<=value['probability']<=1:raise ValueError('Invalid probability')
        payload={'kind':'m83_checkpoint_forecast','classification':'genuinely_issued','forecast_id':slot,
            'game_id':g['game_id'],'season':int(g['season']),'week':int(g['week']),'home_team':g['home_team'],'away_team':g['away_team'],
            'kickoff':g['kickoff'].isoformat(),'target_checkpoint':target.isoformat(),'created_at':created.isoformat(),
            'data_cutoff':now.isoformat(),'cohort':cohort,'tolerance_minutes':tolerance,'run_id':run,
            'forecast_source':'current_cached_inference','models':values,'exclusions':issues}
        _append(Path(directory)/'forecasts',slot,payload)
    return actions


def comparison(directory,schedules):
    saved=records(directory);events=[_read(p) for p in (Path(directory)/'results').glob('*.json')];latest={}
    for e in sorted(events,key=lambda e:e['graded_at']):latest[e['forecast_id']]=e
    current=schedules.set_index('game_id');rows=[];excluded=0
    for f in saved:
        if f['classification']!='genuinely_issued' or not timestamp(f['data_cutoff'])<=timestamp(f['created_at'])<timestamp(f['kickoff']):raise ValueError('Invalid prospective forecast')
        if f['game_id'] not in current.index or timestamp(current.loc[f['game_id'],'kickoff'])!=timestamp(f['kickoff']):excluded+=1;continue
        e=latest.get(f['forecast_id'])
        if e and e['result'] in [0,1]:
            for name,v in f['models'].items():rows.append({'game_id':f['game_id'],'season':f['season'],'week':f['week'],'cohort':f['cohort'],'model':name,'probability':v['probability'],'target':int(e['result'])})
    frame=pd.DataFrame(rows);summary=[];paired=[];calibration=[]
    if len(frame):
        for (cohort,name),g in frame.groupby(['cohort','model']):
            summary.append({'cohort':cohort,'model':name,'sample':'individual',**evaluate(g.target,g.probability)})
            if len(g)>=100:calibration.extend(buckets(g.target,g.probability).assign(cohort=cohort,model=name).to_dict('records'))
        for cohort,g in frame.groupby('cohort'):
            # Require all three models, rather than changing the comparison membership.
            ids=g.groupby('game_id').model.nunique();common=g[g.game_id.isin(ids[ids.eq(3)].index)]
            if len(common):
                for name,h in common.groupby('model'):summary.append({'cohort':cohort,'model':name,'sample':'three_way_matched',**evaluate(h.target,h.probability)})
                paired.append(paired_intervals(common,reference='official_logistic').assign(cohort=cohort))
    return {'forecasts':len(saved),'graded':len(latest),'pending':len(saved)-len(latest),
            'ties':sum(e['result']==.5 for e in latest.values()),'schedule_change_exclusions':excluded,
            'metrics':summary,'calibration':calibration,'paired':pd.concat(paired).to_dict('records') if paired else []}


def market_matches(forecasts,quotes,config):
    from .market_comparison import quote_issues
    matches=[]
    for f in forecasts:
        decision=timestamp(f['created_at']);cutoff=timestamp(f['data_cutoff'])
        for q in quotes:
            if (q['home_team'],q['away_team'],timestamp(q['kickoff']))!=(f['home_team'],f['away_team'],timestamp(f['kickoff'])):continue
            if any(timestamp(q[k])>cutoff for k in ['received_at','quote_at','snapshot_at']):continue
            if not quote_issues(q,decision,config):matches.append({'forecast_id':f['forecast_id'],'quote_id':q['quote_id'],'bookmaker':q['bookmaker']})
    return matches


def weekly(root,data,dry_run=False,report_only=False,include_odds=False,tolerance=60,late=False):
    from .spread_benchmark import load_compact
    root=Path(root);data=Path(data);directory=data/'m83';now=utc_now()
    s,m,sources=load_compact(data)
    future=[x for x in sources if x.get('retrieved_at') and timestamp(x['retrieved_at'])>now]
    if future:raise ValueError('Cache retrieval timestamp lies in the future')
    actions=plan(s,directory,tolerance);issues=[];issued=[]
    freshness=now-timestamp(sources[-1]['retrieved_at'])
    if freshness>pd.Timedelta(hours=24):issues.append('Football cache is older than 24h; refresh with update before issuing')
    if dry_run:return {'dry_run':True,'checkpoints':actions,'writes':0}
    if not report_only:
        if freshness<=pd.Timedelta(hours=24):issued=issue(root,data,s,m,directory,tolerance,late)
        if include_odds:
            from .odds_provider import OddsAPIv4
            from .odds_store import connect
            try:
                db=connect(data/'m8/lab.db')
                try:OddsAPIv4().fetch(db,json.loads((root/'config/m8_protocol.json').read_text()))
                finally:db.close()
            except (ValueError,RuntimeError) as exc:issues.append('Optional odds unavailable: '+str(exc))
        grade(s,directory)
    result=comparison(directory,s);quotes=read_only_rows(data/'m8/lab.db','quotes')
    config=json.loads((root/'config/m8_protocol.json').read_text());matches=market_matches(records(directory),quotes,config)
    result.update(checkpoints=plan(s,directory,tolerance),actions=issued,issues=issues,market_quotes=len(quotes),timestamp_matches=len(matches),
                  latest_successful_run=max([_read(p)['observed_at'] for p in (directory/'runs').glob('*.json')],default=None),previous_m7_forecasts=len(records(data/'m7/experimental_forecasts')),data_retrieval=sources[-1]['retrieved_at'],observed_at=now.isoformat())
    if not report_only:_append(directory/'runs',uuid.uuid4().hex,result)
    lines=['# M8.3 prospective forecast tracking','',
           'Default on-time cohort: 25–24 hours before scheduled kickoff (60-minute early tolerance). Late issuance requires --late and stays separate. UTC throughout; actual wall clock controls issuance. Changed kickoff creates a distinct slot; old forecasts remain immutable and are excluded from current-schedule comparisons. Older M7 forecasts retain their original cohort.','',
           f"Existing M7 forecasts: {result['previous_m7_forecasts']}. New checkpoint forecasts: {result['forecasts']}; graded: {result['graded']}; pending: {result['pending']}; ties: {result['ties']}. No newly graded games." if not result['graded'] else str(result), '',
           f"Market observations: {len(quotes)}; timestamp-compatible matches: {len(matches)}. Capture/import, quote and snapshot must precede the feature cutoff; historical imports cannot establish earlier availability.",'',
           '## Model performance','',table(pd.DataFrame(result['metrics'])) if result['metrics'] else 'No eligible graded binary observations; accuracy, Brier and log loss are unavailable. No results or profitability are inferred.','',
           table(pd.DataFrame(result['paired'])) if result['paired'] else 'No three-model matched graded sample for paired comparisons.','',
           'Calibration requires at least 100 binary games per cohort; smaller samples are withheld. Three-way comparisons require identical games and cohort; repeated forecasts are not independent. No selection or promotion occurs.','',
           '## Operational snapshot','', '```json',json.dumps(result,indent=2,default=str),'```','',
           'Refresh first with the existing update command. No scheduler runs. Cache retrieval times establish local observation, not verified original source publication. Historical revisions remain a data-vintage limitation. Missing experimental artifacts are reported without historical substitution; missing odds do not block issuance. Report-only never issues or grades. Dry-run makes no writes, including reports.','',
           'Windows / Python 3.12 acceptance: `python -m pytest -q tests/test_m83.py`, then `python -m nfl_predictor.cli weekly-m83 --dry-run`, then `python -m nfl_predictor.cli weekly-m83 --report-only`. Native Windows verification has not been executed.']
    report=root/'M83_PROSPECTIVE_TRACKING_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8');return result
