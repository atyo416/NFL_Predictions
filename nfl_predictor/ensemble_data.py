"""Annual OOS base predictions; preserve original M2 and M5 feature contracts."""
from pathlib import Path
from time import perf_counter
from datetime import datetime,timezone
import hashlib
import json
import numpy as np
import pandas as pd
from .ensemble import BASES,PROBABILITIES,CLASSIFICATION,timestamp,validate_matrix
from .feature_engineering import FEATURES,build,cached_build
from .history_features import COMMON,reconstruct,attach_elo
from .history_models import fit_history
from .model import train
from .elo import replay,EloParameters,eligible_at,regular_games
from .integrity import digest,atomic_json
from .registry import register,load_candidate


def identity(*objects):
    h=hashlib.sha256()
    for obj in objects:
        if isinstance(obj,pd.DataFrame):
            h.update(str(list(zip(obj.columns,obj.dtypes.astype(str)))).encode())
            h.update(pd.util.hash_pandas_object(obj,index=False).values.tobytes())
        else:h.update(json.dumps(obj,sort_keys=True,default=str).encode())
    return h.hexdigest()


def code_identity():
    return identity({p.name:digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))})


def availability(schedules):
    return pd.Series({g['game_id']:eligible_at(g) for g in schedules.to_dict('records')},dtype='datetime64[ns, UTC]')


def elo_features(schedules,config,cutoff=None,ids=None):
    """A cutoff probe snapshots unstarted games at cutoff, including offseason decay."""
    s=regular_games(schedules)
    if cutoff is not None:
        cutoff=timestamp(cutoff);s=s.copy()
        s.loc[s.game_id.isin(ids),'kickoff']=cutoff
    standard,_,_=replay(s,EloParameters(**config['standard_elo']),cutoff)
    modern=s[s.season.ge(2018)]
    margin,updates,_=replay(modern,EloParameters(**config['margin_elo']),cutoff)
    out=standard[['game_id','elo_difference']].merge(margin[['game_id','elo_probability']].rename(columns={'elo_probability':'p_elo_margin'}),on='game_id',how='left',validate='one_to_one')
    # Elo's online updates are learning too: record the most recent eligible update.
    times=pd.DatetimeIndex(updates.available_at.unique()).sort_values() if len(updates) else pd.DatetimeIndex([],tz='UTC')
    snapshots=modern.set_index('game_id').kickoff
    stamps=[]
    initial=modern.kickoff.min()-pd.Timedelta(nanoseconds=1)
    for gid in out.game_id:
        at=snapshots.get(gid,pd.NaT)
        pos=times.searchsorted(at,side='left') if pd.notna(at) else 0
        stamps.append(times[pos-1] if pos else initial)
    out['training_cutoff_elo_margin']=stamps
    return out


def feature_frames(schedules,metrics,data,config):
    data=Path(data)
    modern=schedules[schedules.season.ge(2018)]
    logistic=cached_build(modern,metrics[metrics.game_id.isin(modern.game_id)],data/'m7/logistic_features')
    boost,_=reconstruct(schedules,metrics,data/'history_features')
    boost=attach_elo(boost,schedules,config['standard_elo'])
    elo=elo_features(schedules,config)
    for f in [logistic,boost]:f['available_at']=f.game_id.map(availability(schedules))
    return logistic,boost,elo


