"""Event-driven regular-season Elo. Kickoffs precede equal-time final updates."""
from dataclasses import dataclass, asdict
import heapq
import numpy as np
import pandas as pd
from .data_loader import ALIASES
from .analysis import TEAM_DIVISION

TEAMS=sorted(TEAM_DIVISION)
ALGORITHM='elo-m3-v1'
BLOCKED={'postponed','suspended','canceled','cancelled','in progress','in_progress','scheduled'}

@dataclass(frozen=True)
class EloParameters:
    initial: float=1500.
    scale: float=400.
    k: float=20.
    home_advantage: float=50.
    regression: float=.67
    margin: bool=False

    def __post_init__(self):
        if not all(np.isfinite(v) for v in [self.initial,self.scale,self.k,self.home_advantage,self.regression]) or self.scale<=0 or self.k<=0 or not 0<=self.regression<=1:
            raise ValueError('Invalid Elo parameters')

def probability(home,away,neutral=False,parameters=None):
    p=parameters or EloParameters()
    advantage=0 if neutral else p.home_advantage
    return float(1/(1+10**np.clip(-(home+advantage-away)/p.scale,-20,20)))

def eligible_at(game):
    if not game.get('completed',False) or str(game.get('status','')).lower() in BLOCKED:
        return pd.NaT
    if pd.isna(game.get('home_score')) or pd.isna(game.get('away_score')):
        return pd.NaT
    kickoff=pd.Timestamp(game['kickoff'])
    stamp=game.get('result_available_at')
    if pd.notna(stamp):
        stamp=pd.Timestamp(stamp)
        if stamp.tzinfo is None or stamp<kickoff:
            raise ValueError('Result availability must be timezone aware and not precede kickoff')
        return stamp
    return kickoff+pd.Timedelta(hours=8)

def regular_games(schedules):
    f=schedules.copy()
    if 'game_type' in f: f=f[f.game_type.eq('REG')]
    if f.game_id.isna().any(): raise ValueError('Missing game IDs')
    # Exact duplicates are harmless; conflicting revisions require source normalization.
    f=f.drop_duplicates()
    if f.game_id.duplicated().any(): raise ValueError('Conflicting duplicate game results')
    for col in ['home_team','away_team']:
        f[col]=f[col].replace(ALIASES)
        if not f[col].isin(TEAMS).all(): raise ValueError('Unrecognized team identity')
    if f.home_team.eq(f.away_team).any(): raise ValueError('A team cannot play itself')
    if f.kickoff.isna().any() or f.kickoff.dt.tz is None: raise ValueError('Kickoffs must be timezone aware')
    return f.sort_values(['kickoff','game_id']).reset_index(drop=True)

def replay(schedules,parameters=None,cutoff=None):
    """Return pregame snapshots, eligible postgame updates, final team state.
    Updates use expected results fixed at that game's kickoff, not later ratings.
    Equal-time results never enter equal-time kickoff snapshots. First season is warmup.
    """
    p=parameters or EloParameters()
    f=regular_games(schedules)
    cutoff=pd.Timestamp(cutoff) if cutoff is not None else None
    if cutoff is not None and cutoff.tzinfo is None: raise ValueError('Cutoff must be timezone aware')
    events=[]; games={r['game_id']:r for r in f.to_dict('records')}
    for gid,g in games.items():
        if cutoff is None or g['kickoff']<=cutoff:
            heapq.heappush(events,(g['kickoff'],0,gid,'kickoff'))
        at=eligible_at(g)
        if pd.notna(at) and (cutoff is None or at<cutoff):
            heapq.heappush(events,(at,1,gid,'result'))
    ratings={t:p.initial for t in TEAMS}
    records={t:{'wins':0,'losses':0,'ties':0,'last_opponent':None,'last_result':None} for t in TEAMS}
    snapshots={}; history=[]; season=None
    while events:
        at,_,gid,kind=heapq.heappop(events); g=games[gid]
        home,away=g['home_team'],g['away_team']
        if kind=='kickoff':
            if season is None or g['season']>season:
                if season is not None:
                    factor=p.regression**(g['season']-season)
                    ratings={t:p.initial+factor*(v-p.initial) for t,v in ratings.items()}
                season=g['season']
                records={t:{'wins':0,'losses':0,'ties':0,'last_opponent':None,'last_result':None} for t in TEAMS}
            if g['season']<season: raise ValueError('Overlapping season kickoff sequence')
            snapshots[gid]={'game_id':gid,'season':g['season'],'week':g['week'],'kickoff':at,'home_team':home,'away_team':away,'home_elo':ratings[home],'away_elo':ratings[away], 'elo_difference':ratings[home]-ratings[away],'elo_probability':probability(ratings[home],ratings[away],bool(g.get('neutral',False)),p),'algorithm':ALGORITHM,'warmup':g['season']==int(f.season.min())}
        else:
            if gid not in snapshots: raise ValueError('Result has no pregame snapshot')
            snap=snapshots[gid]
            outcome=.5 if g['home_score']==g['away_score'] else float(g['home_score']>g['away_score'])
            multiplier=1.
            if p.margin and outcome!=.5:
                winner_diff=(snap['elo_difference']+(0 if g.get('neutral',False) else p.home_advantage))*(1 if outcome==1 else -1)
                multiplier=float(np.clip(np.log1p(min(abs(g['home_score']-g['away_score']),42))*2.2/(2.2+.001*np.clip(winner_diff,-1000,1000)),.5,3.))
            # Extremely delayed prior-season results are attenuated across offseason(s).
            attenuation=p.regression**max(0,season-g['season'])
            delta=p.k*multiplier*(outcome-snap['elo_probability'])*attenuation
            for team,opponent,change,result in [(home,away,delta,outcome),(away,home,-delta,1-outcome)]:
                before=ratings[team]; ratings[team]+=change
                if g['season']==season:
                    records[team]['wins' if result==1 else 'losses' if result==0 else 'ties']+=1
                    records[team]['last_opponent']=opponent;records[team]['last_result']='W' if result==1 else 'L' if result==0 else 'T'
                history.append({'game_id':gid,'season':g['season'],'week':g['week'],'team':team,'opponent':opponent,'kickoff':g['kickoff'],'available_at':at,'pregame_elo':snap['home_elo'] if team==home else snap['away_elo'],'before_update_elo':before,'postgame_elo':ratings[team],'change':change,'result':result,'margin_multiplier':multiplier,'algorithm':ALGORITHM})
    state=pd.DataFrame([{'team':t,'elo':ratings[t],**records[t]} for t in TEAMS])
    return pd.DataFrame(snapshots.values()),pd.DataFrame(history),state

def rankings(schedules,cutoff,parameters=None):
    cutoff=pd.Timestamp(cutoff)
    pre,h,state=replay(schedules,parameters,cutoff)
    _,_,old=replay(schedules,parameters,cutoff-pd.Timedelta(days=7))
    old=old.sort_values(['elo','team'],ascending=[False,True]).reset_index(drop=True)
    old['previous_week_rank']=np.arange(1,len(old)+1)
    state=state.merge(old[['team','elo','previous_week_rank']].rename(columns={'elo':'previous_week_elo'}),on='team')
    state['weekly_change']=state.elo-state.previous_week_elo
    state=state.sort_values(['elo','team'],ascending=[False,True]).reset_index(drop=True)
    state['rank']=np.arange(1,len(state)+1)
    state['record']=state.wins.astype(str)+'-'+state.losses.astype(str)+'-'+state.ties.astype(str)
    state['cutoff']=cutoff
    return state,h
