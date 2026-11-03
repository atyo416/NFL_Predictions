"""Evidence-tagged QB context. Actual game starters never prove pregame designation."""
from pathlib import Path
from datetime import datetime,timezone
import json
import uuid
import numpy as np
import pandas as pd
from .data_loader import ALIASES
from .elo import regular_games,eligible_at,TEAMS
from .integrity import atomic_json,digest

COLUMNS=['team','player_id','name','source','source_at','observed_at','classification','availability_status','designation','game_id','season','week','quality']

def empty():
    return pd.DataFrame(columns=COLUMNS)

def normalize_depth(frame,retrieved_at,season):
    """Legacy weekly rows and modern snapshots are observations, not verified forecasts."""
    if pd.Timestamp(retrieved_at).tzinfo is None: raise ValueError('QB retrieval time must be timezone aware')
    f=frame.copy()
    modern={'dt','team','gsis_id','player_name','pos_abb','pos_rank'}<=set(f)
    legacy={'club_code','gsis_id','full_name','position','depth_team','week'}<=set(f)
    if modern:
        f=f[f.pos_abb.eq('QB') & pd.to_numeric(f.pos_rank,errors='coerce').eq(1)].copy()
        out=pd.DataFrame({'team':f.team,'player_id':f.gsis_id,'name':f.player_name,'source_at':pd.to_datetime(f.dt,utc=True,errors='raise'),'week':np.nan})
    elif legacy:
        f=f[f.position.eq('QB') & pd.to_numeric(f.depth_team,errors='coerce').eq(1)].copy()
        out=pd.DataFrame({'team':f.club_code,'player_id':f.gsis_id,'name':f.full_name,'source_at':pd.NaT,'week':f.week})
    else: raise ValueError('Unrecognized depth-chart schema: expected legacy weekly or modern timestamped columns')
    out['team']=out.team.replace(ALIASES)
    out['source']='nflverse_depth_chart';out['observed_at']=pd.Timestamp(retrieved_at)
    out['classification']='unknown' if modern else 'retrospective'
    out['quality']='timestamped_depth_candidate_not_verified' if modern else 'weekly_vintage_unverified'
    out['designation']='candidate';out['availability_status']='unknown';out['game_id']=None;out['season']=season
    out['source_at']=pd.to_datetime(out.source_at,utc=True)
    out['observed_at']=pd.to_datetime(out.observed_at,utc=True)
    return out[COLUMNS].drop_duplicates().reset_index(drop=True)

def validate_verified(records):
    missing=set(COLUMNS)-set(records)
    if missing: raise ValueError(f'QB evidence missing fields: {sorted(missing)}')
    f=records.copy()
    for field in ['source_at','observed_at']:
        for value in f[field]:
            if pd.isna(value) or pd.Timestamp(value).tzinfo is None: raise ValueError('Verified QB evidence needs timezone-aware source and observation timestamps')
        f[field]=pd.to_datetime(f[field],utc=True)
    f['team']=f.team.replace(ALIASES)
    if not f.classification.eq('verified_pregame').all() or f[['player_id','team','game_id','source','quality']].isna().any().any() or f[['player_id','game_id','source','quality']].astype(str).apply(lambda c:c.str.strip().eq('')).any().any():
        raise ValueError('Verified QB records require identifiers, game, named evidence and quality')
    if not f.team.isin(TEAMS).all() or not f.designation.isin(['candidate','confirmed_starter']).all():
        raise ValueError('Verified QB evidence needs a recognized team and pregame designation')
    if (f.observed_at>pd.Timestamp.now(tz='UTC')).any(): raise ValueError('QB evidence observation time cannot be in the future')
    if (f.source_at>f.observed_at).any(): raise ValueError('QB source time cannot follow its observation')
    return f[COLUMNS]

