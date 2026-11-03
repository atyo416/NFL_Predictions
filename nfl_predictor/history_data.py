"""Season-bounded historical ingestion with explicit unknown-clock intervals."""
from pathlib import Path
from datetime import datetime,timezone
import gc
import json
import shutil
import numpy as np
import pandas as pd
from .data_loader import normalize_schedules,aggregate_pbp,require,ALIASES
from .integrity import publish,read_season,atomic_json,digest

PROCESSING='history-m5-v1'
PBP_REQUIRED=['game_id','posteam','defteam','play_type','epa','yards_gained','interception','fumble_lost','qb_kneel','qb_spike']

def normalize_history(raw):
    raw=raw.copy()
    require(raw,['gameday','gametime','game_id','location'],'historical schedules')
    unknown=raw.gametime.isna() | raw.gametime.astype(str).str.strip().isin(['','nan','None'])
    # Midnight is an explicitly labeled LOWER BOUND, not an inferred kickoff.
    raw.loc[unknown,'gametime']='00:00'
    f=normalize_schedules(raw)
    f['kickoff_precision']=np.where(f.game_id.isin(raw.loc[unknown,'game_id']),'date_lower_bound','scheduled_clock')
    f['actual_kickoff']=f.kickoff.where(f.kickoff_precision.eq('scheduled_clock'))
    local_day=pd.to_datetime(f.gameday.astype(str),errors='raise')
    latest=(local_day+pd.Timedelta(days=1,hours=8)).dt.tz_localize('America/New_York').dt.tz_convert('UTC')
    f['result_available_at']=f.kickoff+pd.Timedelta(hours=8)
    f.loc[f.kickoff_precision.eq('date_lower_bound'),'result_available_at']=latest
    f['neutral_known']=f.location.notna()
    return f

def metrics_history(raw):
    metrics=aggregate_pbp(raw)
    p=raw[raw.play_type.isin(['run','pass']) & raw.qb_kneel.eq(0) & raw.qb_spike.eq(0) & raw.epa.notna() & raw.posteam.notna() & raw.defteam.notna()].copy()
    p['team']=p.posteam.replace(ALIASES)
    p['net_passing_yards']=p.yards_gained.where(p.play_type.eq('pass'),0)
    p['rushing_yards']=p.yards_gained.where(p.play_type.eq('run'),0)
    p['passing_plays']=p.play_type.eq('pass').astype(int);p['rushing_plays']=p.play_type.eq('run').astype(int)
    production=p.groupby(['game_id','team'])[['net_passing_yards','rushing_yards','passing_plays','rushing_plays']].sum(min_count=1).reset_index()
    return metrics.merge(production,on=['game_id','team'],how='left',validate='one_to_one')

def season_audit(schedules,metrics,pbp,season):
    required_metrics=['off_epa','def_epa','off_success','def_success','off_yards','def_yards','off_turnovers','def_turnovers']
    eligible=schedules[schedules.completed]
    support=[]
    for side in ['home','away']:
        t=eligible.merge(metrics,left_on=['game_id',side+'_team'],right_on=['game_id','team'],how='left')
        support.append(t[required_metrics].notna().all(axis=1).to_numpy())
    usable=support[0]&support[1] if len(eligible) else np.array([],dtype=bool)
    expected=248 if season<=2001 else 256 if season<=2020 else 272
    missing_metrics=eligible.loc[~usable,'game_id'].tolist() if len(eligible) else []
    record={'season':int(season),'processing_version':PROCESSING,'source':'nflverse via nflreadpy','schedule_games':len(schedules),'expected_regular_games':expected,'completed_games':len(eligible),'ties':int((eligible.home_score==eligible.away_score).sum()),'pbp_rows':len(pbp),'metric_team_games':len(metrics),'missing_required_columns':sorted(set(PBP_REQUIRED)-set(pbp)),'source_metric_coverage':float(usable.mean()) if len(usable) else 0.,'missing_metric_games':missing_metrics,'clock_known_fraction':float(schedules.kickoff_precision.eq('scheduled_clock').mean()) if 'kickoff_precision' in schedules else 1.,'venue_known_fraction':float(schedules.location.notna().mean()),'completeness':'complete_source_metrics' if len(schedules)==expected and usable.all() else 'review_required','schema':{'schedules':{c:str(t) for c,t in schedules.dtypes.items()},'pbp':{c:str(t) for c,t in pbp.dtypes.items()}},'missing_rates':{c:float(pbp[c].isna().mean()) for c in pbp},'metric_distributions':{c:{'mean':float(metrics[c].mean()),'median':float(metrics[c].median()),'std':float(metrics[c].std())} for c in required_metrics}}
    if season==2022 and len(schedules)==271 and usable.all():record['completeness']='known_canceled_game_exception'
    return record

