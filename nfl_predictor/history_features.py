"""Incremental compact historical features with consistent comparison history."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .feature_engineering import build,FEATURES
from .elo import replay,EloParameters
from dataclasses import replace
from .integrity import digest,atomic_json
from .data_loader import atomic_parquet

# Rest in days cannot be identified from unknown historical kickoff clocks.
# Apply the same common set to ALL windows rather than inventing clock values.
COMMON=[c for c in FEATURES if c!='rest']

def reconstruct(schedules,metrics,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    frames=[];audits=[]
    for season in sorted(schedules.season.unique()):
        current=schedules[schedules.season.eq(season)]
        context=schedules[schedules.season.between(season-1,season)]
        context_metrics=metrics[metrics.game_id.isin(context.game_id)]
        h=hashlib.sha256()
        for name in ['history_features.py','feature_engineering.py']:
            h.update((Path(__file__).parent/name).read_bytes())
        for frame in [context,context_metrics]:
            h.update(pd.util.hash_pandas_object(frame,index=False).values.tobytes());h.update(str(list(frame.columns)).encode())
        key=h.hexdigest();path=directory/f'{season}-{key}.parquet';sidecar=path.with_suffix('.json')
        if path.exists():
            if not sidecar.exists() or digest(path)!=json.loads(sidecar.read_text())['sha256']:raise ValueError(f'Historical feature cache corrupt: {path}; preserve evidence and use another feature-cache directory')
            f=pd.read_parquet(path);print(f'{season}: compact pregame features reused',flush=True)
        else:
            f=build(context,context_metrics,game_ids=current.game_id)
            # Neutral status is unknown if historical location is absent.
            if 'neutral_known' in f:f.loc[f.neutral_known.eq(False),'neutral']=np.nan
            # Actual rest cannot be inferred from date-only lower bounds.
            if 'kickoff_precision' in f and f.kickoff_precision.eq('date_lower_bound').any():f.loc[f.kickoff_precision.eq('date_lower_bound'),'rest']=np.nan
            atomic_parquet(f,path);atomic_json({'sha256':digest(path),'key':key,'season':int(season)},sidecar)
            print(f'{season}: reconstructed {len(f)} pregame rows',flush=True)
        frames.append(f)
        labels=f[f.target.notna()]
        audits.append({'season':int(season),'binary_games':len(labels),'full_m2_features_complete':float(labels[FEATURES].notna().all(axis=1).mean()),'common_features_complete':float(labels[COMMON].notna().all(axis=1).mean()),'clock_known_fraction':float(f.kickoff_precision.eq('scheduled_clock').mean()) if 'kickoff_precision' in f else 1.})
    frame=pd.concat(frames,ignore_index=True).sort_values(['kickoff','game_id']).reset_index(drop=True)
    if frame.game_id.duplicated().any():raise ValueError('Duplicate historical feature game IDs')
    return frame,pd.DataFrame(audits)

def attach_elo(frame,schedules,parameters):
    p=EloParameters(**parameters)
    pre,_,_=replay(schedules,p);mov,_,_=replay(schedules,replace(p,margin=True))
    frame=frame.merge(pre[['game_id','elo_difference','elo_probability']],on='game_id',validate='one_to_one')
    return frame.merge(mov[['game_id','elo_probability']].rename(columns={'elo_probability':'elo_margin_probability'}),on='game_id',validate='one_to_one')
