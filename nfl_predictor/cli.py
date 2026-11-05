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
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['update','features','train','backtest','predict','analyze','recover-cache','ratings','rankings','compare-m3','report-m3','update-qb','import-qb','train-m4','compare-m4','report-m4','activate-model','rollback-model','update-history','audit-history','compare-history','report-m5','build-adjusted-efficiency','audit-personnel','compare-m6','report-m6','import-personnel','snapshot-personnel','build-ensemble-predictions','compare-m7','report-m7','forecast-ensemble','grade-ensemble','fetch-odds','import-odds','audit-odds','compare-market','issue-paper-bets','settle-paper-bets','report-m8','demo-m8','reconstruct-paper-bets','void-paper-bet','report-m81','report-m82','weekly-m83']); p.add_argument('--seasons',nargs='+',type=int); p.add_argument('--refresh',action='store_true'); p.add_argument('--cutoff'); p.add_argument('--protocol'); p.add_argument('--qb-file'); p.add_argument('--decision-file'); p.add_argument('--event-id'); p.add_argument('--start',type=int,default=1999); p.add_argument('--end',type=int,default=2017); p.add_argument('--evidence-file'); p.add_argument('--game-id'); p.add_argument('--odds-file'); p.add_argument('--rules-file'); p.add_argument('--source-kind',choices=['verified_archive','unverified','synthetic'],default='verified_archive'); p.add_argument('--dry-run',action='store_true'); p.add_argument('--model-family',choices=['official_logistic','boosting','ensemble'],default='official_logistic'); p.add_argument('--ev-threshold',type=float,choices=[0,.03,.05],default=.03); p.add_argument('--cohort',choices=['manual','24h','6h','1h'],default='manual'); p.add_argument('--reconstructed',action='store_true'); p.add_argument('--wager-id'); p.add_argument('--reason'); p.add_argument('--report-only',action='store_true'); p.add_argument('--include-odds',action='store_true'); p.add_argument('--late',action='store_true'); p.add_argument('--tolerance-minutes',type=int,default=60); a=p.parse_args()
    if a.command=='weekly-m83':
        from .prospective import weekly
        print(json.dumps(weekly(ROOT,DATA,a.dry_run,a.report_only,a.include_odds,a.tolerance_minutes,a.late),default=str,indent=2));return
    if a.command=='report-m82':
        from .spread_benchmark import generate
        print(generate(ROOT,DATA));return
    if a.command=='report-m81':
        from .historical_market import generate
        print(generate(ROOT,DATA));return
    if a.command in ['fetch-odds', 'import-odds', 'audit-odds', 'compare-market', 'issue-paper-bets', 'settle-paper-bets', 'report-m8', 'demo-m8', 'reconstruct-paper-bets', 'void-paper-bet']:
        from .betting_cli import execute
        execute(a.command,DATA,ROOT,a);return
    if a.command in ['build-ensemble-predictions','compare-m7','report-m7','forecast-ensemble','grade-ensemble']:
        from .ensemble_cli import execute
        execute(a.command,DATA,ROOT,a.protocol,a.cutoff,a.game_id);return
    if a.command in ['build-adjusted-efficiency','audit-personnel','compare-m6','report-m6','import-personnel','snapshot-personnel']:
        from .m6_cli import execute
        execute(a.command,DATA,ROOT,a.protocol,a.cutoff,a.evidence_file,a.game_id);return
    if a.command in ['update-history','audit-history','compare-history','report-m5']:
        from .history_cli import execute
        execute(a.command,DATA,ROOT,a.start,a.end,a.refresh,a.protocol); return
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
    if a.command=='activate-model':
        from .registry import activate
        if not a.decision_file: p.error('activate-model requires --decision-file')
        print(activate(ROOT/'models/registry',ROOT/'models/production.joblib',a.decision_file)); return
    if a.command=='rollback-model':
        from .registry import rollback
        if not a.event_id: p.error('rollback-model requires --event-id')
        print(rollback(ROOT/'models/registry',ROOT/'models/production.joblib',a.event_id)); return
    schedules,metrics=cached()
    if a.command in ['train-m4','compare-m4','report-m4']:
        from pathlib import Path
        from .m4_features import prepare as prepare_m4
        from .m4 import run as run_m4
        config=json.loads(Path(a.protocol or ROOT/'config/m4_protocol.json').read_text())
        if a.refresh: config['rebuild_revision']=datetime.now(timezone.utc).isoformat()
        source_metadata={p.stem:json.loads(p.read_text()) for p in (DATA/'manifests').glob('*.json')}
        frame=prepare_m4(schedules,metrics,config,DATA/'features')
        result=run_m4(frame,ROOT/'reports/m4',ROOT/'models/registry',config,source_metadata)
        print(result)
        if a.command=='report-m4':
            from .m4_report import engineering_report
            print(engineering_report(result,ROOT))
        return
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
