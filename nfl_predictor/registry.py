"""Additive file registry. Explicit operator decisions, backups and rollback.
No registry operation alters prediction records or migrates SQLite.
"""
from pathlib import Path
from datetime import datetime,timezone
import json
import re
import shutil
import uuid
import joblib
from .integrity import atomic_json,digest

VERSION=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z')

def register(model,directory,metadata):
    directory=Path(directory);version=model['version']
    if not VERSION.fullmatch(version):raise ValueError('Unsafe model version')
    final=directory/'candidates'/version
    descriptor={**metadata,'version':version,'designation':'experimental','algorithm':model.get('algorithm','legacy_sklearn_pipeline'),'features':model['features'],'feature_schema':model.get('feature_schema','legacy'),'feature_config':model.get('feature_config'),'excluded_all_missing_features':model.get('excluded_all_missing_features',[]),'hyperparameters':model.get('hyperparameters',{}),'training_cutoff':model['training_cutoff'],'calibration':model.get('calibration'),'dataset_fingerprint':model.get('dataset_fingerprint')}
    if final.exists():
        existing=json.loads((final/'metadata.json').read_text())
        if {k:v for k,v in existing.items() if k!='artifact_sha256'}!=descriptor or digest(final/'model.joblib')!=existing['artifact_sha256']:
            raise ValueError('Immutable registry entry differs or is corrupt')
        return final
    stage=directory/'candidates'/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    joblib.dump(model,stage/'model.joblib')
    descriptor['artifact_sha256']=digest(stage/'model.joblib')
    atomic_json(descriptor,stage/'metadata.json');stage.rename(final)
    return final

def load_candidate(directory,version):
    if not VERSION.fullmatch(version):raise ValueError('Unsafe candidate version')
    path=Path(directory)/'candidates'/version;metadata=json.loads((path/'metadata.json').read_text())
    if digest(path/'model.joblib')!=metadata['artifact_sha256']:raise ValueError('Candidate checksum mismatch')
    # Trusted local artifacts only. Hashes detect changes, not malicious joblib content.
    model=joblib.load(path/'model.joblib')
    if model.get('feature_schema')=='m7-ensemble-v1':
        from .ensemble_registry import verify_references
        verify_references(model,directory)
    return model,metadata

def list_candidates(directory):
    directory=Path(directory)
    active=json.loads((directory/'active.json').read_text()) if (directory/'active.json').exists() else {}
    version=active.get('decision',{}).get('candidate_version') if active.get('status')=='activated' else None
    entries=[json.loads(p.read_text()) for p in sorted((directory/'candidates').glob('*/metadata.json')) if not p.parent.name.startswith('.')]
    return [{**entry,'effective_designation':'champion' if entry['version']==version else 'experimental'} for entry in entries]


def activate(directory,production,decision_file):
    directory=Path(directory);production=Path(production)
    decision=json.loads(Path(decision_file).read_text())
    required=['candidate_version','reviewer','rationale','evidence_report','artifact_sha256']
    if any(not isinstance(decision.get(k),str) or not decision[k].strip() for k in required) or decision.get('decision')!='approve' or decision.get('windows_verified') is not True:
        raise ValueError('Activation requires an approved documented decision, named reviewer, rationale, evidence and Windows acceptance')
    model,metadata=load_candidate(directory,decision['candidate_version'])
    if decision['artifact_sha256']!=metadata['artifact_sha256']:raise ValueError('Decision does not match reviewed artifact')
    if model.get('activation_blocked'):raise ValueError(model.get('activation_block_reason','M5 candidates remain experimental: activation is prohibited during at-risk development'))
    if model.get('feature_schema')=='m4-v1':
        from .m4_features import FEATURE_SETS
        from .elo import EloParameters
        config=model.get('feature_config') or {}
        if not {'elo','short_rest_days','extended_rest_days'}<=set(config):raise ValueError('M4 activation requires a complete live feature configuration')
        EloParameters(**config['elo'])
        if config['short_rest_days']<=0 or config['extended_rest_days']<=config['short_rest_days']:raise ValueError('Invalid live rest configuration')
        if set(model['features'])-{f for features in FEATURE_SETS.values() for f in features}:raise ValueError('Candidate features have no supported live adapter')
    evidence=Path(decision['evidence_report'])
    if not evidence.is_absolute(): evidence=Path(decision_file).resolve().parent/evidence
    if not evidence.is_file() or decision.get('evidence_sha256')!=digest(evidence):raise ValueError('Decision needs a matching existing evidence report and checksum')
    if not production.is_file():raise ValueError('Existing champion must be present for rollback preservation')
    previous_sha=digest(production)
    if previous_sha==metadata['artifact_sha256']:raise ValueError('Candidate is already the active artifact')
    backups=directory/'champions';backups.mkdir(parents=True,exist_ok=True)
    backup=backups/f'{previous_sha}.joblib'
    if backup.exists() and digest(backup)!=previous_sha:raise ValueError('Champion backup is corrupt')
    if not backup.exists():
        tmp=backups/(uuid.uuid4().hex+'.tmp');shutil.copyfile(production,tmp)
        if digest(tmp)!=previous_sha:raise ValueError('Champion backup verification failed')
        tmp.replace(backup)
    events=directory/'events';events.mkdir(parents=True,exist_ok=True)
    event_id=uuid.uuid4().hex
    event={'event_id':event_id,'created_at':datetime.now(timezone.utc).isoformat(),'decision':decision,'previous_sha256':previous_sha,'candidate_sha256':metadata['artifact_sha256'],'status':'prepared'}
    atomic_json(event,events/f'{event_id}.json')
    tmp=production.with_name(production.name+'.'+event_id+'.tmp');shutil.copyfile(directory/'candidates'/model['version']/'model.joblib',tmp)
    if digest(tmp)!=metadata['artifact_sha256']:raise ValueError('Candidate copy failed verification')
    tmp.replace(production)
    event['status']='activated';atomic_json(event,events/f'{event_id}.json')
    atomic_json(event,directory/'active.json')
    return event

def rollback(directory,production,event_id):
    if not re.fullmatch(r'[a-f0-9]{32}',event_id):raise ValueError('Invalid activation event')
    directory=Path(directory);production=Path(production)
    event=json.loads((directory/'events'/f'{event_id}.json').read_text())
    if event['status'] not in ['activated','prepared'] or digest(production)!=event['candidate_sha256']:
        raise ValueError('Rollback would replace an unrelated or already-restored champion')
    backup=directory/'champions'/f"{event['previous_sha256']}.joblib"
    if digest(backup)!=event['previous_sha256']:raise ValueError('Rollback backup failed verification')
    tmp=production.with_name(production.name+'.rollback.tmp');shutil.copyfile(backup,tmp)
    if digest(tmp)!=event['previous_sha256']:raise ValueError('Rollback copy failed verification')
    tmp.replace(production)
    event={**event,'status':'rolled_back','rolled_back_at':datetime.now(timezone.utc).isoformat()}
    atomic_json(event,directory/'events'/f'{event_id}.json');atomic_json(event,directory/'active.json')
    return event
