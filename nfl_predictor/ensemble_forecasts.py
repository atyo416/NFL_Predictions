"""Separate append-only experimental forecast and grading files; no SQLite writes."""
from pathlib import Path
import hashlib
import json
import os
import uuid
import numpy as np
import pandas as pd
from .ensemble import BASES,PROBABILITIES,timestamp
from .ensemble_data import identity,availability,elo_features
from .ensemble_registry import load_ensemble
from .feature_engineering import build
from .elo import regular_games,eligible_at
from .evaluation import evaluate


def utc_now():return pd.Timestamp.now(tz='UTC')


def _encoded(value):return json.dumps(value,sort_keys=True,default=str).encode()


def _append(directory,key,payload):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);path=directory/(key+'.json')
    envelope={'payload':payload,'sha256':hashlib.sha256(_encoded(payload)).hexdigest()}
    temporary=directory/(uuid.uuid4().hex+'.tmp');temporary.write_bytes(_encoded(envelope))
    try:
        try:os.link(temporary,path)
        except FileExistsError:
            existing=_read(path)
            a={k:v for k,v in existing.items() if k not in ['created_at','graded_at']}
            b={k:v for k,v in payload.items() if k not in ['created_at','graded_at']}
            if a!=b:raise ValueError('An immutable experimental record already exists with different probabilities/provenance; preserve it and use a new cutoff/version')
    finally:temporary.unlink(missing_ok=True)
    return path


def _read(path):
    envelope=json.loads(Path(path).read_text());payload=envelope['payload']
    if hashlib.sha256(_encoded(payload)).hexdigest()!=envelope['sha256']:raise ValueError('Experimental ledger checksum mismatch')
    if payload.get('kind')=='experimental_ensemble_forecast':
        if timestamp(payload['data_cutoff'])>timestamp(payload['created_at']) or timestamp(payload['created_at'])>=timestamp(payload['kickoff']):raise ValueError('Invalid/backdated prospective issuance times')
        expected=identity(payload['game_id'],payload['ensemble_version'],payload['data_cutoff'])
        if Path(path).stem!=expected:raise ValueError('Experimental forecast identity mismatch')
    return payload


def records(directory):
    directory=Path(directory)
    return [_read(p) for p in sorted((directory/'forecasts').glob('*.json'))]


def probabilities(schedules,metrics,ensemble,base_models,config,cutoff,now=None,game_id=None):
    cutoff=timestamp(cutoff);now=timestamp(now if now is not None else utc_now())
    if cutoff>now:raise ValueError('Prediction cutoff cannot be future-dated')
    if timestamp(ensemble['training_cutoff'])>=cutoff:raise ValueError('Ensemble/base/meta/calibration/selection cutoff must precede feature cutoff')
    if base_models['elo_margin']['parameters']!=config['margin_elo'] or base_models['boosting']['feature_config']['standard_elo']!=config['standard_elo']:
        raise ValueError('Live Elo configuration is incompatible with versioned base artifacts')
    s=regular_games(schedules)
    status=s.get('status',pd.Series('',index=s.index)).fillna('').astype(str).str.lower()
    upcoming=s[s.season.eq(ensemble['target_season'])&~s.completed&s.kickoff.gt(now)&s.kickoff.gt(cutoff)&~status.isin(['postponed','suspended','canceled','cancelled','in progress','in_progress'])]
    if game_id is not None:
        upcoming=upcoming[upcoming.game_id.eq(game_id)]
        if upcoming.empty:raise ValueError('Requested game is not a legitimate unstarted scheduled game')
    if upcoming.empty:return pd.DataFrame(),{}
    modern=s[s.season.ge(2018)]
    logistic=build(modern,metrics[metrics.game_id.isin(modern.game_id)],cutoff,game_ids=upcoming.game_id)
    boosting=build(s,metrics,cutoff,game_ids=upcoming.game_id)
    if 'neutral_known' in boosting:boosting.loc[~boosting.neutral_known,'neutral']=np.nan
    elo=elo_features(s,config,cutoff,upcoming.game_id)
    boosting=boosting.merge(elo[['game_id','elo_difference']],on='game_id',validate='one_to_one')
    f=upcoming[['game_id','season','week','kickoff','home_team','away_team']].copy()
    for name,features in [('logistic',logistic),('boosting',boosting)]:
        model=base_models[name]
        if timestamp(model['training_cutoff'])>=cutoff:raise ValueError('Base artifact was trained after requested prediction cutoff')
        p=pd.Series(model['pipeline'].predict_proba(features[model['features']])[:,1],index=features.game_id)
        f['p_'+name]=f.game_id.map(p)
    f=f.merge(elo[['game_id','p_elo_margin']],on='game_id',validate='one_to_one')
    f['ensemble_probability']=ensemble['pipeline'].predict_proba(f)[:,1]
    eligible=s[s.game_id.map(availability(s)).lt(cutoff)&s.kickoff.lt(cutoff)]
    source={'eligible_schedule_fingerprint':identity(eligible),'eligible_metrics_fingerprint':identity(metrics[metrics.game_id.isin(eligible.game_id)]),'elo_config_fingerprint':identity(config['margin_elo']),
            'per_game_features':{gid:identity(logistic.loc[logistic.game_id.eq(gid),['game_id']+base_models['logistic']['features']],boosting.loc[boosting.game_id.eq(gid),['game_id']+base_models['boosting']['features']]) for gid in upcoming.game_id}}
    return f,source


