"""Cutoff-specific additive opponent adjustment with bounded Jacobi iteration.
For each eligible offensive observation y(i,j): y = mu + O_i + D_j.
D is EPA/success ALLOWED: negative means stronger defense. At each iteration:
O_i <- (w*prior_O_i + sum(y-mu-clip(D_j)))/(w+n_i)
D_j <- (w*prior_D_j + sum(y-mu-clip(O_i)))/(w+n_j)
Updates are damped and bounded. mu/priors use only results eligible at cutoff.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .elo import regular_games,TEAMS
from .data_loader import ALIASES,atomic_parquet
from .feature_engineering import team_games
from .integrity import digest,atomic_json

ALGORITHM='opponent-additive-m6-v1'
ADJUSTED=['adj_off_epa_diff','adj_def_epa_advantage','adj_off_success_diff','adj_def_success_advantage']
MATCHUP=['home_matchup_epa','away_matchup_epa','home_matchup_success','away_matchup_success']
OVERALL=['overall_epa_advantage','overall_success_advantage']

@dataclass(frozen=True)
class AdjustmentParameters:
    prior_games:float=4.
    offseason_retention:float=.5
    iterations:int=8
    damping:float=.5
    epa_cap:float=.5
    success_cap:float=.2

    def __post_init__(self):
        if self.prior_games<=0 or not 0<=self.offseason_retention<=1 or not isinstance(self.iterations,int) or not 1<=self.iterations<=100 or not 0<self.damping<=1 or self.epa_cap<=0 or self.success_cap<=0:
            raise ValueError('Invalid bounded opponent-adjustment parameters')
        if not all(np.isfinite(x) for x in [self.prior_games,self.offseason_retention,self.damping,self.epa_cap,self.success_cap]):raise ValueError('Adjustment parameters must be finite')

def observations(schedules,metrics):
    s=regular_games(schedules)
    m=metrics.copy();m['team']=m.team.replace(ALIASES)
    h=team_games(s,m)
    games=s.set_index('game_id')
    home=h.game_id.map(games.home_team);away=h.game_id.map(games.away_team)
    h['opponent']=np.where(h.team.eq(home),away,home)
    return h

def _means(codes,values):
    valid=np.isfinite(values);count=np.bincount(codes[valid],minlength=len(TEAMS)).astype(float)
    sums=np.bincount(codes[valid],weights=values[valid],minlength=len(TEAMS))
    return np.divide(sums,count,out=np.full(len(TEAMS),np.nan),where=count>0),count

def shrink_residual(values,opponent_effect,prior=0.,prior_games=4.):
    """Controlled-example equation; unknown values are excluded, never zero-filled."""
    values=np.asarray(values,dtype=float);opponent_effect=np.asarray(opponent_effect,dtype=float)
    mask=np.isfinite(values)&np.isfinite(opponent_effect)
    return float((prior_games*prior+np.sum(values[mask]-opponent_effect[mask]))/(prior_games+mask.sum()))

def ratings_at(history,season,cutoff,parameters=None):
    p=parameters or AdjustmentParameters();cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None:raise ValueError('Adjustment cutoff must be timezone aware')
    h=history[history.available_at.lt(cutoff)&history.kickoff.lt(cutoff)&history.season.between(season-1,season)]
    code={t:i for i,t in enumerate(TEAMS)}
    off=h.team.replace(ALIASES).map(code);defense=h.opponent.replace(ALIASES).map(code)
    if off.isna().any() or defense.isna().any():raise ValueError('Unknown franchise in adjustment history')
    off=off.to_numpy(dtype=int);defense=defense.to_numpy(dtype=int)
    previous=h.season.eq(season-1).to_numpy();current=h.season.eq(season).to_numpy()
    result=pd.DataFrame({'team':TEAMS,'cutoff':cutoff,'season':season})
    for metric,neutral,cap in [('epa',0.,p.epa_cap),('success',.5,p.success_cap)]:
        values=h['off_'+metric].to_numpy(dtype=float)
        pv=values[previous];po=off[previous];pd_=defense[previous]
        league=float(np.nanmean(pv)) if np.isfinite(pv).any() else neutral
        prior_off,_=_means(po,pv);prior_def,_=_means(pd_,pv)
        prior_off=np.nan_to_num(prior_off,nan=league);prior_def=np.nan_to_num(prior_def,nan=league)
        prior_o=np.clip(p.offseason_retention*(prior_off-league),-cap,cap)
        prior_d=np.clip(p.offseason_retention*(prior_def-league),-cap,cap)
        y=values[current];o=off[current];d=defense[current];valid=np.isfinite(y);y=y[valid];o=o[valid];d=d[valid]
        # Four league pseudo-observations stabilize the early-season reference.
        mu=float((p.prior_games*league+y.sum())/(p.prior_games+len(y)))
        no=np.bincount(o,minlength=len(TEAMS));nd=np.bincount(d,minlength=len(TEAMS))
        O=prior_o.copy();D=prior_d.copy()
        for _ in range(p.iterations):
            next_o=(p.prior_games*prior_o+np.bincount(o,weights=y-mu-np.clip(D[d],-cap,cap),minlength=len(TEAMS)))/(p.prior_games+no)
            next_d=(p.prior_games*prior_d+np.bincount(d,weights=y-mu-np.clip(O[o],-cap,cap),minlength=len(TEAMS)))/(p.prior_games+nd)
            O=np.clip((1-p.damping)*O+p.damping*next_o,-cap,cap)
            D=np.clip((1-p.damping)*D+p.damping*next_d,-cap,cap)
        result['off_'+metric+'_strength']=O;result['def_'+metric+'_allowed_strength']=D
        result['adj_off_'+metric]=np.clip(mu+O,0,1) if metric=='success' else mu+O
        result['adj_def_'+metric+'_allowed']=np.clip(mu+D,0,1) if metric=='success' else mu+D
        raw_o=(p.prior_games*(league+prior_o)+np.bincount(o,weights=y,minlength=len(TEAMS)))/(p.prior_games+no)
        raw_d=(p.prior_games*(league+prior_d)+np.bincount(d,weights=y,minlength=len(TEAMS)))/(p.prior_games+nd)
        result['raw_estimate_off_'+metric]=raw_o;result['raw_estimate_def_'+metric+'_allowed']=raw_d
        result['off_schedule_'+metric]=np.divide(np.bincount(o,weights=D[d],minlength=len(TEAMS)),no,out=np.zeros(len(TEAMS)),where=no>0)
        result['def_schedule_'+metric]=np.divide(np.bincount(d,weights=O[o],minlength=len(TEAMS)),nd,out=np.zeros(len(TEAMS)),where=nd>0)
        result['league_'+metric]=mu;result[metric+'_games']=no
    result['algorithm']=ALGORITHM
    return result

def matchup(home,away):
    r={}
    for metric in ['epa','success']:
        r['adj_off_'+metric+'_diff']=float(home['off_'+metric+'_strength']-away['off_'+metric+'_strength'])
        r['adj_def_'+metric+'_advantage']=float(away['def_'+metric+'_allowed_strength']-home['def_'+metric+'_allowed_strength'])
        r['home_matchup_'+metric]=float(home['league_'+metric]+home['off_'+metric+'_strength']+away['def_'+metric+'_allowed_strength'])
        r['away_matchup_'+metric]=float(away['league_'+metric]+away['off_'+metric+'_strength']+home['def_'+metric+'_allowed_strength'])
        if metric=='success':
            r['home_matchup_success']=float(np.clip(r['home_matchup_success'],0,1));r['away_matchup_success']=float(np.clip(r['away_matchup_success'],0,1))
        r['overall_'+metric+'_advantage']=r['adj_off_'+metric+'_diff']+r['adj_def_'+metric+'_advantage']
    return r

def build_adjusted(schedules,metrics,parameters=None,directory=None,cutoff=None,game_ids=None):
    p=parameters or AdjustmentParameters();s=regular_games(schedules)
    if cutoff is not None:
        cutoff=pd.Timestamp(cutoff)
        if cutoff.tzinfo is None:raise ValueError('Adjustment cutoff must be timezone aware')
    targets=s if game_ids is None else s[s.game_id.isin(game_ids)]
    history=observations(s,metrics);frames=[]
    for season,t in targets.groupby('season',sort=True):
        context=history[history.season.between(season-1,season)]
        h=hashlib.sha256(Path(__file__).read_bytes()+json.dumps(asdict(p),sort_keys=True).encode())
        for f in [context,t]:h.update(pd.util.hash_pandas_object(f,index=False).values.tobytes())
        if cutoff is not None:h.update(cutoff.isoformat().encode())
        key=h.hexdigest();path=Path(directory)/f'{season}-{key}.parquet' if directory is not None else None
        if path is not None and path.exists():
            if digest(path)!=json.loads(path.with_suffix('.json').read_text())['sha256']:raise ValueError('Opponent-adjusted cache checksum mismatch')
            frames.append(pd.read_parquet(path));continue
        rows=[];snapshots={}
        for g in t.to_dict('records'):
            at=min(g['kickoff'],cutoff) if cutoff is not None else g['kickoff']
            if at not in snapshots:snapshots[at]=ratings_at(context,int(season),at,p).set_index('team')
            state=snapshots[at]
            rows.append({'game_id':g['game_id'],'adjustment_cutoff':at,**matchup(state.loc[g['home_team']],state.loc[g['away_team']]),'home_adjustment_games':state.loc[g['home_team'],'epa_games'],'away_adjustment_games':state.loc[g['away_team'],'epa_games']})
        frame=pd.DataFrame(rows);frames.append(frame)
        if path is not None:
            atomic_parquet(frame,path);atomic_json({'algorithm':ALGORITHM,'parameters':asdict(p),'input_code_key':key,'sha256':digest(path),'cutoff':cutoff.isoformat() if cutoff is not None else 'per-game kickoff lower bound'},path.with_suffix('.json'))
        print(f'{season}: opponent-adjusted snapshots built ({len(frame)} games)',flush=True)
    return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=['game_id']+ADJUSTED+MATCHUP+OVERALL)
