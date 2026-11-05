"""M9.1 source observations only; never creates model features or starter claims."""
from pathlib import Path
import json
import inspect
import uuid
import numpy as np
import pandas as pd
import polars as pl
from .data_loader import ALIASES
from .elo import TEAMS
from .ensemble import timestamp
from .ensemble_forecasts import _append, _read
from .integrity import digest
from .odds_store import key
from .reporting import table

SOURCES=['load_injuries','load_depth_charts','load_rosters_weekly','load_player_stats','load_snap_counts']
PERFORMANCE={'load_player_stats','load_snap_counts'}


def utc_now():return pd.Timestamp.now(tz='UTC')


def source_time(value):
    """Do not assign UTC to naive source clocks or date-only strings."""
    if value is None or pd.isna(value):return pd.NaT
    try:
        t=pd.Timestamp(value)
        return t.tz_convert('UTC') if t.tzinfo is not None else pd.NaT
    except (ValueError,TypeError):return pd.NaT


def reconcile(frame,roster=None):
    """Exact GSIS/ESPN/PFR crosswalk only. Never use a name as an identity key."""
    out=pd.Series(None,index=frame.index,dtype='object')
    for column in ['gsis_id','player_id']:
        if column in frame:out=out.fillna(frame[column].replace('',None))
    if roster is not None:
        for column in ['espn_id','pfr_id','pfr_player_id']:
            bridge='pfr_id' if column=='pfr_player_id' else column
            if column not in frame or bridge not in roster or 'gsis_id' not in roster:continue
            pairs=roster[[bridge,'gsis_id']].dropna().drop_duplicates()
            counts=pairs.groupby(bridge).gsis_id.nunique()
            unique=pairs[pairs[bridge].isin(counts[counts.eq(1)].index)].drop_duplicates(bridge)
            mapped=frame[column].map(unique.set_index(bridge).gsis_id)
            conflict=out.notna()&mapped.notna()&out.ne(mapped)
            out=out.fillna(mapped);out.loc[conflict]=None
    return out


def normalize(raw,source,season,roster=None):
    """Lossless source remains separate; this diagnostic view preserves raw statuses."""
    f=raw.to_pandas() if isinstance(raw,pl.DataFrame) else raw.copy()
    def col(*names):
        for name in names:
            if name in f:return f[name]
        return pd.Series(None,index=f.index,dtype='object')
    result=pd.DataFrame({'player_id':reconcile(f,roster),'team':col('team','club_code').replace(ALIASES),
        'position':col('position','pos_abb'),'season':col('season').fillna(season),
        'week':col('week'),'game_type':col('game_type','season_type'),
        'name':col('full_name','player_name','player'),'rank':pd.to_numeric(col('depth_team','pos_rank'),errors='coerce'),
        'game_designation':col('report_status'),'practice_participation':col('practice_status'),
        'reported_injury':col('report_primary_injury'),'secondary_injury':col('report_secondary_injury'),
        'practice_injury':col('practice_primary_injury'),'roster_status':col('status'),
        'source_time_text':col('date_modified','dt')})
    result['source_at']=pd.to_datetime(result.source_time_text.map({v:source_time(v) for v in result.source_time_text.dropna().unique()}),utc=True)
    result['identity_status']=np.where(result.player_id.notna()&result.team.isin(TEAMS),'source_identified','unknown')
    if roster is not None and {'gsis_id','team'}<=set(roster):
        known=set(zip(roster.gsis_id,roster.team.replace(ALIASES)))
        mask=[(pid,t) in known for pid,t in zip(result.player_id,result.team)]
        result['roster_pair_match']=mask
    return result


