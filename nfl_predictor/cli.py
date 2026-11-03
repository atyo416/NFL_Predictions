import argparse
import json
import pandas as pd
from datetime import datetime,timezone
from .data_loader import update,cached,DATA,ROOT,atomic_parquet
from .feature_engineering import build,cached_build
from .model import train,save,load
from .backtest import run
from .database import connect,attach_results
from .predictions import predict

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['update','features','train','backtest','predict','analyze','recover-cache']); p.add_argument('--seasons',nargs='+',type=int); p.add_argument('--refresh',action='store_true'); p.add_argument('--cutoff'); p.add_argument('--protocol',default=str(ROOT/'config/m2_protocol.json'));  a=p.parse_args()
    if a.command=='update':
        update(a.seasons or range(2018,2027),a.refresh); return
    if a.command=='recover-cache':
        from .integrity import recover
        if not a.seasons: p.error('recover-cache requires --seasons')
        for year in a.seasons: print(recover(DATA,year)['generation'])
        return
    schedules,metrics=cached()
    if a.command=='predict':
        db=connect(DATA/'predictions.db'); attach_results(db,schedules)
        print(predict(schedules,metrics,load(ROOT/'models/production.joblib'),db,a.cutoff).to_string(index=False)); db.close(); return
    f=cached_build(schedules,metrics,DATA/'features',refresh=a.refresh)
    if a.command=='analyze':
        from .analysis import run_analysis
        source_metadata={p.stem:json.loads(p.read_text()) for p in (DATA/'manifests').glob('*.json')}
        print(run_analysis(f,ROOT/'reports/m2',json.loads(__import__('pathlib').Path(a.protocol).read_text()),source_metadata))
        return
    if a.command=='features':
        atomic_parquet(f,DATA/'processed/features.parquet')
    elif a.command=='backtest':
        print(json.dumps(run(f,ROOT/'reports'),indent=2))
    else:
        now=datetime.now(timezone.utc)
        f=f[f.kickoff.lt(now-pd.Timedelta(hours=8)) & f.target.notna()]
        m=train(f); save(m,ROOT/'models/production.joblib')
        db=connect(DATA/'predictions.db')
        with db: db.execute('INSERT INTO models VALUES(?,?)',(m['version'],json.dumps({k:v for k,v in m.items() if k!='pipeline'})))
        db.close(); print(m['version'])

if __name__=='__main__':
    import pandas as pd
    main()
