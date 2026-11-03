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
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['update','features','train','backtest','predict','analyze','recover-cache','ratings','rankings','compare-m3','report-m3','update-qb','import-qb']); p.add_argument('--seasons',nargs='+',type=int); p.add_argument('--refresh',action='store_true'); p.add_argument('--cutoff'); p.add_argument('--protocol'); p.add_argument('--qb-file');  a=p.parse_args()
    if a.command=='update':
        update(a.seasons or range(2018,2027),a.refresh); return
    if a.command=='recover-cache':
        from .integrity import recover
        if not a.seasons: p.error('recover-cache requires --seasons')
        for year in a.seasons: print(recover(DATA,year)['generation'])
        return
    if a.command=='update-qb':
        from .quarterbacks import update_sources
        print(update_sources(DATA,a.seasons or [2024,2026])); return
    if a.command=='import-qb':
        from .quarterbacks import import_verified
        if not a.qb_file: p.error('import-qb requires --qb-file (reviewed evidence JSON)')
        print(import_verified(a.qb_file,DATA)); return
    schedules,metrics=cached()
    if a.command in ['ratings','rankings','compare-m3','report-m3']:
        from pathlib import Path
        from .m3 import ratings_bundle,prepare,compare
        from .elo import EloParameters
        from .quarterbacks import cached_context
        config=json.loads(Path(a.protocol or ROOT/'config/m3_protocol.json').read_text())
        source_metadata={p.stem:json.loads(p.read_text()) for p in (DATA/'manifests').glob('*.json')}
        if a.command in ['ratings','rankings']:
            cutoff=pd.Timestamp(a.cutoff) if a.cutoff else pd.Timestamp.now(tz='UTC')
            result=ratings_bundle(schedules,DATA/'ratings',cutoff,EloParameters(**config['elo']),source_metadata)
            print(pd.read_parquet(result/'rankings.parquet').to_string(index=False));print(result);return
        records=cached_context(DATA/'qb_context')
        qb_pointer=DATA/'qb_context/latest.json'
        if qb_pointer.exists(): source_metadata['qb_context']=json.loads(qb_pointer.read_text())
        frame=prepare(schedules,metrics,records,config,DATA/'features')
        result=compare(frame,ROOT/'reports/m3',config,source_metadata)
        print(result)
        if a.command=='report-m3':
            from .m3_report import engineering_report
            engineering_report(result,ROOT)
        return
    if a.command=='predict':
        db=connect(DATA/'predictions.db'); attach_results(db,schedules)
        print(predict(schedules,metrics,load(ROOT/'models/production.joblib'),db,a.cutoff).to_string(index=False)); db.close(); return
    f=cached_build(schedules,metrics,DATA/'features',refresh=a.refresh)
    if a.command=='analyze':
        from .analysis import run_analysis
        source_metadata={p.stem:json.loads(p.read_text()) for p in (DATA/'manifests').glob('*.json')}
        print(run_analysis(f,ROOT/'reports/m2',json.loads(__import__('pathlib').Path(a.protocol or ROOT/'config/m2_protocol.json').read_text()),source_metadata))
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
