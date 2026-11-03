"""Versioned evidence ledger, strict pregame gates and prospective context snapshots.
No contemporary or retrospective source is silently promoted to verified evidence.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
import uuid
import numpy as np
import pandas as pd
from .data_loader import ALIASES
from .elo import TEAMS,regular_games,eligible_at
from .integrity import atomic_json,digest
from .player_performance import qb_rating

GROUPS=['OL','WR','RB','TE','DL','LB','DB']
POSITIONS={**{p:'OL' for p in ['OL','C','G','OG','OT','T']},**{p:'DL' for p in ['DL','DT','DE','NT']},**{p:'LB' for p in ['LB','ILB','OLB']},**{p:'DB' for p in ['DB','CB','S','FS','SS']},'WR':'WR','RB':'RB','FB':'RB','TE':'TE','QB':'QB'}
STATUSES={'confirmed_starter','likely_starter','questionable','ruled_out','unknown'}
FIELDS=['game_id','team','player_id','position','source_name','source_reference','source_at','observed_at','forecast_cutoff','availability','quality','verification_status']
QB_FEATURES=['qb_expected_epa_difference','qb_change_gap_difference','qb_recent_epa_difference','qb_experience_difference']
PLAYER_FEATURES=['ol_unavailable_starters_advantage']

def empty_evidence():return pd.DataFrame(columns=FIELDS+['is_starter','coverage_groups','evidence_id','recorded_at'])

def normalize_evidence(records):
    f=records.copy()
    missing=set(FIELDS)-set(f)
    if missing:raise ValueError(f'Personnel evidence missing fields {sorted(missing)}')
    if f.empty:return empty_evidence()
    for field in ['source_at','observed_at','forecast_cutoff']:
        for value in f[field]:
            if pd.notna(value) and pd.Timestamp(value).tzinfo is None:raise ValueError('Personnel timestamps must be timezone aware; date-only claims are unverified')
        f[field]=pd.to_datetime(f[field],utc=True)
    f['team']=f.team.replace(ALIASES);f['position']=f.position.astype(str).str.strip().str.upper()
    if not f.team.isin(TEAMS).all() or not f.availability.isin(STATUSES).all() or not f.verification_status.isin(['verified_pregame','retrospective','unverified']).all():raise ValueError('Unknown team, availability or verification class')
    if f[['game_id','player_id','source_name','quality']].isna().any().any():raise ValueError('Personnel evidence requires identities and provenance')
    if 'is_starter' not in f:f['is_starter']=None
    if 'coverage_groups' not in f:f['coverage_groups']='[]'
    for field in ['is_starter']:
        if any(pd.notna(v) and not isinstance(v,(bool,np.bool_)) for v in f[field]):raise ValueError('Starter designation must be true/false/unknown, not an inferred role')
    normalized=[]
    for value in f.coverage_groups:
        groups=json.loads(value) if isinstance(value,str) else (value if isinstance(value,list) else [])
        if set(groups)-set(GROUPS):raise ValueError('Unknown availability coverage group')
        normalized.append(json.dumps(sorted(set(groups))))
    f['coverage_groups']=normalized
    verified=f.verification_status.eq('verified_pregame')
    if (verified&~f.position.isin(POSITIONS)).any():raise ValueError('Verified personnel position must use a supported position code')
    required_time=f[['source_at','observed_at','forecast_cutoff']].notna().all(axis=1)
    references=f.source_reference.fillna('').astype(str).str.strip().ne('')
    timely=f.source_at.lt(f.forecast_cutoff)&f.observed_at.lt(f.forecast_cutoff)&f.source_at.le(f.observed_at)
    if (verified&~(required_time&references&timely)).any():raise ValueError('Verified personnel evidence requires a reference and source/observation times strictly before its cutoff')
    if (f.observed_at>pd.Timestamp.now(tz='UTC')).any():raise ValueError('Personnel observations cannot be future-dated')
    for c in ['game_id','player_id','source_name','quality']:
        if f[c].astype(str).str.strip().eq('').any():raise ValueError('Empty personnel identity/provenance')
    return f

def _canonical(record):
    return {k:(None if pd.isna(v) else v.isoformat() if isinstance(v,pd.Timestamp) else bool(v) if isinstance(v,np.bool_) else v) for k,v in record.items() if k not in ['evidence_id','recorded_at']}

def import_evidence(path,directory):
    raw=json.loads(Path(path).read_text());f=normalize_evidence(pd.DataFrame(raw))
    old=load_evidence(directory);stamp=datetime.now(timezone.utc).isoformat()
    f['evidence_id']=[hashlib.sha256(json.dumps(_canonical(r),sort_keys=True).encode()).hexdigest() for r in f.to_dict('records')]
    f['recorded_at']=stamp
    result=pd.concat([old,f],ignore_index=True).drop_duplicates('evidence_id',keep='first')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);generation=uuid.uuid4().hex
    file=directory/f'{generation}.parquet';result.to_parquet(file,index=False)
    meta={'schema_version':1,'file':file.name,'sha256':digest(file),'rows':len(result),'import_source_sha256':digest(path),'captured_at':stamp,'note':'Operator-verified claims are not automatically authenticated; retain original source references.'}
    atomic_json(meta,directory/f'{generation}.json');atomic_json(meta,directory/'latest.json')
    return file

def load_evidence(directory):
    directory=Path(directory);pointer=directory/'latest.json'
    if not pointer.exists():return empty_evidence()
    meta=json.loads(pointer.read_text());path=directory/meta['file']
    if path.resolve().parent!=directory.resolve() or digest(path)!=meta['sha256']:raise ValueError('Personnel evidence cache checksum/path mismatch')
    f=pd.read_parquet(path)
    if meta.get('schema_version')!=1 or len(f)!=meta['rows']:raise ValueError('Personnel evidence schema/row-count mismatch')
    return f

def eligible_evidence(records,game_id,team,cutoff):
    cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None:raise ValueError('Personnel cutoff must be timezone aware')
    if records.empty:return records.copy()
    r=records[records.game_id.eq(game_id)&records.team.eq(ALIASES.get(team,team))].copy()
    for c in ['source_at','observed_at','forecast_cutoff']:r[c]=pd.to_datetime(r[c],utc=True)
    r=r[r.verification_status.eq('verified_pregame')&r.source_at.lt(cutoff)&r.observed_at.lt(cutoff)&r.forecast_cutoff.le(cutoff)&r.source_at.lt(r.forecast_cutoff)&r.observed_at.lt(r.forecast_cutoff)&r.source_at.le(r.observed_at)&r.source_reference.fillna('').astype(str).str.strip().ne('')]
    # Keep equally recent conflicting reports for explicit conflict resolution.
    if len(r):
        latest=r.groupby('player_id').source_at.transform('max');r=r[r.source_at.eq(latest)]
    return r

def previous_starter(schedules,team,cutoff):
    s=regular_games(schedules);cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None:raise ValueError('Starter observation cutoff must be timezone aware')
    rows=[]
    for g in s[(s.home_team.eq(team)|s.away_team.eq(team))&s.kickoff.lt(cutoff)].to_dict('records'):
        at=eligible_at(g)
        if pd.isna(at) or at>=cutoff:continue
        side='home' if g['home_team']==team else 'away';pid=g.get(side+'_qb_id')
        if pd.notna(pid):rows.append({'player_id':pid,'name':g.get(side+'_qb_name'),'team':team,'game_id':g['game_id'],'kickoff':g['kickoff'],'available_at':at,'classification':'previous_observed_starter_not_prediction','quality':'retrospective_schedule_observation'})
    if not rows:return None
    result=sorted(rows,key=lambda r:(r['kickoff'],r['game_id']))[-1]
    return {**result,'kickoff':result['kickoff'].isoformat(),'available_at':result['available_at'].isoformat()}

def team_context(schedules,performance,records,game_id,team,cutoff,prior_dropbacks=80.):
    game=schedules[schedules.game_id.eq(game_id)]
    if len(game)!=1:raise ValueError('Unknown/ambiguous personnel game ID')
    g=game.iloc[0];cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None:raise ValueError('Personnel cutoff must be timezone aware')
    if ALIASES.get(team,team) not in [ALIASES.get(g.home_team,g.home_team),ALIASES.get(g.away_team,g.away_team)]:raise ValueError('Personnel team is not in the target game')
    if cutoff>g.kickoff:raise ValueError('Personnel feature cutoff cannot follow target kickoff')
    team=ALIASES.get(team,team);eligible=eligible_evidence(records,game_id,team,cutoff)
    recent=previous_starter(schedules,team,cutoff)
    previous=qb_rating(performance,recent['player_id'],cutoff,int(g.season),prior_dropbacks) if recent else None
    qb=eligible[eligible.position.eq('QB')]
    # A later ruled-out or uncertain report supersedes an older starter claim.
    candidates=qb[qb.availability.isin(['confirmed_starter','likely_starter'])]
    chosen=None;conflict=False
    if len(candidates):
        latest=candidates[candidates.source_at.eq(candidates.source_at.max())]
        conflict=latest.player_id.nunique()>1
        if not conflict:
            row=latest.sort_values(['source_at','observed_at']).iloc[-1]
            same=qb[qb.player_id.eq(row.player_id)&qb.source_at.eq(row.source_at)]
            conflict=same.availability.nunique()>1
            if not conflict:chosen=row
    expected=qb_rating(performance,chosen.player_id,cutoff,int(g.season),prior_dropbacks) if chosen is not None else None
    groups={group:{'unavailable_starters':None,'verified_unavailable_players':0,'coverage':'unknown'} for group in GROUPS}
    covered=set()
    for value in eligible.get('coverage_groups',[]):covered.update(json.loads(value))
    for group in GROUPS:
        r=eligible[eligible.position.map(POSITIONS).eq(group)]
        conflicts=set(r.groupby('player_id').availability.nunique().loc[lambda x:x>1].index)
        out=r[r.availability.eq('ruled_out')&~r.player_id.isin(conflicts)]
        groups[group]['verified_unavailable_players']=int(out.player_id.nunique())
        if conflicts:groups[group]['coverage']='conflicting_evidence'
        if group in covered and not conflicts and out.is_starter.notna().all():
            groups[group]['unavailable_starters']=int(out[out.is_starter.eq(True)].player_id.nunique())
            groups[group]['coverage']='verified_complete_report_scope'
    return {'game_id':game_id,'team':team,'cutoff':cutoff.isoformat(),'previous_observed_starter':recent,'previous_performance':previous,'expected_starter_id':chosen.player_id if chosen is not None else None,'expected_starter_status':chosen.availability if chosen is not None else ('conflicting_evidence' if conflict else 'unknown'),'expected_performance':expected,'evidence_quality':chosen.quality if chosen is not None else 'unknown','source_reference':chosen.source_reference if chosen is not None else None,'source_at':chosen.source_at.isoformat() if chosen is not None else None,'verified_evidence_records':len(eligible),'position_groups':groups,'qb_change':bool(chosen.player_id!=recent['player_id']) if chosen is not None and recent else None}

def game_features(schedules,performance,records,prior_dropbacks=80.):
    rows=[]
    # If no qualified records exist, record missingness without doing thousands of lookups.
    any_verified=not records.empty and records.verification_status.eq('verified_pregame').any()
    for g in schedules.to_dict('records'):
        row={'game_id':g['game_id'],'qb_verified':False,'player_verified':False,**{f:np.nan for f in QB_FEATURES+PLAYER_FEATURES},'qb_changes':0,'meaningful_absences':0,'verified_qb_team_count':0,'qb_designation_verified':False}
        if any_verified:
            contexts=[team_context(schedules,performance,records,g['game_id'],g[side+'_team'],g['kickoff'],prior_dropbacks) for side in ['home','away']]
            home,away=contexts
            verified=all(c['expected_starter_id'] is not None and c['expected_performance'] and c['expected_performance']['epa_per_dropback'] is not None and c['previous_performance'] and c['previous_performance']['epa_per_dropback'] is not None for c in contexts)
            row['verified_qb_team_count']=sum(int(c['expected_starter_id'] is not None) for c in contexts)
            row['qb_designation_verified']=row['verified_qb_team_count']==2
            row['qb_verified']=verified
            if verified:
                row['qb_expected_epa_difference']=home['expected_performance']['epa_per_dropback']-away['expected_performance']['epa_per_dropback']
                row['qb_change_gap_difference']=(home['expected_performance']['epa_per_dropback']-home['previous_performance']['epa_per_dropback'])-(away['expected_performance']['epa_per_dropback']-away['previous_performance']['epa_per_dropback'])
                row['qb_recent_epa_difference']=home['expected_performance']['recent_epa']-away['expected_performance']['recent_epa']
                row['qb_experience_difference']=home['expected_performance']['career_dropbacks']-away['expected_performance']['career_dropbacks']
            row['qb_changes']=sum(int(c['qb_change'] or False) for c in contexts)
            known=all(c['position_groups']['OL']['unavailable_starters'] is not None for c in contexts)
            row['player_verified']=known
            if known:row['ol_unavailable_starters_advantage']=away['position_groups']['OL']['unavailable_starters']-home['position_groups']['OL']['unavailable_starters']
            row['meaningful_absences']=sum(c['position_groups'][p]['verified_unavailable_players'] for c in contexts for p in GROUPS)
        rows.append(row)
    return pd.DataFrame(rows)

def coverage_gate(training,evaluation,kind,config):
    flag='qb_verified' if kind=='qb' else 'player_verified'
    tr=training[training[flag]];ev=evaluation[evaluation[flag]]
    ready=len(tr)>=config['personnel_min_training_games'] and len(ev)>=config['personnel_min_evaluation_games'] and len(tr)/max(1,len(training))>=config['personnel_min_team_coverage'] and len(ev)/max(1,len(evaluation))>=config['personnel_min_team_coverage'] and tr.target.nunique()==2
    return tr,ev,{'status':'eligible_matched_sample' if ready else 'skipped_insufficient_verified_coverage','kind':kind,'training_games':len(tr),'evaluation_games':len(ev),'training_coverage':len(tr)/max(1,len(training)),'evaluation_coverage':len(ev)/max(1,len(evaluation)),'training_seasons':sorted(tr.season.unique().tolist()),'evaluation_seasons':sorted(ev.season.unique().tolist()),'qb_changes':int(ev.qb_changes.sum()),'meaningful_absences':int(ev.meaningful_absences.sum()),'missing_status_fraction':float(1-len(ev)/max(1,len(evaluation))),'verified_starter_team_fraction':float(evaluation.get('verified_qb_team_count',2*evaluation.qb_verified.astype(int)).sum()/(2*max(1,len(evaluation)))),'timestamp_rule':'publication AND observation before declared and feature cutoffs; verified reference required'}

def save_prospective(schedules,performance,records,game_id,directory,cutoff=None):
    now=pd.Timestamp.now(tz='UTC');cutoff=pd.Timestamp(cutoff) if cutoff is not None else now
    game=schedules[schedules.game_id.eq(game_id)]
    if cutoff.tzinfo is None or cutoff>now or len(game)!=1:raise ValueError('Context requires an existing game and aware, non-future cutoff')
    g=game.iloc[0]
    if g.completed or g.kickoff<=now:raise ValueError('Prospective context cannot be issued for a started/completed game')
    payload={'kind':'prospective_personnel_context_not_official_forecast','game_id':game_id,'kickoff':g.kickoff.isoformat(),'created_at':now.isoformat(),'cutoff':cutoff.isoformat(),'home':team_context(schedules,performance,records,game_id,g.home_team,cutoff),'away':team_context(schedules,performance,records,game_id,g.away_team,cutoff),'evidence_ids':sorted(set(pd.concat([eligible_evidence(records,game_id,t,cutoff) for t in [g.home_team,g.away_team]]).evidence_id.tolist())) if 'evidence_id' in records else []}
    encoded=json.dumps(payload,sort_keys=True,default=str).encode();key=hashlib.sha256(encoded).hexdigest()
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);path=directory/(key+'.json')
    if not path.exists():atomic_json(payload,path)
    return path


def read_prospective(path):
    path=Path(path);payload=json.loads(path.read_text())
    expected=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
    if path.stem!=expected:raise ValueError('Prospective context checksum mismatch')
    if pd.Timestamp(payload['created_at'])>=pd.Timestamp(payload['kickoff']) or pd.Timestamp(payload['cutoff'])>pd.Timestamp(payload['created_at']):raise ValueError('Invalid prospective context issuance times')
    return payload
