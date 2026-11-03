"""Checksum-bound ensemble references; no missing or incompatible base fallback."""
from pathlib import Path
import json
from .ensemble import BASES,PROBABILITIES
from .integrity import digest


def verify_references(model,directory):
    from .registry import load_candidate,VERSION
    if model.get('features')!=PROBABILITIES or set(model.get('base_refs',{}))!=set(BASES):raise ValueError('Incompatible ensemble feature/base contract')
    loaded={}
    for name,reference in model['base_refs'].items():
        version=reference['version']
        if not VERSION.fullmatch(version):raise ValueError('Unsafe base version')
        path=Path(directory)/'candidates'/version
        if not (path/'model.joblib').exists():raise ValueError(f'Missing ensemble base model {name}: {version}; rebuild M7 base predictions')
        metadata=json.loads((path/'metadata.json').read_text())
        if metadata.get('feature_schema')!=reference['feature_schema'] or metadata.get('features')!=reference['features'] or reference['feature_schema']!='m7-'+name+'-v1':
            raise ValueError('Incompatible ensemble base feature version')
        if digest(path/'model.joblib')!=reference['artifact_sha256'] or metadata['artifact_sha256']!=reference['artifact_sha256']:raise ValueError('Ensemble base checksum mismatch')
        base,_=load_candidate(directory,version)
        if base.get('base_kind')!=name or base.get('feature_schema')!=reference['feature_schema'] or base['features']!=reference['features'] or base['training_cutoff']!=reference['training_cutoff']:
            raise ValueError('Loaded ensemble base contract differs from reviewed reference')
        loaded[name]=base
    return loaded


def load_ensemble(directory,version):
    from .registry import load_candidate
    model,metadata=load_candidate(directory,version)
    if model.get('feature_schema')!='m7-ensemble-v1' or not model.get('activation_blocked'):raise ValueError('Not an experimental M7 ensemble artifact')
    return model,verify_references(model,directory),metadata
