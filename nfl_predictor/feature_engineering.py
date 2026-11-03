"""Conservative availability: a final becomes eligible at kickoff + 8 hours.
No exact final timestamp is supplied by nflverse schedules. This intentionally
excludes potentially overlapping games rather than inferring availability by week.
"""
import numpy as np
import pandas as pd
METRICS = ['off_epa','def_epa','scoring','turnover','off_success','def_success','win','off_yards','def_yards']
FEATURES = METRICS + ['recent_off_epa','recent_def_epa','rest','neutral']
LOWER_BETTER = {'def_epa','def_success','def_yards','recent_def_epa'}

def team_games(schedules, metrics):
    completed = schedules[schedules.completed].copy()
    rows = []
    for side, other in [('home','away'),('away','home')]:
        t = completed[['game_id','season','week','kickoff']].copy()
        t['team'] = completed[f'{side}_team']
        t['scoring'] = completed[f'{side}_score'] - completed[f'{other}_score']
        t['win'] = np.where(t.scoring.eq(0), .5, t.scoring.gt(0).astype(float))
        rows.append(t)
    out = pd.concat(rows).merge(metrics, on=['game_id','team'], how='left', validate='one_to_one')
    out['turnover'] = out.def_turnovers - out.off_turnovers
    out['available_at'] = out.kickoff + pd.Timedelta(hours=8)
    return out

def rating(history, team, season, cutoff, prior_weight=4., regression=.5):
    cutoff = pd.Timestamp(cutoff)
    if cutoff.tzinfo is None:
        raise ValueError('Cutoff must be timezone aware')
    h = history[history.available_at.lt(cutoff) & history.kickoff.lt(cutoff)]
    # Previous-season priors only; no current-season league mean can leak future games.
    prev = h[h.season.eq(season-1)]
    league = prev[METRICS].mean()
    prior = prev[prev.team.eq(team)][METRICS].mean()
    prior = regression * prior.fillna(league) + (1-regression) * league
    current = h[h.team.eq(team) & h.season.eq(season)].sort_values('kickoff')
    n = current[METRICS].count()
    values = (prior_weight*prior + current[METRICS].sum(min_count=1).fillna(0))/(prior_weight+n)
    values = values.where(prior.notna(), current[METRICS].mean())
    result = values.to_dict()
    for metric in ['off_epa','def_epa']:
        recent = current.tail(3)[metric].dropna()
        result['recent_'+metric] = (prior_weight*prior[metric]+recent.sum())/(prior_weight+len(recent)) if pd.notna(prior[metric]) else recent.mean()
    past = h[h.team.eq(team)].sort_values('kickoff')
    result['rest'] = (cutoff-past.iloc[-1].kickoff).total_seconds()/86400 if len(past) else np.nan
    return result

def build(schedules, metrics, cutoff=None):
    history = team_games(schedules, metrics)
    rows = []
    for g in schedules.sort_values('kickoff').itertuples():
        at = min(g.kickoff, pd.Timestamp(cutoff)) if cutoff is not None else g.kickoff
        home = rating(history,g.home_team,g.season,at)
        away = rating(history,g.away_team,g.season,at)
        row = g._asdict()
        row.pop('Index',None)
        row['data_cutoff'] = at
        for key in FEATURES:
            if key == 'neutral':
                continue
            row[key] = (home[key]-away[key]) * (-1 if key in LOWER_BETTER else 1)
        rows.append(row)
    return pd.DataFrame(rows)
