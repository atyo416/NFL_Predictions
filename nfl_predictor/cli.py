import argparse
import json
import pandas as pd
from datetime import datetime,timezone
from .data_loader import update,cached,DATA,ROOT,atomic_parquet
from .feature_engineering import build
from .model import train,save,load
from .backtest import run
from .database import connect,attach_results
from .predictions import predict

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['update','features','train','backtest','predict']); p.add_argument('--seasons',nargs='+',type=int); p.add_argument('--refresh',action='store_true'); p.add_argument('--cutoff'); a=p.parse_args()
    if a.command=='update':
        update(a.seasons or range(2018,2027),a.refresh); return
    schedules,metrics=cached()
    if a.command=='predict':
        db=connect(DATA/'predictions.db'); attach_results(db,schedules)
        print(predict(schedules,metrics,load(ROOT/'models/production.joblib'),db,a.cutoff).to_string(index=False)); db.close(); return
    f=build(schedules,metrics)
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
