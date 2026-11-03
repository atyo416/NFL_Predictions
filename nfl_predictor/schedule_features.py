"""Schedule-derived context from the current source vintage, not archived revisions."""
import numpy as np
import pandas as pd
from .elo import regular_games,eligible_at

REST_FEATURES=['rest_advantage','bye_difference','short_rest_difference','extended_rest_difference']

def schedule_features(schedules,cutoff=None,short_days=6.,extended_days=10.,game_ids=None):
    if short_days<=0 or extended_days<=short_days: raise ValueError('Invalid rest thresholds')
    f=regular_games(schedules)
    if cutoff is not None:
        cutoff=pd.Timestamp(cutoff)
        if cutoff.tzinfo is None: raise ValueError('Cutoff must be timezone aware')
    rows=[]; byes={}; team_schedules={}
    for season,season_frame in f.groupby('season'):
        for team in set(season_frame.home_team)|set(season_frame.away_team):
            t=season_frame[season_frame.home_team.eq(team)|season_frame.away_team.eq(team)].sort_values('kickoff')
            team_schedules[season,team]=t
            # A missing late/canceled game must not be labeled a scheduled bye.
            # At least 16 entries and one gap within normal NFL bye weeks required.
            absent=set(range(4,15))-set(t.week)
            byes[season,team]=next(iter(absent)) if len(t)>=16 and len(absent)==1 else None
    targets=f if game_ids is None else f[f.game_id.isin(game_ids)]
    for g in targets.to_dict('records'):
        at=min(g['kickoff'],cutoff) if cutoff is not None else g['kickoff']
        row={'game_id':g['game_id']}
        for side in ['home','away']:
            t=team_schedules[g['season'],g[side+'_team']]
            past=t[t.kickoff.lt(at)]
            past=past[past.apply(lambda r:pd.notna(eligible_at(r)) and eligible_at(r)<at,axis=1)] if len(past) else past
            last=past.iloc[-1] if len(past) else None
            days=(g['kickoff']-last.kickoff).total_seconds()/86400 if last is not None else np.nan
            bye_week=byes[g['season'],g[side+'_team']]
            # Week 1 cannot follow an in-season bye; incomplete later schedules are unknown.
            bye=float(g['week']==bye_week+1) if bye_week is not None else (0. if g['week']==1 else np.nan)
            short=float(days<short_days) if pd.notna(days) else np.nan
            extended=float(days>extended_days and bye==0) if pd.notna(days) and pd.notna(bye) else np.nan
            row.update({side+'_rest_days':days,side+'_bye':bye,side+'_short_rest':short,side+'_extended_rest':extended,side+'_bye_week':bye_week})
        row.update({'rest_advantage':row['home_rest_days']-row['away_rest_days'],'bye_difference':row['home_bye']-row['away_bye'],'short_rest_difference':row['away_short_rest']-row['home_short_rest'],'extended_rest_difference':row['home_extended_rest']-row['away_extended_rest']})
        rows.append(row)
    return pd.DataFrame(rows)

def post_bye_diagnostic(frame):
    rows=[]
    for side in ['home','away']:
        for g in frame[frame.completed].to_dict('records'):
            bye=g.get(side+'_bye')
            if pd.isna(bye): continue
            score=g[side+'_score']-g[('away' if side=='home' else 'home')+'_score']
            rows.append({'season':g['season'],'bye':int(bye),'result':.5 if score==0 else float(score>0),'margin':score})
    if not rows: return pd.DataFrame(columns=['season','bye','team_games','win_fraction','mean_margin'])
    return pd.DataFrame(rows).groupby(['season','bye']).agg(team_games=('result','size'),win_fraction=('result','mean'),mean_margin=('margin','mean')).reset_index()
