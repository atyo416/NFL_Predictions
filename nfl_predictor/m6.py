"""Independent adjusted-efficiency and coverage-gated personnel experiments."""
from pathlib import Path
from time import perf_counter
import json
import uuid
import numpy as np
import pandas as pd
from .history_features import COMMON
from .history_models import fit_history
from .history_analysis import split
from .adjusted_efficiency import ADJUSTED,MATCHUP,OVERALL,ALGORITHM
from .personnel import QB_FEATURES,PLAYER_FEATURES,coverage_gate
from .model import train
from .feature_engineering import FEATURES
from .m4 import permutation_diagnostics
from .analysis import fingerprint,paired_intervals,calibration_diagnostic,fit_calibrators,runtime_versions
from .boosting import calibrated
from .evaluation import evaluate,buckets
from .registry import register,list_candidates,load_candidate
from .integrity import atomic_json,digest
from .m3 import git_reference

RAW_EFFICIENCY=['off_epa','def_epa','off_success','def_success']
BASE=COMMON+['elo_difference']
OTHER=[f for f in BASE if f not in RAW_EFFICIENCY]
FEATURES_M6={'A_raw':BASE,'B_replacement':OTHER+ADJUSTED,'C_raw_adjusted':BASE+ADJUSTED,'D_matchups':OTHER+MATCHUP,'D2_overall':OTHER+OVERALL,
 'C_without_elo':[f for f in BASE if f!='elo_difference']+ADJUSTED,
 'C_without_adjusted_offense':BASE+[f for f in ADJUSTED if not f.startswith('adj_off')],
 'C_without_adjusted_defense':BASE+[f for f in ADJUSTED if not f.startswith('adj_def')]}

def _fit(frame,features,config):
    model=fit_history(frame,'hgb',config,None,features)
    model.update({'feature_schema':'m6-v1','activation_blocked':True,'activation_block_reason':'M6 candidates remain experimental; separate future approval and native Windows verification required.','adjustment_algorithm':ALGORITHM,'adjustment_parameters':config['adjustment'],'training_window':{'earliest_training_season':2008,'weighting':'uniform'}})
    return model

