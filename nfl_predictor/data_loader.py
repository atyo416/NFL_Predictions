"""Atomic season caches. nflverse schedules use US Eastern kickoff clock times."""
from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
import numpy as np

ALIASES = {'OAK':'LV','SD':'LAC','STL':'LA','LAR':'LA','JAC':'JAX','WSH':'WAS'}
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def require(df, columns, source):
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f'{source}: missing columns {sorted(missing)}; refresh source or check nflreadpy schema')

def normalize_schedules(df):
    df = df.copy()
    require(df, ['game_id','season','week','game_type','gameday','gametime','home_team','away_team','home_score','away_score'], 'schedules')
    df = df[df.game_type.eq('REG')].drop_duplicates('game_id', keep='last')
    if df.game_id.isna().any():
        raise ValueError('schedules: null game IDs')
    for c in ['home_team','away_team']:
        df[c] = df[c].replace(ALIASES)
    local = pd.to_datetime(df.gameday.astype(str)+' '+df.gametime.astype(str), errors='coerce')
    df['kickoff'] = local.dt.tz_localize('America/New_York', ambiguous='NaT', nonexistent='NaT').dt.tz_convert('UTC')
    if df.kickoff.isna().any():
        raise ValueError('schedules: missing/invalid kickoff; cannot safely build pregame features')
    if df[['home_team','away_team']].isna().any().any() or df.home_team.eq(df.away_team).any():
        raise ValueError('schedules: missing or identical teams')
    for c in ['home_score','away_score']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['neutral'] = df.get('location', pd.Series('Home', index=df.index)).eq('Neutral').astype(int)
    df['completed'] = df.home_score.notna() & df.away_score.notna() & df.kickoff.lt(pd.Timestamp.now(tz='UTC'))
    if ((df.home_score.dropna() < 0).any() or (df.away_score.dropna() < 0).any()):
        raise ValueError('schedules: negative final scores')
    if 'status' in df:
        df.loc[df.status.astype(str).str.lower().isin(['scheduled','in progress','in_progress','postponed','suspended','canceled','cancelled']), 'completed'] = False
    df['target'] = np.where(df.completed & df.home_score.ne(df.away_score), (df.home_score > df.away_score).astype(float), np.nan)
    return df.sort_values('kickoff').reset_index(drop=True)

def aggregate_pbp(pbp):
    require(pbp, ['game_id','posteam','defteam','play_type','epa','yards_gained','interception','fumble_lost','qb_kneel','qb_spike'], 'play-by-play')
    p = pbp.copy()
    for c in ['posteam','defteam']:
        p[c] = p[c].replace(ALIASES)
    # Scrimmage rush/pass including sacks; omit kneels, spikes, no-plays and special teams.
    p = p[p.play_type.isin(['run','pass']) & p.qb_kneel.eq(0) & p.qb_spike.eq(0) & p.epa.notna() & p.posteam.notna() & p.defteam.notna()].copy()
    p['success'] = p.epa.gt(0).astype(float)
    p['turnovers'] = p.interception.fillna(0) + p.fumble_lost.fillna(0)
    out = []
    for side, team in [('off','posteam'),('def','defteam')]:
        g = p.groupby(['game_id',team]).agg(epa=('epa','mean'),success=('success','mean'),yards=('yards_gained','mean'),turnovers=('turnovers','sum'),plays=('epa','size')).reset_index().rename(columns={team:'team'})
        g = g.rename(columns={c:f'{side}_{c}' for c in ['epa','success','yards','turnovers','plays']})
        out.append(g)
    return out[0].merge(out[1], on=['game_id','team'], how='outer', validate='one_to_one')

def atomic_parquet(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp.parquet')
    df.to_parquet(tmp, index=False)
    tmp.replace(path)

def update(seasons=range(2018,2027), refresh=False):
    import nflreadpy as nfl
    from nflreadpy.config import update_config
    update_config(cache_mode='off' if refresh else 'memory')
    for season in seasons:
        if not 2018 <= season <= 2026:
            raise ValueError('Supported seasons: 2018–2026')
        schedule_path = DATA / 'processed' / f'schedule_{season}.parquet'
        metrics_path = DATA / 'processed' / f'metrics_{season}.parquet'
        from .integrity import read_season, publish
        pointer = DATA/'manifests'/f'{season}.json'
        if pointer.exists() and not refresh:
            read_season(DATA,season,include_pbp=False)
            continue
        if schedule_path.exists() and metrics_path.exists() and not refresh:
            raw_path = DATA/'raw'/f'pbp_{season}.parquet'
            if raw_path.exists():
                meta_path = DATA/'processed'/f'metadata_{season}.json'
                stamp = json.loads(meta_path.read_text()).get('retrieved_at') if meta_path.exists() else None
                publish(DATA,season,pd.read_parquet(schedule_path),pd.read_parquet(metrics_path),pd.read_parquet(raw_path),stamp)
                continue
        try:
            schedules = normalize_schedules(nfl.load_schedules([season]).to_pandas())
            pbp = nfl.load_pbp([season]).to_pandas()
            metrics = aggregate_pbp(pbp)
            # Validate before replacing any season's existing cache.
            if schedules.empty or metrics.empty:
                raise ValueError('Source returned no regular-season schedules or eligible plays')
            manifest = publish(DATA,season,schedules,metrics,pbp)
            print({'season':season,'retrieved_at':manifest['retrieved_at'],'games':len(schedules)},flush=True)
        except Exception as exc:
            raise RuntimeError(f'Download/validation failed for {season}; existing cache retained where possible: {exc}') from exc

def cached(seasons=None, data=None):
    from .integrity import read_season
    from .data_validation import coverage
    import warnings
    root=Path(data) if data is not None else DATA
    pointers = {int(p.stem):p for p in (root/'manifests').glob('*.json')}
    legacy = {int(p.stem.split('_')[-1]):p for p in (root/'processed').glob('schedule_*.parquet')}
    # Preserve the original M1–M4 feature history unless expansion is explicit.
    selected=set(range(2018,2027) if seasons is None else seasons)
    pointers={year:path for year,path in pointers.items() if year in selected}
    legacy={year:path for year,path in legacy.items() if year in selected}
    if not pointers and not legacy:
        raise FileNotFoundError('No cache. Run python -m nfl_predictor.cli update first.')
    schedule_frames, metric_frames = [], []
    for season in sorted(pointers.keys() | legacy.keys()):
        if season in pointers:
            frames, meta = read_season(root,season,include_pbp=False)
            schedule_frames.append(frames['schedules']); metric_frames.append(frames['metrics'])
        else:
            warnings.warn(f'Legacy cache {season} has no verified manifest; run update to adopt it.',stacklevel=2)
            schedule_frames.append(pd.read_parquet(legacy[season]))
            metric_frames.append(pd.read_parquet(root/'processed'/f'metrics_{season}.parquet'))
    schedules = pd.concat(schedule_frames,ignore_index=True)
    team_metrics = pd.concat(metric_frames,ignore_index=True)
    coverage(schedules,team_metrics)
    return schedules,team_metrics