def update_history(data,start=1999,end=2017,refresh=False,inspection=None):
    if not 1999<=start<=end<=2026:raise ValueError('History range must be within 1999–2026')
    import nflreadpy as nfl
    from nflreadpy.config import update_config
    update_config(cache_mode='off') # Our own manifests provide reuse, without retaining 28 raw seasons in RAM.
    data=Path(data)
    for season in range(start,end+1):
        pointer=data/'manifests'/f'{season}.json'
        if pointer.exists() and not refresh:
            read_season(data,season,include_pbp=False);print(f'{season}: verified cache reused',flush=True);continue
        if shutil.disk_usage(data.parent).free<512*1024**2:raise RuntimeError('Less than 512 MiB free disk; free space before historical ingestion')
        print(f'{season}: downloading/processing one season',flush=True)
        try:
            prior=Path(inspection or data/'history_inspection')
            if not refresh and all((prior/name).exists() for name in [f'schedules_{season}.parquet',f'pbp_{season}.parquet',f'{season}.json']):
                meta=json.loads((prior/f'{season}.json').read_text())
                if digest(prior/f'schedules_{season}.parquet')!=meta['schedules_sha256'] or digest(prior/f'pbp_{season}.parquet')!=meta['pbp_sha256']:raise ValueError('Inspected historical source checksum mismatch')
                raw_s=pd.read_parquet(prior/f'schedules_{season}.parquet');pbp=pd.read_parquet(prior/f'pbp_{season}.parquet');stamp=meta['retrieved_at']
            else:
                raw_s=nfl.load_schedules([season]).to_pandas();pbp=nfl.load_pbp([season]).to_pandas();stamp=datetime.now(timezone.utc).isoformat()
            require(pbp,PBP_REQUIRED,f'play-by-play {season}')
            schedules=normalize_history(raw_s);metrics=metrics_history(pbp)
            if schedules.empty or metrics.empty:raise ValueError('Empty regular-season schedules or scrimmage metrics')
            audit=season_audit(schedules,metrics,pbp,season)
            manifest=publish(data,season,schedules,metrics,pbp,stamp,audit)
            print(f"{season}: committed {len(schedules)} games, {len(pbp)} plays; {audit['source_metric_coverage']:.1%} source metric coverage; {audit['clock_known_fraction']:.1%} known clocks",flush=True)
            del raw_s,pbp,schedules,metrics,manifest,audit
            gc.collect()
        except Exception as exc:
            raise RuntimeError(f'Historical season {season} failed; previous manifest unchanged. Fix the source/access issue and rerun to resume: {exc}') from exc

def audit_history(data,directory):
    data=Path(data);directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    records=[]
    for pointer in sorted((data/'manifests').glob('*.json')):
        year=int(pointer.stem)
        if not 1999<=year<=2026:continue
        frames,meta=read_season(data,year,include_pbp=False)
        if 'processing' in meta:record=meta['processing']
        else:
            pbp_path=data/'generations'/meta['generation']/meta['files']['pbp']['file']
            raw=pd.read_parquet(pbp_path);record=season_audit(frames['schedules'],frames['metrics'],raw,year);del raw;gc.collect()
        records.append({**record,'retrieved_at':meta['retrieved_at'],'generation':meta['generation'],'files':meta['files'],'disk_bytes':sum((data/'generations'/meta['generation']/info['file']).stat().st_size for info in meta['files'].values())})
    atomic_json(records,directory/'source_audit.json')
    columns=['season','schedule_games','expected_regular_games','completed_games','ties','pbp_rows','source_metric_coverage','clock_known_fraction','venue_known_fraction','completeness','retrieved_at','disk_bytes']
    pd.DataFrame(records)[columns].to_csv(directory/'source_audit.csv',index=False)
    return records


def load_history(data,start=1999,end=2026):
    data=Path(data);schedules=[];metrics=[]
    missing=[year for year in range(start,end+1) if not (data/'manifests'/f'{year}.json').exists()]
    if missing:raise ValueError(f'Missing historical seasons {missing}; run update-history for those years before comparing complete windows')
    for year in range(start,end+1):
        frames,_=read_season(data,year,include_pbp=False)
        s=frames['schedules'].copy()
        if 'kickoff_precision' not in s:s['kickoff_precision']='scheduled_clock'
        if 'neutral_known' not in s:s['neutral_known']=s.location.notna()
        if 'result_available_at' not in s:s['result_available_at']=s.kickoff+pd.Timedelta(hours=8)
        schedules.append(s);metrics.append(frames['metrics'])
    return pd.concat(schedules,ignore_index=True),pd.concat(metrics,ignore_index=True)