def fit_annual(logistic,boost,schedules,year,config,registry):
    target=schedules[schedules.season.eq(year)]
    if target.empty:raise ValueError(f'No schedule for base-prediction season {year}')
    before=timestamp(target.kickoff.min());models={};refs={};audit=[]
    for name,frame,start in [('logistic',logistic,2018),('boosting',boost,2008)]:
        candidates=frame[frame.season.between(start,year-1)&frame.target.notna()]
        tr=candidates[candidates.available_at.notna()&candidates.available_at.lt(before)&candidates.data_cutoff.lt(before)]
        if tr.empty or tr.target.nunique()!=2:raise ValueError(f'{name} lacks eligible prior-season training classes for {year}')
        features=FEATURES if name=='logistic' else COMMON+['elo_difference']
        key=identity(code_identity(),name,config,tr[['game_id','kickoff','available_at','target']+features])
        version=f'm7-base-{year}-{name}-{key[:16]}'
        path=Path(registry)/'candidates'/version
        if path.exists():model,meta=load_candidate(registry,version)
        else:
            started=perf_counter();model=train(tr) if name=='logistic' else fit_history(tr,'hgb',config,None,features)
            model.update(version=version,algorithm='LogisticRegression' if name=='logistic' else 'HistGradientBoostingClassifier',
                         feature_schema='m7-'+name+'-v1',base_kind=name,training_cutoff=tr.available_at.max().isoformat(),
                         activation_blocked=True,activation_block_reason='M7 base refits remain experimental; production champion preserved.',dataset_fingerprint=key)
            model['feature_config']={'history_start':2018,'prior_weight':4.,'regression':.5} if name=='logistic' else {'history_start':1999,'standard_elo':config['standard_elo'],'prior_weight':4.,'regression':.5}
            path=register(model,registry,{'base_kind':name,'target_season':int(year),'training_games':len(tr),'excluded_delayed_training_labels':len(candidates)-len(tr),'runtime_seconds':perf_counter()-started,'feature_contract':'M2 original full/2018 history' if name=='logistic' else 'M5 2008/uniform/common+standard Elo/1999 warmup','code_fingerprint':code_identity()})
            meta=json.loads((path/'metadata.json').read_text())
        if timestamp(model['training_cutoff'])>=before:raise ValueError('Annual base fit overlaps target season')
        models[name]=model;refs[name]={'version':version,'artifact_sha256':meta['artifact_sha256'],'feature_schema':model['feature_schema'],'features':model['features'],'base_kind':name,'training_cutoff':model['training_cutoff']}
        audit.append({'base':name,'target_season':int(year),'training_games':len(tr),'excluded_delayed_training_labels':len(candidates)-len(tr),'training_cutoff':model['training_cutoff'],'version':version})
    history=schedules[schedules.season.between(2018,year-1)].copy();history['available_at']=history.game_id.map(availability(history))
    history=history[history.available_at.lt(before)]
    at=history.available_at.max() if len(history) else before-pd.Timedelta(nanoseconds=1)
    key=identity(code_identity(),config['margin_elo'],history);version=f'm7-base-{year}-elo-{key[:16]}'
    model={'version':version,'algorithm':'M3 margin-adjusted Elo','base_kind':'elo_margin','feature_schema':'m7-elo_margin-v1','features':['p_elo_margin'],'training_cutoff':at.isoformat(),'parameters':config['margin_elo'],'warmup_start':2018,'activation_blocked':True,'activation_block_reason':'M7 Elo adapter remains experimental.','dataset_fingerprint':key}
    register(model,registry,{'base_kind':'elo_margin','target_season':int(year),'online_updates':'Prior eligible results replayed before each cutoff; annual checksum verifies parameters/adapter contract, not a frozen in-season rating.'})
    _,meta=load_candidate(registry,version);models['elo_margin']=model
    refs['elo_margin']={'version':version,'artifact_sha256':meta['artifact_sha256'],'feature_schema':model['feature_schema'],'features':model['features'],'base_kind':'elo_margin','training_cutoff':model['training_cutoff']}
    return models,refs,audit


