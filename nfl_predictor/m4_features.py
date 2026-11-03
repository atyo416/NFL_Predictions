"""Pregame team-perspective interactions, preserving M2/M3 default outputs."""
from pathlib import Path
from dataclasses import replace
import hashlib
import json
import numpy as np
import pandas as pd
from .feature_engineering import build,FEATURES
from .elo import replay,EloParameters
from .schedule_features import schedule_features,REST_FEATURES
from .integrity import digest,atomic_json
from .data_loader import atomic_parquet

INTERACTIONS=['home_attack_defense','away_attack_defense','home_success_defense','away_success_defense','recent_long_term_gap','elo_scoring_product']
FEATURE_SETS={
 'm2':FEATURES,
 'elo':FEATURES+['elo_difference'],
 'margin':FEATURES+['elo_margin_difference'],
 'elo_relative':FEATURES+['elo_probability'],
 'rest':[f for f in FEATURES if f!='rest']+['elo_difference']+REST_FEATURES,
 'interactions':FEATURES+['elo_difference']+INTERACTIONS}
FEATURE_GROUPS={
 'offense':['off_epa','off_success','off_yards'],
 'defense':['def_epa','def_success','def_yards'],
 'scoring_turnovers':['scoring','turnover'],
 'win_percentage':['win'],
 'recent':['recent_off_epa','recent_def_epa'],
 'rest_venue':['rest','neutral']+REST_FEATURES,
 'elo':['elo_difference','elo_margin_difference','elo_probability'],
 'interactions':INTERACTIONS}

def add_interactions(frame):
    f=frame.copy()
    f['home_attack_defense']=f.home_rating_off_epa*f.away_rating_def_epa
    f['away_attack_defense']=f.away_rating_off_epa*f.home_rating_def_epa
    f['home_success_defense']=f.home_rating_off_success*f.away_rating_def_success
    f['away_success_defense']=f.away_rating_off_success*f.home_rating_def_success
    f['recent_long_term_gap']=f.recent_off_epa-f.off_epa
    f['elo_scoring_product']=(f.elo_difference/400)*f.scoring
    return f

def prepare(schedules,metrics,config,directory=None,cutoff=None,game_ids=None):
    key=None;path=None
    if directory is not None and cutoff is None and game_ids is None:
        h=hashlib.sha256(json.dumps({'elo':config['elo'],'short':config['short_rest_days'],'extended':config['extended_rest_days']},sort_keys=True).encode())
        for frame in [schedules,metrics]:h.update(pd.util.hash_pandas_object(frame,index=False).values.tobytes());h.update(str(list(frame.columns)).encode())
        for name in ['m4_features.py','feature_engineering.py','elo.py','schedule_features.py']:h.update((Path(__file__).parent/name).read_bytes())
        key=h.hexdigest();path=Path(directory)/f'm4-features-{key}.parquet'
        if path.exists():
            meta=path.with_suffix('.json')
            if not meta.exists() or json.loads(meta.read_text())['sha256']!=digest(path):raise ValueError('M4 feature cache checksum mismatch; preserve damaged cache and choose a new cache directory')
            return pd.read_parquet(path)
    frame=build(schedules,metrics,cutoff,game_ids=game_ids,include_team_ratings=True)
    p=EloParameters(**config['elo'])
    if cutoff is None:
        pre,_,_=replay(schedules,p);margin,_,_=replay(schedules,replace(p,margin=True))
        frame=frame.merge(pre[['game_id','home_elo','away_elo','elo_difference','elo_probability']],on='game_id',validate='one_to_one')
        frame=frame.merge(margin[['game_id','elo_difference','elo_probability']].rename(columns={'elo_difference':'elo_margin_difference','elo_probability':'elo_margin_probability'}),on='game_id',validate='one_to_one')
    else:
        # Live rows use ratings known at issuance, never outcomes becoming eligible
        # between issuance and the future scheduled kickoff.
        from .elo import probability
        _,_,state=replay(schedules,p,cutoff);_,_,margin_state=replay(schedules,replace(p,margin=True),cutoff)
        standard=state.set_index('team').elo;mov=margin_state.set_index('team').elo
        frame['home_elo']=frame.home_team.map(standard);frame['away_elo']=frame.away_team.map(standard)
        frame['elo_difference']=frame.home_elo-frame.away_elo
        frame['elo_probability']=[probability(h,a,bool(n),p) for h,a,n in zip(frame.home_elo,frame.away_elo,frame.neutral)]
        frame['elo_margin_difference']=frame.home_team.map(mov)-frame.away_team.map(mov)
        frame['elo_margin_probability']=[probability(mov[h],mov[a],bool(n),p) for h,a,n in zip(frame.home_team,frame.away_team,frame.neutral)]
    rest=schedule_features(schedules,cutoff,config['short_rest_days'],config['extended_rest_days'],game_ids=game_ids)
    frame=add_interactions(frame.merge(rest,on='game_id',validate='one_to_one'))
    frame.attrs['m4_feature_config']={k:config[k] for k in ['elo','short_rest_days','extended_rest_days']}
    if path is not None:
        atomic_parquet(frame,path);atomic_json({'sha256':digest(path),'key':key},path.with_suffix('.json'))
    return frame
