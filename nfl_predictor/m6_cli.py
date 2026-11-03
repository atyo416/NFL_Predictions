"""M6 orchestration; sources stay separate from verified evidence and forecast history."""
from pathlib import Path
from dataclasses import replace
from time import perf_counter
import json
import pandas as pd
from .history_data import load_history
from .history_features import reconstruct,attach_elo
from .adjusted_efficiency import build_adjusted,AdjustmentParameters
from .player_performance import build_performance
from .personnel import load_evidence,game_features
from .integrity import atomic_json


def execute(command,data,root,protocol=None,cutoff=None,evidence_file=None,game_id=None):
    data=Path(data);root=Path(root)
    config=json.loads(Path(protocol or root/'config/m6_protocol.json').read_text())
    if command=='import-personnel':
        from .personnel import import_evidence
        if not evidence_file:raise ValueError('import-personnel requires --evidence-file')
        print(import_evidence(evidence_file,data/'m6/personnel'));return
    schedules,metrics=load_history(data)
    p=AdjustmentParameters(**config['adjustment'])
    start=perf_counter()
    if command=='build-adjusted-efficiency':
        adjusted=build_adjusted(schedules,metrics,p,data/'m6/adjusted',cutoff=cutoff)
        from .data_loader import atomic_parquet
        atomic_parquet(adjusted,data/'m6/adjusted_export.parquet')
        print(f'Built {len(adjusted)} adjusted matchup rows in {perf_counter()-start:.2f}s');return
    records=load_evidence(data/'m6/personnel')
    performance=build_performance(data,data/'m6/qb_performance',schedules)
    audit={'performance_audit':json.loads((data/'m6/qb_performance/audit.json').read_text()),'evidence_records':len(records),'verified_claims':int(records.verification_status.eq('verified_pregame').sum()) if len(records) else 0,'source_timestamp_classification':records.verification_status.value_counts().to_dict() if len(records) else {},'note':'M3 historical depth/roster/injury snapshots are not independently verified pregame evidence. No automatic upgrade or fabricated starter identity.'}
    output=root/'reports/personnel_audit';output.mkdir(parents=True,exist_ok=True);atomic_json(audit,output/'coverage.json')
    if command=='audit-personnel':print(json.dumps(audit,indent=2));return
    if command=='snapshot-personnel':
        from .personnel import save_prospective
        if not game_id:raise ValueError('snapshot-personnel requires --game-id')
        print(save_prospective(schedules,performance,records,game_id,data/'m6/prospective_contexts',cutoff));return
    frame,_=reconstruct(schedules,metrics,data/'history_features');frame=attach_elo(frame,schedules,config['elo'])
    adjusted=build_adjusted(schedules,metrics,p,data/'m6/adjusted')
    frame=frame.merge(adjusted,on='game_id',validate='one_to_one').merge(game_features(schedules,performance,records,config['qb_prior_dropbacks']),on='game_id',validate='one_to_one')
    from .data_loader import cached
    from .feature_engineering import cached_build
    reference_s,reference_m=cached(data=data);reference=cached_build(reference_s,reference_m,data/'features')
    from .m6 import run
    provenance={'source_manifests':{f.stem:json.loads(f.read_text()) for f in (data/'manifests').glob('*.json')},'personnel_audit':audit,'personnel_ledger':json.loads((data/'m6/personnel/latest.json').read_text()) if (data/'m6/personnel/latest.json').exists() else None,'feature_computation_seconds':perf_counter()-start}
    result=run(frame,reference,root/'reports/m6',root/'models/registry',config,provenance)
    # Sensitivity is fixed and evaluated only on historical development periods.
    # It is an external diagnostic, never a selection input to the primary run.
    sensitivity=root/'reports/m6_sensitivity'/result.name;sensitivity.mkdir(parents=True,exist_ok=True)
    from .integrity import digest
    artifact=sensitivity/'development_prior_sensitivity.csv'
    sidecar=sensitivity/'metadata.json'
    if artifact.exists():
        if not sidecar.exists() or digest(artifact)!=json.loads(sidecar.read_text())['sha256']:raise ValueError('Prior sensitivity artifact checksum mismatch')
    else:
        from .history_models import fit_history
        from .history_analysis import split
        from .evaluation import evaluate
        from .m6 import FEATURES_M6
        rows=[]
        dev_ids=schedules.loc[schedules.season.isin([f['validation'] for f in config['development_folds']]+list(range(2008,2021))),'game_id']
        for prior in [p.prior_games]+config['prior_sensitivity']:
            variant=build_adjusted(schedules,metrics,replace(p,prior_games=prior),data/'m6/adjusted',game_ids=dev_ids)
            columns=[c for c in variant if c not in ['game_id']]
            v=frame.drop(columns=columns).merge(variant,on='game_id',validate='one_to_one')
            for fold in config['development_folds']:
                tr,ev=split(v,2008,fold['train_end'],fold['validation'])
                model=fit_history(tr,'hgb',config,None,FEATURES_M6['B_replacement'])
                rows.append({'prior_games':prior,'training_end':fold['train_end'],'validation':fold['validation'],**evaluate(ev.target,model['pipeline'].predict_proba(ev[model['features']])[:,1])})
        pd.DataFrame(rows).to_csv(sensitivity/'development_prior_sensitivity.csv',index=False)
        atomic_json({'run':result.name,'scope':'2019–2021 development only; no default selection','sha256':digest(artifact)},sidecar)
    print(result)
    if command=='report-m6':
        from .m6_report import engineering_report
        print(engineering_report(result,root))