def preserve(raw,source,season,directory,captured_at):
    """Reprocessing a capture is idempotent; its local receipt cannot be backdated."""
    if source not in SOURCES:raise ValueError('Unsupported personnel source')
    captured_at=timestamp(captured_at);recorded=utc_now()
    if captured_at>recorded:raise ValueError('Capture cannot be future-dated')
    directory=Path(directory);objects=directory/'objects';objects.mkdir(parents=True,exist_ok=True)
    temporary=objects/(uuid.uuid4().hex+'.tmp');raw.write_parquet(temporary)
    sha=digest(temporary);path=objects/(sha+'.parquet')
    try:
        import os
        try:os.link(temporary,path)
        except FileExistsError:
            if digest(path)!=sha:raise ValueError('Personnel object checksum failure')
    finally:temporary.unlink(missing_ok=True)
    payload={'source':source,'season':int(season),'captured_at':captured_at.isoformat(),'created_at':recorded.isoformat(),
        'sha256':sha,'file':path.name,'rows':raw.height,'schema':{c:str(t) for c,t in raw.schema.items()},
        'source_reference':f'https://nflreadr.nflverse.com/reference/{source}.html',
        'provenance':'direct_nflreadpy_capture','publication_at':None}
    identifier=key([source,season,sha,captured_at.isoformat()])
    return _read(_append(directory/'observations',identifier,payload))


def observations(directory):return [_read(p) for p in sorted((Path(directory)/'observations').glob('*.json'))]


def read_raw(directory,observation):
    root=Path(directory)/'objects';path=root/observation['file']
    if path.resolve().parent!=root.resolve() or digest(path)!=observation['sha256']:raise ValueError('Personnel object integrity/path failure')
    return pl.read_parquet(path)


def classify(row,observation,cutoff=None,kickoff=None):
    if row.get('identity_status')=='unknown':return 'unknown'
    at=row.get('source_at');captured=timestamp(observation['captured_at']);recorded=timestamp(observation['created_at'])
    if (pd.notna(at) and timestamp(at)>captured) or (pd.isna(at) and pd.notna(row.get('source_time_text'))):return 'unknown'
    if observation['source'] in PERFORMANCE:return 'retrospective'
    if cutoff is not None and kickoff is not None:
        cutoff=timestamp(cutoff);kickoff=timestamp(kickoff)
        if captured<=cutoff and recorded<=cutoff<kickoff and observation.get('provenance')=='direct_nflreadpy_capture':return 'verified_prospective'
    return 'historical_source_timestamped' if pd.notna(at) else 'retrospective'


def as_of(directory,game,cutoff,_views=None):
    """Read-only capture availability, not a confirmed starter/availability feature."""
    cutoff=timestamp(cutoff);kickoff=timestamp(game['kickoff'])
    if cutoff>utc_now() or cutoff>=kickoff:raise ValueError('Diagnostic cutoff must be nonfuture and before kickoff')
    result=[]
    for o,prepared in (_views if _views is not None else [(o,None) for o in observations(directory)]):
        if o['season']!=int(game['season']) or timestamp(o['captured_at'])>cutoff or timestamp(o['created_at'])>cutoff or o['source'] in PERFORMANCE:continue
        f=prepared if prepared is not None else normalize(read_raw(directory,o),o['source'],o['season'])
        f=f[f.team.isin([game['home_team'],game['away_team']])]
        if f.week.notna().any():f=f[f.week.eq(game['week'])]
        if f.game_type.notna().any():f=f[f.game_type.eq('REG')]
        f=f[f.source_at.isna()|f.source_at.le(timestamp(o['captured_at']))]
        if o['source']=='load_depth_charts' and f.source_at.notna().any():
            # Latest whole team chart; never combine ranks from older chart snapshots.
            f=f[f.source_at.eq(f.groupby('team').source_at.transform('max'))]
        if f.empty:continue
        f['evidence_class']=[classify(r,o,cutoff,kickoff) for r in f.to_dict('records')]
        f['captured_at']=o['captured_at'];f['recorded_at']=o['created_at'];f['publication_at']=None
        f['source']=o['source'];f['source_hash']=o['sha256'];f['game_id']=game['game_id'];f['kickoff']=kickoff;f['forecast_cutoff']=cutoff
        f['assignment']='listed_only_not_confirmed_starter'
        result.append(f)
    return pd.concat(result,ignore_index=True) if result else pd.DataFrame()


def quarterback_list(frame):
    qb=frame[frame.position.eq('QB')].copy()
    qb['role']=np.where(qb['rank'].eq(1),'listed_QB1','listed_backup_or_unknown')
    qb['uncertain']=True
    scope=[c for c in ['season','week','source_at','team'] if c in qb]
    if not qb.empty:
        qb1=qb.player_id.where(qb['rank'].eq(1))
        count=qb.assign(qb1=qb1).groupby(scope,dropna=False).qb1.transform('nunique')
        qb['uncertain']=qb['rank'].isna()|qb.player_id.isna()|count.ne(1)
    return qb.sort_values(['team','rank'],na_position='last')


