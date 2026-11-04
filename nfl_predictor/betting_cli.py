"""Explicit read-only odds fetch, offline imports, reports and paper simulations."""
from pathlib import Path
import json
from .data_loader import cached
from .odds_store import connect,rows
from .odds_provider import OddsAPIv4,ingest
from .market_forecasts import ForecastRepository,persist_forecasts,historical_inference
from .market_comparison import audit_matches
from .paper_betting import issue,settle,void_wager,performance,ledger_view
from .betting_report import build,engineering_report

COMMANDS=['fetch-odds','import-odds','audit-odds','compare-market','issue-paper-bets','settle-paper-bets','report-m8','demo-m8','reconstruct-paper-bets','void-paper-bet']


def execute(command,data,root,args):
    root=Path(root);data=Path(data);config=json.loads(Path(args.protocol or root/'config/m8_protocol.json').read_text())
    if command=='demo-m8':
        from .betting_demo import run_demo
        print(json.dumps(run_demo(root,root/'reports/m8_demo'),indent=2));return
    db=connect(data/'m8/lab.db')
    try:
        rules=json.loads(Path(args.rules_file).read_text()) if args.rules_file else None
        if command=='fetch-odds':print(json.dumps(OddsAPIv4().fetch(db,config,rules),indent=2));return
        if command=='import-odds':
            if not args.odds_file:raise ValueError('import-odds requires --odds-file with timestamped CSV/JSON evidence')
            path=Path(args.odds_file);result=ingest(db,path.read_bytes(),'csv' if path.suffix.lower()=='.csv' else 'json',args.source_kind,rules)
            print(json.dumps(result,indent=2));return
        if command=='void-paper-bet':
            if not args.wager_id or not args.reason:raise ValueError('void-paper-bet requires --wager-id and a traceable --reason')
            print(json.dumps(void_wager(db,args.wager_id,args.reason),indent=2));return
        if args.reconstructed:
            from .history_data import load_history
            schedules,metrics=load_history(data)
        else:schedules,metrics=cached(data=data)
        if command=='audit-odds':
            audits=audit_matches(db,schedules,config)
            print(json.dumps({'normalized_pairs':len(rows(db,'quotes')),'raw_responses':db.execute('SELECT count(*) FROM raw').fetchone()[0],'matches':audits,'receipts':rows(db,'receipts')},indent=2));return
        repository=ForecastRepository(root,data);forecasts=repository.read();persist_forecasts(db,forecasts)
        if command=='issue-paper-bets':
            print(json.dumps(issue(db,schedules,forecasts,config,args.model_family,args.ev_threshold,args.cohort,args.dry_run,args.cutoff),indent=2));return
        if command=='settle-paper-bets':
            events=settle(db,schedules,config);print(json.dumps({'new_events':len(events),'summary':performance(ledger_view(db))},indent=2));return
        if command=='reconstruct-paper-bets':
            if not args.reconstructed:raise ValueError('Historical simulations require explicit --reconstructed classification')
            from .market_benchmark import benchmark,reconstruct_paper
            _,opportunities,exclusions=benchmark(db,schedules,forecasts,config,'reconstructed',lambda gid,at:historical_inference(root,schedules,metrics,gid,at,db))
            wagers=reconstruct_paper(db,opportunities,schedules,config);settle(db,schedules,config)
            print(json.dumps({'classification':'historical_reconstructed_only','new_simulated_wagers':len(wagers),'exclusions':exclusions},indent=2));return
        mode='reconstructed' if args.reconstructed else 'prospective'
        infer=(lambda gid,at:historical_inference(root,schedules,metrics,gid,at,db)) if args.reconstructed else None
        run=build(db,schedules,forecasts,config,root/'reports/m8',args.cutoff,mode,infer,repository.issues);print(run)
        if command=='report-m8':print(engineering_report(run,root))
    finally:db.close()