def issue(schedules,metrics,registry,version,config,directory,cutoff=None,game_id=None):
    initial_now=utc_now();cutoff=timestamp(cutoff if cutoff is not None else initial_now)
    model,bases,_=load_ensemble(registry,version)
    frame,source=probabilities(schedules,metrics,model,bases,config,cutoff,initial_now,game_id)
    saved=[]
    for row in frame.to_dict('records'):
        created=utc_now()
        if created>=timestamp(row['kickoff']):raise ValueError('Game started during computation; experimental forecast was not saved')
        key=identity(row['game_id'],version,cutoff.isoformat())
        row_source={k:v for k,v in source.items() if k!='per_game_features'};row_source['feature_fingerprint']=source['per_game_features'][row['game_id']]
        payload={'kind':'experimental_ensemble_forecast','designation':'experimental','forecast_id':key,'game_id':row['game_id'],'season':int(row['season']),'week':int(row['week']),'home_team':row['home_team'],'away_team':row['away_team'],'kickoff':row['kickoff'].isoformat(),'created_at':created.isoformat(),'data_cutoff':cutoff.isoformat(),'ensemble_version':version,'ensemble_method':model['ensemble_method'],'base_versions':{n:r['version'] for n,r in model['base_refs'].items()},'base_checksums':{n:r['artifact_sha256'] for n,r in model['base_refs'].items()},'base_probabilities':{n:float(row['p_'+n]) for n in BASES},'home_probability':float(row['ensemble_probability']),'away_probability':float(1-row['ensemble_probability']),'calibration':model['calibration'],'source_fingerprints':row_source,'training_cutoff':model['training_cutoff'],'selection':model['selection']}
        path=_append(Path(directory)/'forecasts',key,payload);saved.append(_read(path))
    return pd.DataFrame(saved)


def grade(schedules,directory):
    now=utc_now();games=regular_games(schedules).set_index('game_id');events=[]
    for forecast in records(directory):
        if forecast['game_id'] not in games.index:continue
        g=games.loc[forecast['game_id']];at=eligible_at(g.to_dict())
        if pd.isna(at) or at>=now:continue
        result=.5 if g.home_score==g.away_score else float(g.home_score>g.away_score)
        payload={'kind':'experimental_ensemble_result','forecast_id':forecast['forecast_id'],'game_id':forecast['game_id'],'home_score':float(g.home_score),'away_score':float(g.away_score),'result':result,'eligible_at':at.isoformat(),'graded_at':now.isoformat()}
        key=identity({k:v for k,v in payload.items() if k!='graded_at'})
        path=_append(Path(directory)/'results',key,payload);events.append(_read(path))
    return events


def prospective_summary(directory):
    forecasts=records(directory);events=[_read(p) for p in (Path(directory)/'results').glob('*.json')]
    latest={}
    for e in sorted(events,key=lambda e:e['graded_at']):latest[e['forecast_id']]=e
    rows=[{**f,'result':latest[f['forecast_id']]['result']} for f in forecasts if f['forecast_id'] in latest]
    first={}
    for forecast in sorted(forecasts,key=lambda r:(r['created_at'],r['forecast_id'])):first.setdefault(forecast['game_id'],forecast)
    first_graded=[{**f,'result':latest[f['forecast_id']]['result']} for f in first.values() if f['forecast_id'] in latest]
    binary=[r for r in first_graded if r['result'] in [0.,1.]]
    return {'genuinely_issued_forecasts':len(forecasts),'unique_games':len(first),'graded':len(rows),'ties':sum(r['result']==.5 for r in first_graded),'binary_metrics':evaluate([r['result'] for r in binary],[r['home_probability'] for r in binary]) if binary else None,'metric_cohort':'First genuinely issued experimental forecast per game; future research should also compare fixed model-version/cutoff cohorts.','note':'Multiple forecasts per game are revisions, not independent games.'}