def collect(data,seasons=None):
    import nflreadpy as nfl
    from nflreadpy.config import update_config
    update_config(cache_mode='off',timeout=20)
    directory=Path(data)/'m91';events=[]
    for season in seasons or [2026]:
        for source in SOURCES:
            try:
                raw=getattr(nfl,source)([season]);captured=utc_now()
                # Inspect/store actual schema before deriving any diagnostic fields.
                saved=preserve(raw,source,season,directory,captured)
                events.append({'source':source,'season':season,'rows':raw.height,'sha256':saved['sha256']})
            except Exception as exc:
                event={'source':source,'season':season,'created_at':utc_now().isoformat(),'error':str(exc)}
                _append(directory/'failures',uuid.uuid4().hex,event);events.append(event)
    return events


def audit_entry(raw,source,season,roster=None):
    f=normalize(raw,source,season,roster)
    weeks=sorted(pd.to_numeric(f.week,errors='coerce').dropna().astype(int).unique().tolist())
    out={'source':source,'season':season,'rows':raw.height,'exact_duplicate_rows':raw.height-raw.hash_rows().n_unique(),
         'weeks':weeks,'teams':int(f.team.nunique()),'players':int(f.player_id.nunique()),
         'missing_player_ids':int(f.player_id.isna().sum()),'unknown_teams':int((~f.team.isin(TEAMS)).sum()),
         'source_timestamp_rows':int(f.source_at.notna().sum()),'missing_game_designation':int(f.game_designation.isna().sum()),
         'qb_rows':int(f.position.eq('QB').sum()),'schema':{c:str(t) for c,t in raw.schema.items()},
         'weekly_rows':{str(k):int(v) for k,v in f.groupby('week').size().items()}}
    known=f.identity_status.ne('unknown')
    out['historical_source_timestamped']=int((known&f.source_at.notna()).sum()) if source not in PERFORMANCE else 0
    out['retrospective']=int((known&f.source_at.isna()).sum()) if source not in PERFORMANCE else int(known.sum())
    out['unknown']=int((~known).sum())
    if 'roster_pair_match' in f:
        identified=f[f.player_id.notna()];out['roster_pair_match_rate']=float(identified.roster_pair_match.mean()) if len(identified) else None
        out['roster_pair_match_denominator']=len(identified)
    return out