def run(frame,reference,directory,registry_directory,config,provenance=None):
    if config['training_start']!=2008 or config['weighting']!='uniform':raise ValueError('M6 preserves the selected M5 2008/uniform policy; window/weight searches are out of scope')
    key=fingerprint(frame,{'config':config,'reference':fingerprint(reference,{}),'provenance':{k:v for k,v in (provenance or {}).items() if k!='feature_computation_seconds'}})
    directory=Path(directory);final=directory/key[:16]
    if final.exists():
        checks=json.loads((final/'outputs.json').read_text())
        if any(digest(final/p)!=sha for p,sha in checks.items()):raise ValueError('M6 report checksum mismatch')
        for version in json.loads((final/'registry_versions.json').read_text()):load_candidate(registry_directory,version)
        atomic_json({'run':final.name},directory/'latest.json');return final
    stage=directory/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    records=[];importance=[];training=[];coverage=[];versions=[];personnel_predictions=[];folds=[]
    for fold in config['folds']:
        tr,ev=split(frame,2008,fold['train_end'],fold['evaluation'])
        ref_tr,ref_ev=split(reference,2018,fold['train_end'],fold['evaluation'])
        if set(ev.game_id)!=set(ref_ev.game_id) or not ev.set_index('game_id').target.sort_index().equals(ref_ev.set_index('game_id').target.sort_index()):raise ValueError('M6/reference evaluation samples or outcomes differ')
        baseline=train(ref_tr);raw=ref_ev[['game_id','season','week','target']].copy();raw['model']='logistic';raw['probability']=baseline['pipeline'].predict_proba(ref_ev[FEATURES])[:,1];records.append(raw)
        fitted={}
        for name,features in FEATURES_M6.items():
            start=perf_counter();model=_fit(tr,features,config);seconds=perf_counter()-start
            model['version']='m6-'+key[:12]+'-'+str(fold['evaluation'])+'-'+name
            p=model['pipeline'].predict_proba(ev[features])[:,1];fitted[name]=model
            o=ev[['game_id','season','week','target']].copy();o['model']=name;o['probability']=p;records.append(o)
            evaluation=evaluate(ev.target,p)
            path=register(model,registry_directory,{'run_id':key,'adjustment_version':ALGORITHM,'adjustment_parameters':config['adjustment'],'feature_cutoff':'strict per-game availability before kickoff/lower bound','training_window':model['training_window'],'report_reference':str(final),'evaluation':evaluation,'evaluation_season':fold['evaluation'],'personnel_coverage':'not used for efficiency-only model','source_verification':'retrospective nflverse performance; availability proxy/vintage limitations preserved','code_commit':git_reference()});versions.append(path.name)
            training.append({'model':name,'evaluation':fold['evaluation'],'training_games':len(tr),'runtime_seconds':seconds,**evaluation,**{'train_'+k:v for k,v in evaluate(tr.target,model['pipeline'].predict_proba(tr[features])[:,1]).items()}})
            if name in ['C_raw_adjusted','D_matchups']:
                groups={'raw_epa':['off_epa','def_epa'],'raw_success':['off_success','def_success'],'elo':['elo_difference'],'adjusted_offense':[x for x in ADJUSTED if x.startswith('adj_off')],'adjusted_defense':[x for x in ADJUSTED if x.startswith('adj_def')],'adjusted_matchups':MATCHUP}
                groups.update({'feature:'+f:[f] for f in features})
                imp=permutation_diagnostics(model,ev,groups,config['permutation_repeats'],config['seed']);imp['model']=name;imp['evaluation']=fold['evaluation'];importance.append(imp)
            if name=='C_raw_adjusted':
                cal=frame[frame.season.eq(fold['calibration'])&frame.target.notna()]
                for method,calibrator in fit_calibrators(model,cal,ev.data_cutoff.min(),config['isotonic_min_games']).items():
                    cm=calibrated(model,method,calibrator,cal);cm['version']=model['version']+'-'+method
                    p=cm['pipeline'].predict_proba(ev[features])[:,1]
                    o=ev[['game_id','season','week','target']].copy();o['model']='C_'+method;o['probability']=p;records.append(o)
                    path=register(cm,registry_directory,{'run_id':key,'adjustment_version':ALGORITHM,'adjustment_parameters':config['adjustment'],'report_reference':str(final),'training_window':model['training_window'],'evaluation':evaluate(ev.target,p),'evaluation_season':fold['evaluation'],'personnel_coverage':'not used','code_commit':git_reference()});versions.append(path.name)
        # E and F are evaluated independently. G uses fixed B replacement + both;
        # no feature winner is selected from 2024–2025 to construct a combined model.
        qb_tr,qb_ev,qb_status=coverage_gate(tr,ev,'qb',config)
        pl_tr,pl_ev,pl_status=coverage_gate(tr,ev,'player',config)
        for kind,t,e,status,base_features,extras in [('E_qb',qb_tr,qb_ev,qb_status,BASE,QB_FEATURES),('F_ol',pl_tr,pl_ev,pl_status,BASE,PLAYER_FEATURES)]:
            coverage.append({'evaluation':fold['evaluation'],'experiment':kind,**status})
            if status['status']=='eligible_matched_sample':
                for name,features in [('matched_baseline',base_features),(kind,base_features+extras)]:
                    model=_fit(t,features,config);model['version']='m6-'+key[:12]+'-'+str(fold['evaluation'])+'-'+kind+'-'+name
                    o=e[['game_id','season','week','target']].copy();o['experiment']=kind;o['model']=name;o['probability']=model['pipeline'].predict_proba(e[features])[:,1];personnel_predictions.append(o)
                    path=register(model,registry_directory,{'run_id':key,'report_reference':str(final),'experiment':kind,'player_evidence_coverage':status,'adjustment_version':ALGORITHM,'training_window':model['training_window'],'evaluation':evaluate(e.target,o.probability)});versions.append(path.name)
        both_tr=tr[tr.qb_verified&tr.player_verified];both_ev=ev[ev.qb_verified&ev.player_verified]
        _,_,both=coverage_gate(tr.assign(qb_verified=tr.qb_verified&tr.player_verified),ev.assign(qb_verified=ev.qb_verified&ev.player_verified),'qb',config)
        coverage.append({'evaluation':fold['evaluation'],'experiment':'G_adjusted_qb_ol',**both})
        if both['status']=='eligible_matched_sample' and qb_status['status']=='eligible_matched_sample' and pl_status['status']=='eligible_matched_sample':
            for name,features in [('matched_baseline',FEATURES_M6['B_replacement']),('G_adjusted_qb_ol',FEATURES_M6['B_replacement']+QB_FEATURES+PLAYER_FEATURES)]:
                model=_fit(both_tr,features,config);model['version']='m6-'+key[:12]+'-'+str(fold['evaluation'])+'-G-'+name
                o=both_ev[['game_id','season','week','target']].copy();o['experiment']='G_adjusted_qb_ol';o['model']=name;o['probability']=model['pipeline'].predict_proba(both_ev[features])[:,1];personnel_predictions.append(o)
                path=register(model,registry_directory,{'run_id':key,'report_reference':str(final),'experiment':'G_adjusted_qb_ol','player_evidence_coverage':both,'adjustment_version':ALGORITHM,'training_window':model['training_window'],'evaluation':evaluate(both_ev.target,o.probability)});versions.append(path.name)
        folds.append({**fold,'training_start':2008,'training_cutoff':(tr.kickoff.max()+pd.Timedelta(hours=8)).isoformat(),'evaluation_games':len(ev)})
    predictions=pd.concat(records,ignore_index=True);predictions.to_parquet(stage/'predictions.parquet',index=False)
    comparison=[];relative=[];calibration=[];probabilities=[];confidence=[]
    for period,f in [('all_exploratory',predictions),('examined_2024_2025',predictions[predictions.season.isin([2024,2025])])]+[(str(y),predictions[predictions.season.eq(y)]) for y in sorted(predictions.season.unique())]:
        if f.empty:continue
        kwargs={'replicates':config['bootstrap_replicates'],'seed':config['seed'],'confidence':config['confidence_level']}
        c=paired_intervals(f,**kwargs);c['period']=period;comparison.append(c)
        c=paired_intervals(f,reference='A_raw',**kwargs);c['period']=period;relative.append(c)
        for name,g in f.groupby('model'):
            calibration.append({'model':name,'period':period,**evaluate(g.target,g.probability),**calibration_diagnostic(g.target,g.probability)})
            b=buckets(g.target,g.probability);b['model']=name;b['period']=period;probabilities.append(b)
            b=buckets(g.target,g.probability,True);b['model']=name;b['period']=period;confidence.append(b)
    pd.concat(comparison).to_csv(stage/'comparison.csv',index=False);pd.concat(relative).to_csv(stage/'vs_m5.csv',index=False)
    pd.DataFrame(calibration).to_csv(stage/'calibration.csv',index=False);pd.concat(probabilities).to_csv(stage/'probability_buckets.csv',index=False);pd.concat(confidence).to_csv(stage/'confidence_buckets.csv',index=False)
    pd.concat(importance).to_csv(stage/'permutation_importance.csv',index=False);pd.DataFrame(training).to_csv(stage/'training.csv',index=False)
    pd.DataFrame(coverage).to_csv(stage/'personnel_coverage.csv',index=False)
    phases=[]
    for (name,year,phase),g in predictions.assign(phase=np.where(predictions.week.le(3),'weeks_1_3','weeks_4_plus')).groupby(['model','season','phase']):phases.append({'model':name,'season':year,'phase':phase,**evaluate(g.target,g.probability)})
    pd.DataFrame(phases).to_csv(stage/'season_phase.csv',index=False)
    if personnel_predictions:
        pp=pd.concat(personnel_predictions);pp.to_parquet(stage/'personnel_matched_predictions.parquet',index=False)
        intervals=[]
        for experiment,f in pp.groupby('experiment'):
            c=paired_intervals(f,config['bootstrap_replicates'],config['seed'],config['confidence_level'],reference='matched_baseline');c['experiment']=experiment;intervals.append(c)
        pd.concat(intervals).to_csv(stage/'personnel_matched_comparison.csv',index=False)
    frame.groupby('season')[ADJUSTED+MATCHUP+QB_FEATURES+PLAYER_FEATURES].agg(lambda x:float(x.notna().mean())).to_csv(stage/'feature_coverage.csv')
    atomic_json(versions,stage/'registry_versions.json');atomic_json([e for e in list_candidates(registry_directory) if e['version'] in versions],stage/'registry_metadata.json')
    try:
        import resource,sys
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    except ImportError:peak=None
    metadata={'run_id':key,'protocol':config,'feature_sets':FEATURES_M6,'folds':folds,'adjustment_version':ALGORITHM,'provenance':provenance or {},'module_hashes':{p.name:digest(p) for p in Path(__file__).parent.glob('*.py')},'runtime_versions':runtime_versions(),'code_commit':git_reference(),'peak_rss_bytes':peak,'efficiency_configurations':len(FEATURES_M6),'personnel':'E/F independently coverage-gated, G fixed B+QB+OL only if both independent studies eligible; no later feature selection','promotion':'All candidates experimental/activation-blocked; original champion preserved.','windows':'M5 Windows acceptance reported in supplied brief, not independently evidenced here. M6 tests executed on Linux only unless separate evidence is supplied.'}
    atomic_json(metadata,stage/'metadata.json')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots();sample=predictions[predictions.season.isin([2024,2025])]
    if sample.empty:sample=predictions
    for name,g in sample[sample.model.isin(['logistic','A_raw','B_replacement','C_raw_adjusted','D_matchups','D2_overall'])].groupby('model'):
        b=buckets(g.target,g.probability);ax.plot(b.predicted,b.observed,'o-',label=name)
    ax.plot([0,1],[0,1],'k--');ax.set(xlabel='Predicted home win probability',ylabel='Observed home win fraction',title='M6 exploratory reliability');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(stage/'reliability.png');plt.close(fig)
    from .m6_report import write_comparison
    write_comparison(stage)
    atomic_json({p.name:digest(p) for p in stage.iterdir()},stage/'outputs.json');stage.rename(final);atomic_json({'run':final.name},directory/'latest.json')
    return final
