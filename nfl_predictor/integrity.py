"""Immutable season generations; a single atomic pointer publishes all tables."""
import hashlib
import json
import uuid
import warnings
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

SCHEMA_VERSION = 2

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def atomic_json(value, path):
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    tmp.replace(path)

def read_season(root, season, include_pbp=True):
    pointer = Path(root)/'manifests'/f'{season}.json'
    manifest = json.loads(pointer.read_text())
    if manifest['schema_version'] != SCHEMA_VERSION:
        raise ValueError('Unsupported cache schema; refresh season')
    generation = Path(root)/'generations'/manifest['generation']
    if generation.resolve().parent != (Path(root)/'generations').resolve():
        raise ValueError('Invalid cache generation path')
    frames = {}
    for name, info in manifest['files'].items():
        path = generation/info['file']
        if path.resolve().parent != generation.resolve() or not path.is_file() or digest(path) != info['sha256']:
            raise ValueError(f'Cache corruption for {season}/{name}; use update --seasons {season} --refresh or recover-cache --seasons {season}')
        if name == 'pbp' and not include_pbp:
            continue
        frame = pd.read_parquet(path)
        if len(frame) != info['rows'] or list(frame.columns) != info['columns']:
            raise ValueError(f'Cache schema mismatch: {season}/{name}')
        frames[name] = frame
    if set(manifest['files']) != {'schedules','metrics','pbp'}:
        raise ValueError('Incomplete season manifest')
    schedules, metrics = frames['schedules'], frames['metrics']
    if schedules.game_id.isna().any() or schedules.game_id.duplicated().any() or metrics.duplicated(['game_id','team']).any():
        raise ValueError('Invalid cache identifiers; refresh season')
    if schedules.kickoff.isna().any() or schedules.kickoff.dt.tz is None:
        raise ValueError('Invalid cached kickoff timestamps')
    return frames, manifest

def publish(root, season, schedules, metrics, pbp, retrieved_at=None):
    root = Path(root)
    pointer = root/'manifests'/f'{season}.json'
    previous = json.loads(pointer.read_text()) if pointer.exists() else None
    generation = f'{season}-{uuid.uuid4().hex}'
    directory = root/'generations'/generation
    directory.mkdir(parents=True)
    files = {}
    for name, frame in [('schedules',schedules),('metrics',metrics),('pbp',pbp)]:
        path = directory/f'{name}.parquet'
        frame.to_parquet(path,index=False)
        # Read back before making any generation visible.
        check = pd.read_parquet(path)
        if not check.equals(frame.reset_index(drop=True)):
            raise ValueError(f'Parquet round-trip failed: {name}')
        files[name] = {'file':path.name,'sha256':digest(path),'rows':len(frame),'columns':list(frame.columns)}
    manifest = {'schema_version':SCHEMA_VERSION,'season':int(season),'generation':generation,'retrieved_at':retrieved_at or datetime.now(timezone.utc).isoformat(),'source':'nflverse via nflreadpy','files':files,'previous_generation':previous['generation'] if previous else None}
    atomic_json(manifest,directory/'manifest.json')
    if previous and any(previous['files'][k]['sha256'] != files[k]['sha256'] for k in files):
        warnings.warn(f'Season {season} source revision detected; previous generation retained; saved forecasts unchanged.',stacklevel=2)
    pointer.parent.mkdir(parents=True,exist_ok=True)
    atomic_json(manifest,pointer)
    return manifest

def recover(root,season):
    root = Path(root)
    current = json.loads((root/'manifests'/f'{season}.json').read_text())
    previous = current.get('previous_generation')
    if not previous:
        raise ValueError('No previous generation; refresh from source')
    old = json.loads((root/'generations'/previous/'manifest.json').read_text())
    # Verify before changing the active pointer.
    for info in old['files'].values():
        if digest(root/'generations'/previous/info['file']) != info['sha256']:
            raise ValueError('Previous generation is also corrupt; refresh from source')
    atomic_json(old,root/'manifests'/f'{season}.json')
    read_season(root,season)
    return old