def report(root,data):
    root=Path(root);data=Path(data);directory=data/'m91';entries=[];schemas=[];frames={};source_meta=[]
    paths=list((directory/'source_audit').glob('*.json'))
    # Reuse verified preexisting M6 samples; no PBP/player-performance rebuild.
    paths+=list((data/'qb_sources').glob('*.json'))+list((data/'m6_source_inspection').glob('*.json'))
    for meta_path in paths:
        meta=json.loads(meta_path.read_text());source=meta.get('source');year=meta.get('season');path=meta_path.with_suffix('.parquet')
        if source not in SOURCES or not year:continue
        if 'error' in meta:source_meta.append(meta);continue
        if not path.exists():continue
        if digest(path)!=meta['sha256']:raise ValueError('Source audit cache checksum failure')
        k=(source,int(year))
        if k in frames:continue
        frames[k]=pl.read_parquet(path);source_meta.append(meta)
    # Include actual collector snapshots without backdating them as old audit captures.
    for o in observations(directory):
        k=(o['source'],o['season'])
        if k not in frames:frames[k]=read_raw(directory,o)
    qbs=[]
    for (source,season),raw in sorted(frames.items()):
        roster=frames.get(('load_rosters_weekly',season));roster=roster.to_pandas() if roster is not None else None
        item=audit_entry(raw,source,season,roster);schemas.append({'source':source,'season':season,'schema':item.pop('schema'),'weekly_rows':item.pop('weekly_rows')});entries.append(item)
        if source=='load_depth_charts':
            qb=quarterback_list(normalize(raw,source,season,roster));qbs.append(qb.assign(audit_season=season))
    out=root/'reports/m91';out.mkdir(parents=True,exist_ok=True)
    (out/'schemas_and_weekly_counts.json').write_text(json.dumps(schemas,indent=2,default=str))
    pd.DataFrame(entries).to_csv(out/'coverage.csv',index=False)
    obs=observations(directory);classes={};available=0;linked_games=set();current_qb=[]
    performance_ids=set();active=data/'m6/qb_performance/active.json'
    if active.exists():
        for info in json.loads(active.read_text())['files']:
            p=active.parent/info['file']
            if p.resolve().parent!=active.parent.resolve() or digest(p)!=info['sha256']:raise ValueError('M6 performance integrity failure')
            performance_ids.update(pd.read_parquet(p,columns=['player_id']).player_id.dropna().tolist())
    depth_ids=set(pd.concat(qbs).player_id.dropna()) if qbs else set()
    crosscheck={'m6_cached_qb_ids':len(performance_ids),'depth_qb_ids':len(depth_ids),'matched_ids':len(depth_ids&performance_ids),'unmatched_ids':len(depth_ids-performance_ids)}
    # Diagnostic linkage uses cached schedules only, without metrics/PBP scans.
    pointer=data/'manifests/2026.json'
    if pointer.exists():
        meta=json.loads(pointer.read_text());generation=data/'generations'/meta['generation'];info=meta['files']['schedules'];path=generation/info['file']
        if generation.resolve().parent!=(data/'generations').resolve() or path.resolve().parent!=generation.resolve() or digest(path)!=info['sha256']:raise ValueError('Schedule integrity/path failure')
        s=pd.read_parquet(path);now=utc_now();views=[]
        for o in obs:
            if o['source'] in PERFORMANCE:continue
            f=normalize(read_raw(directory,o),o['source'],o['season'])
            if o['source']=='load_depth_charts' and f.source_at.notna().any():
                f=f[f.source_at.le(timestamp(o['captured_at']))]
                f=f[f.source_at.eq(f.groupby('team').source_at.transform('max'))]
            views.append((o,f))
        upcoming=s[s.game_type.eq('REG')&~s.completed&s.kickoff.gt(now)]
        for g in upcoming.to_dict('records'):
            f=as_of(directory,g,now,views)
            if len(f):
                linked_games.add(g['game_id']);available+=len(f)
                for c,n in f.evidence_class.value_counts().items():classes[c]=classes.get(c,0)+int(n)
                current_qb.append(quarterback_list(f))
    import nflreadpy as nfl
    lines=['# M9.1 personnel source audit and prospective evidence','',
        'No new model, feature, forecast probability, personnel weighting or starter inference was created. M6 evidence is reused for comparison, not silently promoted into this independent additive store.','',
        '## Inventory and measured coverage','',
        table(pd.DataFrame([{'source':n,'installed_signature':str(inspect.signature(getattr(nfl,n))),'documented_start':{'load_injuries':2009,'load_depth_charts':2001,'load_rosters_weekly':2002,'load_player_stats':1999,'load_snap_counts':2012}[n]} for n in SOURCES])),'',
        'Documented start years describe library support, not verified complete availability. Representative full-season downloads were inspected first (2019, 2026); injury/depth samples extend the 2019–2026 audit. Cached 2024 depth charts and M6 player samples are reused. Unlisted source/seasons are unmeasured; no complete 2019–2026 roster/stat/snap coverage is claimed.','',table(pd.DataFrame(entries)),'',
        'All counts include source regular/postseason rows where present. Week lists/weekly counts do not prove all expected games or timely reports. Duplicate counts are exact full-row duplicates; different updates/ranks are preserved, not deduplicated into an invented truth. Missing player IDs and unknown teams stay uncertain.','',
        '## Actual schemas','']
    for entry in schemas:lines.extend([f"### {entry['source']} / {entry['season']}",'',json.dumps(entry['schema'],sort_keys=True),''])
    lines.extend(['## Temporal integrity and prospective capture','',
        'Source event/update times (`date_modified`, `dt`), original publication time (unknown), actual capture time, local receipt time, forecast cutoff and kickoff remain distinct. Naive/date-only source times are retained verbatim but are not assigned an invented timezone. `dt` and `date_modified` never prove original public availability. Historic source-timestamped rows remain historical; actual participation/stats/snaps are retrospective performance, not pregame starter evidence.','',
        f'Actual collector observations: **{len(obs)}**; linked upcoming games: **{len(linked_games)}**; diagnostic linked rows: **{available}**. Evidence classes within those game/observation links: `{json.dumps(classes,sort_keys=True)}`. Rows may link to multiple future games and observations; these are not independent games or unique reports.','',
        'Verified prospective means the source contents were directly captured and locally preserved before the diagnostic cutoff and kickoff, with identified player/team and no future source timestamp. It verifies possession of that evidence, not truth of a listed starter or availability. Week-bearing sources match season/week/team and REG. Timestamped charts use the latest whole team chart inside each observation; absent week/effective-date proof remains a relevance/staleness limitation. Historical source audits are never automatically imported into the prospective store.','',
        '## Quarterback and injury interpretation','',
        'Rank 1 means listed QB1, never confirmed starter. All backups and missing ranks are retained. Equal-scope multiple QB1 identities and missing IDs/ranks are uncertain. No actual participation is used to choose a starter. GSIS keys are matched exactly; ESPN/PFR bridging requires unique roster mappings. Name similarity is never used. Roster-pair match rates above measure exact player/team overlap across the sampled season, not labeled identity accuracy or pregame roster membership. Week-specific reconciliation and transfers can remain unresolved.','',
        'Questionable, Doubtful, Out and null statuses stay distinct, with original practice, primary/secondary injury and roster status fields. Missing status is not healthy, active or absent. Rosters are not injury reports. A source may have no current-week report; no missing source rows are synthesized. Revisions are distinct immutable source observations, and earlier statuses remain queryable.',''])
    if current_qb:
        qb=pd.concat(current_qb,ignore_index=True);examples=qb[qb.uncertain.eq(True)].head(8)
        lines.extend(['Current ambiguous QB examples (if observed):','',table(examples[['game_id','team','player_id','rank','role','uncertain']]) if len(examples) else 'No ambiguous QB1 ties detected in the linked snapshots; this does not confirm any starter.',''])
    lines.extend(['## Suitability and limitations','',
        'The observed sources do not establish a meaningful verified historical pregame QB/injury experiment. Historical timestamps lack independently verified original publication/capture evidence; current captures cannot be backdated to old games. Continue evidence collection for future M9.2 assessment; no modeling decision or adjustment is implemented. Missing IDs, changing schemas, delayed/stale charts, absent current injury weeks and source revisions limit even prospective use.','',
        'Actual exact-ID cross-check against checksum-verified existing M6 compact QB performance (no PBP reads/rebuild): '+json.dumps(crosscheck)+'. This is career/sample identity overlap, not current availability or starter accuracy. Performance is retrospective; only prior eligible games could support future historical-statistics work, and no strength formula is used here.','',
        '## Operation and verification','',
        '`python -m nfl_predictor.cli collect-personnel` captures the five available current-season sources using bounded explicit nflreadpy calls, preserving lossless Polars Parquet plus SHA-256 receipts under data/m91. It does not refresh football schedules, train models, issue predictions or touch old ledgers. Partial failures are appended separately; previous snapshots survive. Exact observation reprocessing is idempotent; a later capture of unchanged bytes is a new observation with its own real timestamp.','',
        '`python -m nfl_predictor.cli report-m91` is offline and reads source audits/captures plus cached schedules. `as_of(directory, game, cutoff)` is read-only and requires capture AND local receipt by the nonfuture pregame cutoff; late imports cannot establish earlier availability. Source hashes and metadata are checked on every read. Source publication is left null rather than invented.','',
        'Detailed schemas and per-week counts: reports/m91/schemas_and_weekly_counts.json; coverage: reports/m91/coverage.csv. Raw datasets remain gitignored.','',
        'Windows / Python 3.12 acceptance: `python -m pytest -q tests/test_m91.py`; `python -m nfl_predictor.cli collect-personnel`; `python -m nfl_predictor.cli report-m91`. No native Windows verification is claimed. Test results and preservation measurements follow after execution.',''])
    report=root/'M91_PERSONNEL_DATA_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8');return report
