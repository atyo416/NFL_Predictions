"""Non-destructive native/platform acceptance evidence, not an automatic certificate."""
from pathlib import Path
import hashlib
import json
import platform
import shutil
import sys
import tempfile
from datetime import datetime,timezone
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from nfl_predictor.data_loader import cached
from nfl_predictor.model import load
from nfl_predictor.database import connect
from nfl_predictor.predictions import predict
from nfl_predictor.integrity import digest


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot-only',action='store_true')
    parser.add_argument('--baseline')
    args=parser.parse_args()
    paths=[p for base in ['models','data/ratings'] for p in (ROOT/base).rglob('*') if p.is_file()]+[ROOT/'data/predictions.db']
    hashes={str(p):digest(p) for p in paths if p.is_file()}
    if args.snapshot_only:
        if not args.baseline:parser.error('--snapshot-only requires --baseline')
        path=Path(args.baseline);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():raise ValueError('Preservation baseline already exists; choose a unique run name')
        path.write_text(json.dumps(hashes,indent=2));print(path);return
    if args.baseline:hashes={**hashes,**json.loads(Path(args.baseline).read_text())}
    evidence={'platform':platform.platform(),'python':sys.version,'native_windows':sys.platform=='win32','checked_at':datetime.now(timezone.utc).isoformat(),'checks':{}}
    model_path=ROOT/'models/production.joblib'
    if model_path.exists():
        model=load(model_path);evidence['checks']['champion_load']='passed';evidence['champion_version']=model['version']
        schedules,metrics=cached()
        with tempfile.TemporaryDirectory() as directory:
            copy=Path(directory)/'acceptance.db'
            if (ROOT/'data/predictions.db').exists():shutil.copyfile(ROOT/'data/predictions.db',copy)
            db=connect(copy);forecasts=predict(schedules,metrics,model,db);db.close()
            evidence['checks']['upcoming_predictions']='passed' if len(forecasts) else 'unrun: no eligible upcoming 2026 games'
            evidence['upcoming_count']=len(forecasts)
    else:evidence['checks']['champion_load']='unrun: restore existing local champion artifact first'
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(ROOT/'app.py'),default_timeout=180).run()
    for page in ['Upcoming Games','Team Comparison','Model Performance','Model Analysis','Team Power Rankings']:
        if not app.sidebar.radio:evidence['checks'][page]='unrun: source cache missing';continue
        app.sidebar.radio[0].set_value(page).run()
        if app.exception:raise RuntimeError(f'{page}: {list(app.exception)}')
        evidence['checks'][page]='passed'
    from nfl_predictor.registry import list_candidates,load_candidate
    entries=list_candidates(ROOT/'models/registry')
    for entry in entries:load_candidate(ROOT/'models/registry',entry['version'])
    evidence['checks']['registry_load']='passed' if entries else 'unrun: no registered candidates'
    evidence['registered_candidates_loaded']=len(entries)
    changed=[p for p,sha in hashes.items() if digest(p)!=sha]
    if changed:raise RuntimeError(f'Existing local artifacts changed: {changed}')
    evidence['checks']['preservation']='passed';evidence['preserved_artifacts']=len(hashes)
    evidence['status']='Review required; no automatic Windows certification. Native Windows, full data/model steps, manual UI startup and RAM behavior must all be verified.'
    out=ROOT/'reports/local_acceptance';out.mkdir(parents=True,exist_ok=True)
    path=out/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json');path.write_text(json.dumps(evidence,indent=2));print(path)

if __name__=='__main__':main()
