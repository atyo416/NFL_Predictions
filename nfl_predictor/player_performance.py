"""Retrospective QB performance, available only after each prior game's eligibility.
No performance row proves a target game's pregame starter.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .data_loader import ALIASES,atomic_parquet
from .elo import regular_games,eligible_at
from .integrity import digest,atomic_json,read_season

VERSION='qb-dropback-m6-v1'
REQUIRED=['game_id','posteam','play_type','epa','qb_dropback','qb_kneel','qb_spike','passer_player_id','passer_player_name']
OPTIONAL=['rusher_player_id','rusher_player_name','qb_scramble','complete_pass','pass_attempt','interception','sack','cpoe']

def aggregate_qbs(pbp,schedules):
    missing=set(REQUIRED)-set(pbp)
    if missing:raise ValueError(f'QB performance source missing columns {sorted(missing)}')
    p=pbp[pbp.qb_dropback.eq(1)&pbp.qb_kneel.eq(0)&pbp.qb_spike.eq(0)&pbp.play_type.isin(['run','pass'])&pbp.epa.notna()].copy()
    p['player_id']=p.passer_player_id;p['player_name']=p.passer_player_name
    if {'qb_scramble','rusher_player_id'}<=set(p):
        scramble=p.player_id.isna()&p.qb_scramble.eq(1)
        p.loc[scramble,'player_id']=p.loc[scramble,'rusher_player_id']
        if 'rusher_player_name' in p:p.loc[scramble,'player_name']=p.loc[scramble,'rusher_player_name']
    p=p[p.player_id.notna()&p.posteam.notna()].copy();p['team']=p.posteam.replace(ALIASES)
    p['success_count']=p.epa.gt(0).astype(int)
    for c in ['complete_pass','pass_attempt','interception','sack','cpoe']:
        if c not in p:p[c]=np.nan
    group=p.groupby(['game_id','player_id','team'],sort=True)
    f=group.agg(name=('player_name','last'),dropbacks=('epa','size'),epa_sum=('epa','sum'),successes=('success_count','sum'),cpoe=('cpoe','mean'),cpoe_count=('cpoe','count')).reset_index()
    for source,target in [('complete_pass','completions'),('pass_attempt','attempts'),('interception','interceptions'),('sack','sacks')]:
        values=group[source].sum(min_count=1).rename(target).reset_index();f=f.merge(values,on=['game_id','player_id','team'],validate='one_to_one')
    s=regular_games(schedules)
    s=s[s.completed].copy();s['available_at']=[eligible_at(g) for g in s.to_dict('records')]
    s=s[s.available_at.notna()]
    f=f.merge(s[['game_id','season','week','kickoff','available_at']],on='game_id',how='inner',validate='many_to_one')
    f['epa_per_dropback']=f.epa_sum/f.dropbacks;f['success_rate']=f.successes/f.dropbacks
    f['classification']='retrospective_performance';f['algorithm']=VERSION
    return f

def build_performance(data,directory,schedules,seasons=None):
    data=Path(data);directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    frames=[];audit=[];active=[]
    for year in sorted(seasons if seasons is not None else schedules.season.unique()):
        meta=json.loads((data/'manifests'/f'{year}.json').read_text())
        key=hashlib.sha256(Path(__file__).read_bytes()+meta['files']['pbp']['sha256'].encode()+pd.util.hash_pandas_object(schedules[schedules.season.eq(year)],index=False).values.tobytes()).hexdigest()
        path=directory/f'{year}-{key}.parquet'
        if path.exists():
            cached=json.loads(path.with_suffix('.json').read_text())
            if digest(path)!=cached['sha256']:raise ValueError('QB performance cache checksum mismatch')
            frames.append(pd.read_parquet(path));audit.append(cached['audit']);active.append({'file':path.name,'sha256':cached['sha256']});continue
        # Validate source integrity before selecting only relevant columns.
        read_season(data,int(year),include_pbp=False)
        source=data/'generations'/meta['generation']/meta['files']['pbp']['file']
        import pyarrow.parquet as pq
        fields=pq.read_schema(source).names
        missing=sorted(set(REQUIRED)-set(fields))
        if missing:
            audit.append({'season':int(year),'status':'unavailable','missing_columns':missing,'rows':0});continue
        raw=pd.read_parquet(source,columns=[c for c in REQUIRED+OPTIONAL if c in fields])
        f=aggregate_qbs(raw,schedules[schedules.season.eq(year)]);frames.append(f)
        entry={'season':int(year),'status':'retrospective_performance_only','rows':len(f),'players':int(f.player_id.nunique()),'games':int(f.game_id.nunique()),'source_sha256':meta['files']['pbp']['sha256'],'retrieved_at':meta['retrieved_at'],'missing_optional_columns':sorted(set(OPTIONAL)-set(fields)),'cpoe_available_rows':int(f.cpoe.notna().sum())}
        audit.append(entry);atomic_parquet(f,path);atomic_json({'sha256':digest(path),'algorithm':VERSION,'audit':entry},path.with_suffix('.json'));active.append({'file':path.name,'sha256':digest(path)})
        print(f'{year}: QB performance cached ({len(f)} player-games)',flush=True)
        del raw
    atomic_json(audit,directory/'audit.json');atomic_json({'algorithm':VERSION,'files':active},directory/'active.json')
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=['game_id','player_id','team','available_at','kickoff','season','dropbacks','epa_sum','successes'])

def qb_rating(performance,player_id,cutoff,season,prior_dropbacks=80.):
    cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None or prior_dropbacks<=0:raise ValueError('QB rating requires aware cutoff and positive prior sample size')
    h=performance[performance.available_at.lt(cutoff)&performance.kickoff.lt(cutoff)]
    league=h[h.season.between(season-1,season)]
    if len(league) and league.dropbacks.sum()>0:
        league_epa=float(league.epa_sum.sum()/league.dropbacks.sum());league_success=float(league.successes.sum()/league.dropbacks.sum());basis='eligible_current_previous_season'
    else:league_epa=0.;league_success=.5;basis='neutral_algorithm_prior'
    career=h[h.player_id.eq(player_id)].sort_values(['kickoff','game_id'])
    recent=career[career.season.between(season-1,season)];n=float(recent.dropbacks.sum())
    result={'player_id':player_id,'cutoff':cutoff.isoformat(),'epa_per_dropback':None,'success_rate':None,'recent_epa':None,'dropbacks':n,'career_dropbacks':float(career.dropbacks.sum()),'games':len(recent),'prior_dropbacks':prior_dropbacks,'league_epa_prior':league_epa,'prior_basis':basis,'sample_uncertainty':None,'performance_status':'unknown_no_recent_performance','last_eligible_game':None,'last_team':None}
    if n>0:
        result.update({'epa_per_dropback':float((prior_dropbacks*league_epa+recent.epa_sum.sum())/(prior_dropbacks+n)),'success_rate':float((prior_dropbacks*league_success+recent.successes.sum())/(prior_dropbacks+n)),'recent_epa':float(recent.tail(3).epa_sum.sum()/recent.tail(3).dropbacks.sum()),'sample_uncertainty':float(1/np.sqrt(prior_dropbacks+n)),'performance_status':'regularized_prior_performance','last_eligible_game':str(recent.iloc[-1].game_id),'last_team':str(recent.iloc[-1].team)})
    return result