def context(schedules,records,team,game_id,cutoff):
    cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None: raise ValueError('QB cutoff must be timezone aware')
    team=ALIASES.get(team,team)
    f=regular_games(schedules)
    past=f[(f.home_team.eq(team)|f.away_team.eq(team)) & f.kickoff.lt(cutoff)]
    observed=[]
    for g in past.to_dict('records'):
        at=eligible_at(g)
        if pd.isna(at) or at>=cutoff: continue
        side='home' if g['home_team']==team else 'away'
        if pd.notna(g.get(side+'_qb_id')):
            observed.append((g['kickoff'],g[side+'_qb_id'],g.get(side+'_qb_name'),at))
    last=sorted(observed)[-1] if observed else None
    result={'team':team,'most_recent_observed_id':last[1] if last else None,'most_recent_observed_name':last[2] if last else None,'observed_starter_classification':'retrospective','candidate_id':None,'candidate_name':None,'availability_status':'unknown','classification':'unknown','starter_change':np.nan,'source':None,'source_at':None,'quality':'unavailable'}
    if records.empty: return result
    r=records[records.team.eq(team)].copy()
    r['source_at']=pd.to_datetime(r.source_at,utc=True); r['observed_at']=pd.to_datetime(r.observed_at,utc=True)
    # Retrieval after the cutoff cannot manufacture historical pregame knowledge.
    valid=r[r.classification.eq('verified_pregame') & r.game_id.eq(game_id) & r.source_at.lt(cutoff) & r.observed_at.lt(cutoff)]
    if len(valid):
        v=valid.sort_values(['source_at','observed_at','player_id']).iloc[-1]
        # Conflicting equally recent designations remain unknown.
        same=valid[valid.source_at.eq(v.source_at)&valid.observed_at.eq(v.observed_at)]
        if same.player_id.nunique()>1: return result
        result.update({'candidate_id':v.player_id,'candidate_name':v['name'],'availability_status':v.availability_status if pd.notna(v.availability_status) else 'unknown','classification':'verified_pregame','starter_change':float(v.player_id!=last[1]) if last else np.nan,'source':v.source,'source_at':v.source_at.isoformat(),'quality':v.quality})
    return result

def features(schedules,records):
    if records.empty or not records.classification.eq('verified_pregame').any():
        return pd.DataFrame({'game_id':schedules.game_id,'qb_verified':False,'qb_change_difference':np.nan})
    rows=[]
    for g in regular_games(schedules).to_dict('records'):
        home=context(schedules,records,g['home_team'],g['game_id'],g['kickoff'])
        away=context(schedules,records,g['away_team'],g['game_id'],g['kickoff'])
        rows.append({'game_id':g['game_id'],'qb_verified':home['classification']=='verified_pregame' and away['classification']=='verified_pregame','qb_change_difference':away['starter_change']-home['starter_change']})
    return pd.DataFrame(rows)

def save_context(records,directory,provenance):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    key=uuid.uuid4().hex
    path=directory/f'{key}.parquet';records.to_parquet(path,index=False)
    meta={'file':path.name,'sha256':digest(path),'retrieved_at':datetime.now(timezone.utc).isoformat(),'sources':provenance,'rows':len(records),'schema_version':1}
    atomic_json(meta,directory/f'{key}.json');atomic_json(meta,directory/'latest.json')
    return path

def cached_context(directory):
    directory=Path(directory); pointer=directory/'latest.json'
    if not pointer.exists(): return empty()
    meta=json.loads(pointer.read_text());path=directory/meta['file']
    if path.resolve().parent!=directory.resolve() or digest(path)!=meta['sha256']: raise ValueError('QB cache checksum/path mismatch; refresh QB sources')
    records=pd.read_parquet(path)
    if meta.get('schema_version')!=1 or set(COLUMNS)-set(records) or len(records)!=meta['rows']:
        raise ValueError('QB cache schema/row-count mismatch')
    return records

def update_sources(data,seasons=(2024,2026)):
    import nflreadpy as nfl
    data=Path(data); records=[];provenance=[]
    for season in seasons:
        for name in ['load_depth_charts','load_injuries','load_rosters_weekly']:
            frame=getattr(nfl,name)([season]).to_pandas()
            stamp=datetime.now(timezone.utc).isoformat()
            path=data/'qb_sources'/f'{name}_{season}_{uuid.uuid4().hex}.parquet';path.parent.mkdir(parents=True,exist_ok=True)
            frame.to_parquet(path,index=False)
            source={'source':name,'season':int(season),'retrieved_at':stamp,'file':path.name,'sha256':digest(path),'columns':list(frame.columns)}
            atomic_json(source,path.with_suffix('.json'));provenance.append(source)
            if name=='load_depth_charts':records.append(normalize_depth(frame,stamp,season))
    if records:
        # Preserve independently verified local evidence across refreshes.
        existing=cached_context(data/'qb_context')
        if len(existing): records.append(existing[existing.classification.eq('verified_pregame')])
        return save_context(pd.concat(records,ignore_index=True),data/'qb_context',provenance)

def import_verified(path,data):
    path=Path(path)
    records=validate_verified(pd.DataFrame(json.loads(path.read_text())))
    existing=cached_context(Path(data)/'qb_context')
    return save_context(pd.concat([existing,records],ignore_index=True).drop_duplicates(),Path(data)/'qb_context',[{'source':'reviewed_local_evidence','sha256':digest(path)}])
