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
    if 'result_available_at' in completed:
        explicit = completed.set_index('game_id')['result_available_at']
        times = pd.to_datetime(out.game_id.map(explicit),utc=True,errors='raise')
        if (times.notna() & times.lt(out.kickoff)).any():
            raise ValueError('Result availability precedes kickoff')
        out['available_at'] = times.fillna(out.available_at)
    if 'status' in completed:
        blocked = completed.set_index('game_id').status.astype(str).str.lower().isin(['postponed','suspended','in progress','in_progress','canceled','cancelled'])
        out.loc[out.game_id.map(blocked).fillna(False),'available_at'] = pd.NaT
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

def build(schedules, metrics, cutoff=None, game_ids=None, include_team_ratings=False):
    history = team_games(schedules, metrics)
    rows = []
    targets=schedules if game_ids is None else schedules[schedules.game_id.isin(game_ids)]
    for g in targets.sort_values('kickoff').itertuples():
        at = min(g.kickoff, pd.Timestamp(cutoff)) if cutoff is not None else g.kickoff
        home = rating(history,g.home_team,g.season,at)
        away = rating(history,g.away_team,g.season,at)
        row = g._asdict()
        row.pop('Index',None)
        row['data_cutoff'] = at
        if include_team_ratings:
            for side,values in [('home',home),('away',away)]:
                row.update({side+'_rating_'+name:value for name,value in values.items()})
        for key in FEATURES:
            if key == 'neutral':
                continue
            row[key] = (home[key]-away[key]) * (-1 if key in LOWER_BETTER else 1)
        rows.append(row)
    return pd.DataFrame(rows)


def cached_build(schedules, metrics, directory, refresh=False):
    """Content + feature-code keyed historical features; never used for live cutoffs."""
    import hashlib
    from pathlib import Path
    from .data_loader import atomic_parquet
    directory = Path(directory)
    h = hashlib.sha256(Path(__file__).read_bytes())
    for frame in [schedules,metrics]:
        h.update(str(list(frame.dtypes.astype(str))).encode())
        h.update(str(list(frame.columns)).encode())
        h.update(pd.util.hash_pandas_object(frame,index=False).values.tobytes())
    path = directory/f'features-{h.hexdigest()}.parquet'
    from .integrity import digest,atomic_json
    import json
    manifest=path.with_suffix('.json')
    if path.exists() and not refresh:
        if not manifest.exists() or json.loads(manifest.read_text())['sha256']!=digest(path):
            raise ValueError('Feature cache corruption; run features --refresh to rebuild')
        return pd.read_parquet(path)
    frame = build(schedules,metrics)
    atomic_parquet(frame,path)
    atomic_json({'sha256':digest(path),'input_and_code_key':h.hexdigest()},manifest)
    return frame