def build_matrix(schedules,metrics,data,root,config):
    data=Path(data);root=Path(root);registry=root/'models/registry';directory=data/'m7/base_predictions';directory.mkdir(parents=True,exist_ok=True)
    started=perf_counter();validated=regular_games(schedules)
    # Preserve the normalized source row order for the existing M5 cache keys.
    # Reconstruct sorts its output itself; input sorting needlessly invalidates caches.
    logistic,boost,elo=feature_frames(schedules,metrics,data,config)
    schedules=validated
    frames=[];audits=[];annual={}
    for year in config['base_seasons']:
        models,refs,audit=fit_annual(logistic,boost,schedules,year,config,registry);annual[str(year)]=refs;audits.extend(audit)
        if year>2025:continue  # Future games are scored only by the explicit live adapter.
        l=logistic[logistic.season.eq(year)];b=boost[boost.season.eq(year)]
        s=schedules[schedules.season.eq(year)].copy()
        if set(l.game_id)!=set(s.game_id) or set(b.game_id)!=set(s.game_id):raise ValueError('Base feature/game alignment mismatch')
        key=identity(code_identity(),config,s,l[['game_id','target']+FEATURES],b[['game_id','target']+COMMON+['elo_difference']],refs)
        file=directory/f'{year}-{key}.parquet';sidecar=file.with_suffix('.json')
        if file.exists():
            if digest(file)!=json.loads(sidecar.read_text())['sha256']:raise ValueError('Historical base-prediction cache checksum mismatch')
            f=pd.read_parquet(file)
        else:
            f=s[['game_id','season','week','kickoff','home_team','away_team','target','completed','home_score','away_score']].copy()
            f['data_cutoff']=f.kickoff;f['available_at']=f.game_id.map(availability(s))
            for name,frame in [('logistic',l),('boosting',b)]:
                probabilities=pd.Series(models[name]['pipeline'].predict_proba(frame[models[name]['features']])[:,1],index=frame.game_id)
                f['p_'+name]=f.game_id.map(probabilities);f['training_cutoff_'+name]=timestamp(models[name]['training_cutoff'])
            f=f.merge(elo,on='game_id',how='left',validate='one_to_one')
            f['classification']=CLASSIFICATION;f['generated_at']=datetime.now(timezone.utc).isoformat()
            for name in BASES:f['version_'+name]=refs[name]['version'];f['missing_'+name]=f['p_'+name].isna()
            f['source_fingerprint']=[identity(row) for row in f[['game_id','kickoff','data_cutoff']+PROBABILITIES+['version_'+n for n in BASES]].to_dict('records')]
            f.to_parquet(file,index=False);atomic_json({'sha256':digest(file),'configuration':config,'base_refs':refs,'classification':CLASSIFICATION},sidecar)
        frames.append(f)
        print(f'{year}: chronological OOS base matrix ({len(f)} games)',flush=True)
    frame=pd.concat(frames,ignore_index=True)
    # Matrix includes ties/unfinished/missing rows for auditing; never impute them.
    fingerprint=identity(code_identity(),config,frame.drop(columns=['generated_at']),annual)
    final=directory/fingerprint[:16]
    if not final.exists():
        final.mkdir();frame.to_parquet(final/'matrix.parquet',index=False)
        atomic_json({'key':fingerprint,'annual_base_refs':annual,'season_starts':{str(y):schedules.loc[schedules.season.eq(y),'kickoff'].min().isoformat() for y in config['base_seasons']},'training':audits,'seconds':perf_counter()-started,'rows':len(frame),'matrix_sha256':digest(final/'matrix.parquet'),'configuration':config,'code_fingerprint':code_identity()},final/'metadata.json')
    else:
        if digest(final/'matrix.parquet')!=json.loads((final/'metadata.json').read_text())['matrix_sha256']:raise ValueError('Base matrix integrity failure')
    atomic_json({'run':final.name},directory/'latest.json')
    return frame,final


def aligned(frame,observed_before):
    if frame.game_id.duplicated().any():raise ValueError('Duplicate base prediction game IDs')
    observed_before=timestamp(observed_before);f=frame.copy()
    missing=f[PROBABILITIES].isna().any(axis=1)
    labels=f.target.notna();known=f.available_at.notna()&f.available_at.lt(observed_before)
    keep=~missing&labels&known
    audit={'scheduled_games':len(f),'included_games':int(keep.sum()),'missing_base_predictions':int(missing.sum()),'ties':int((f.completed&f.home_score.eq(f.away_score)).sum()),'incomplete_labels':int((~f.completed).sum()),'unavailable_or_delayed_labels':int((labels&~known).sum()),'exclusions_are_overlapping':True}
    result=f[keep].copy();validate_matrix(result,True)
    return result,audit
