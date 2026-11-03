"""Controlled chronological development and aligned forward nonlinear experiments."""
from pathlib import Path
from dataclasses import replace
from time import perf_counter
import json
import uuid
import numpy as np
import pandas as pd
from .boosting import fit_boosting,calibrated,check_features
from .m4_features import FEATURE_SETS,FEATURE_GROUPS,INTERACTIONS
from .feature_engineering import FEATURES
from .model import train
from .analysis import fingerprint,paired_intervals,validate_fold,fit_calibrators,calibration_diagnostic,runtime_versions
from .evaluation import evaluate,buckets
from .integrity import digest,atomic_json
from .m3 import git_reference
from .registry import register


def chronological_parts(frame,train_start,train_end,later_year):
    if not train_start<=train_end<later_year:raise ValueError('Training must precede validation/evaluation')
    f=frame[frame.target.notna()]
    tr=f[f.season.between(train_start,train_end)];later=f[f.season.eq(later_year)]
    if tr.empty or later.empty:raise ValueError('Missing chronological period')
    if (tr.kickoff.max()+pd.Timedelta(hours=8))>=later.kickoff.min():raise ValueError('Chronological periods overlap')
    return tr,later

def select_configuration(frame,config):
    """This function never indexes target rows outside predefined development years."""
    records=[]
    for name,params in config['configurations'].items():
        for fold in config['development_folds']:
            tr,val=chronological_parts(frame,fold['train_start'],fold['train_end'],fold['validation'])
            start=perf_counter();m=fit_boosting(tr,FEATURE_SETS['elo'],params,config['cpu_threads']);seconds=perf_counter()-start
            validation_probabilities=m['pipeline'].predict_proba(val[FEATURE_SETS['elo']])[:,1]
            records.append({'configuration':name,'algorithm':'HistGradientBoostingClassifier','parameters':json.dumps(params,sort_keys=True),'features':json.dumps(FEATURE_SETS['elo']),'training_cutoff':m['training_cutoff'],'validation_season':fold['validation'],'training_games':len(tr),'runtime_seconds':seconds,**evaluate(val.target,validation_probabilities),**{'validation_'+k:v for k,v in calibration_diagnostic(val.target,validation_probabilities).items()},**{'train_'+k:v for k,v in evaluate(tr.target,m['pipeline'].predict_proba(tr[FEATURE_SETS['elo']])[:,1]).items()}})
    trials=pd.DataFrame(records)
    ranking=trials.groupby('configuration').agg(validation_brier=('brier','mean'),validation_log_loss=('log_loss','mean'),validation_accuracy=('accuracy','mean')).reset_index().sort_values(['validation_brier','validation_log_loss','configuration'])
    return str(ranking.iloc[0].configuration),trials,ranking

def permutation_diagnostics(model,frame,groups,repeats=5,seed=42):
    """One common row permutation per group preserves within-group dependence.
    It breaks across-group correlations; exploratory importance, not causal influence.
    """
    if repeats<1:raise ValueError('Permutation repeats must be positive')
    features=model['features'];x=check_features(frame,features)
    p=model['pipeline'].predict_proba(x)[:,1];base=evaluate(frame.target,p)
    rng=np.random.default_rng(seed);records=[]
    for name,columns in groups.items():
        columns=[c for c in columns if c in features]
        if not columns:continue
        for repeat in range(repeats):
            altered=x.copy();order=rng.permutation(len(x));altered[columns]=x.iloc[order][columns].to_numpy()
            metrics=evaluate(frame.target,model['pipeline'].predict_proba(altered)[:,1])
            records.append({'group':name,'features':json.dumps(columns),'repeat':repeat,'brier_increase':metrics['brier']-base['brier'],'log_loss_increase':metrics['log_loss']-base['log_loss'],'accuracy_decrease':base['accuracy']-metrics['accuracy']})
    return pd.DataFrame(records)

def run(frame,directory,registry_directory,config,source_metadata=None):
    # Selection must finish before EVERY reported calibration/evaluation fold.
    development_end=max(f['validation'] for f in config['development_folds'])
    if development_end>2021:raise ValueError('Development outcomes must remain through 2021; later periods are reporting only')
    if any(f['calibration']<development_end or f['evaluation']<=development_end for f in config['folds']):
        raise ValueError('Development outcomes overlap or follow a reported forward period')
    key=fingerprint(frame,{'protocol':config,'sources':source_metadata or {}})
    directory=Path(directory);final=directory/key[:16]
    if final.exists():
        checks=json.loads((final/'outputs.json').read_text())
        if any(digest(final/name)!=sha for name,sha in checks.items()):raise ValueError('M4 report artifact checksum mismatch')
        entries=json.loads((final/'registry_versions.json').read_text())
        from .registry import load_candidate
        try:
            for version in entries:load_candidate(registry_directory,version)
        except (FileNotFoundError,ValueError) as exc:
            raise ValueError('Cached M4 candidate artifacts are missing/corrupt; run compare-m4 --refresh to create a fresh audited run') from exc
        atomic_json({'run':final.name},directory/'latest.json');return final
    stage=directory/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    selected,trials,ranking=select_configuration(frame,config)
    trials.to_csv(stage/'development_trials.csv',index=False);ranking.to_csv(stage/'development_ranking.csv',index=False)
    records=[];diagnostics=[];importance=[];coefficients=[];registry_versions=[];fold_metadata=[]
    for fold in config['folds']:
        tr,cal,ev=validate_fold(frame,fold)
        chosen=config['configurations'][selected]
        candidate_specs={('hgb_config_'+name):('elo',params) for name,params in config['configurations'].items()}
        candidate_specs.update({'hgb_selected':('elo',chosen),'hgb_m2_only':('m2',chosen),'hgb_margin_elo':('margin',chosen),'hgb_relative_strength':('elo_relative',chosen),'hgb_rest':('rest',chosen),'hgb_interactions':('interactions',chosen)})
        logistic=train(tr);logistic_elo=train(tr,FEATURE_SETS['elo'])
        probabilities={'logistic':logistic['pipeline'].predict_proba(ev[FEATURES])[:,1],'m2_elo':logistic_elo['pipeline'].predict_proba(ev[FEATURE_SETS['elo']])[:,1],'elo_only':ev.elo_probability.to_numpy(),'elo_margin':ev.elo_margin_probability.to_numpy(),'pregame_win_percentage':np.clip(.5+ev.win.fillna(0).to_numpy()/2,.05,.95),'historical_home_rate':np.full(len(ev),float(tr.target.mean()))}
        for feature,coefficient in zip(FEATURES,logistic['pipeline'][-1].coef_[0]):coefficients.append({'evaluation':fold['evaluation'],'feature':feature,'standardized_coefficient':coefficient})
        for name,(feature_set,params) in candidate_specs.items():
            features=FEATURE_SETS[feature_set];start=perf_counter();model=fit_boosting(tr,features,params,config['cpu_threads']);seconds=perf_counter()-start
            model['version']='m4-'+key[:12]+'-'+str(fold['evaluation'])+'-'+name
            model['feature_config']={k:config[k] for k in ['elo','short_rest_days','extended_rest_days']}
            probabilities[name]=model['pipeline'].predict_proba(ev[features])[:,1]
            path=register(model,registry_directory,{'report_reference':str(final),'run_id':key,'feature_set':feature_set,'evaluation_season':fold['evaluation'],'code_commit':git_reference(),'status':'experimental; not a prospective issued forecast'})
            registry_versions.append(path.name)
            for label,f in [('training',tr),('calibration_diagnostic',cal),('forward_evaluation',ev)]:
                diagnostics.append({'model':name,'feature_set':feature_set,'evaluation':fold['evaluation'],'period':label,'runtime_seconds':seconds,**evaluate(f.target,model['pipeline'].predict_proba(f[features])[:,1])})
            if name in ['hgb_selected','hgb_interactions']:
                groups={**{'feature:'+f:[f] for f in features},**{'group:'+g:cols for g,cols in FEATURE_GROUPS.items()}}
                imp=permutation_diagnostics(model,ev,groups,config['permutation_repeats'],config['seed']);imp['model']=name;imp['evaluation']=fold['evaluation'];importance.append(imp)
            if name=='hgb_selected':
                methods=fit_calibrators(model,cal,ev.kickoff.min(),config['isotonic_min_games'])
                for method,calibrator in methods.items():
                    calibrated_model=calibrated(model,method,calibrator,cal)
                    calibrated_model['version']=model['version']+'-'+method
                    probabilities['hgb_'+method]=calibrated_model['pipeline'].predict_proba(ev[features])[:,1]
                    path=register(calibrated_model,registry_directory,{'report_reference':str(final),'run_id':key,'feature_set':feature_set,'evaluation_season':fold['evaluation'],'code_commit':git_reference(),'status':'experimental; not a prospective issued forecast'})
                    registry_versions.append(path.name)
        for name,p in probabilities.items():
            out=ev[['game_id','season','week','kickoff','home_team','away_team','target']].copy();out['model']=name;out['probability']=p;out['correct']=out.target.eq(out.probability.ge(.5));out['training_through']=fold['train_end'];records.append(out)
        fold_metadata.append({**fold,'training_cutoff':(tr.kickoff.max()+pd.Timedelta(hours=8)).isoformat(),'calibration_cutoff':(cal.kickoff.max()+pd.Timedelta(hours=8)).isoformat(),'evaluation_start':ev.kickoff.min().isoformat(),'evaluation_end':ev.kickoff.max().isoformat(),'training_games':len(tr),'calibration_games':len(cal),'evaluation_games':len(ev)})
    predictions=pd.concat(records,ignore_index=True)
    if predictions.duplicated(['game_id','model']).any():raise ValueError('Duplicate forward evaluation games')
    predictions.to_parquet(stage/'predictions.parquet',index=False)
    comparisons=[];calibration=[];bands=[];confidence=[];slices=[]
    for period,f in [('all_exploratory',predictions),('examined_2024_2025',predictions[predictions.season.isin([2024,2025])])]+[(str(y),predictions[predictions.season.eq(y)]) for y in sorted(predictions.season.unique())]:
        if f.empty:continue
        c=paired_intervals(f,config['bootstrap_replicates'],config['seed'],config['confidence_level']);c['period']=period;comparisons.append(c)
        for name,g in f.groupby('model'):
            calibration.append({'period':period,'model':name,**evaluate(g.target,g.probability),**calibration_diagnostic(g.target,g.probability)})
            b=buckets(g.target,g.probability);b['period']=period;b['model']=name;bands.append(b)
            b=buckets(g.target,g.probability,True);b['period']=period;b['model']=name;confidence.append(b)
    for (name,season,phase),g in predictions.assign(phase=np.where(predictions.week.le(4),'weeks_1_4','weeks_5_plus')).groupby(['model','season','phase']):
        slices.append({'model':name,'season':season,'phase':phase,**evaluate(g.target,g.probability)})
    pd.concat(comparisons).to_csv(stage/'comparison.csv',index=False)
    pd.DataFrame(calibration).to_csv(stage/'calibration.csv',index=False)
    pd.concat(bands).to_csv(stage/'probability_buckets.csv',index=False)
    pd.concat(confidence).to_csv(stage/'confidence_buckets.csv',index=False)
    pd.DataFrame(slices).to_csv(stage/'season_phase.csv',index=False)
    pd.DataFrame(diagnostics).to_csv(stage/'overfitting.csv',index=False)
    pd.concat(importance).to_csv(stage/'permutation_importance.csv',index=False)
    pd.DataFrame(coefficients).to_csv(stage/'logistic_coefficients.csv',index=False)
    frame[frame.season.le(2025)][sorted({f for fs in FEATURE_SETS.values() for f in fs})].isna().mean().rename('missing_fraction').to_csv(stage/'feature_missingness.csv')
    atomic_json(registry_versions,stage/'registry_versions.json')
    from .registry import list_candidates
    atomic_json([entry for entry in list_candidates(registry_directory) if entry['version'] in registry_versions],stage/'registry_metadata.json')
    metadata={'run_id':key,'protocol':config,'selected_configuration':selected,'selection_scope':'Only development validation outcomes through '+str(development_end),'candidate_feature_sets':FEATURE_SETS,'folds':fold_metadata,'source_manifests':source_metadata or {},'module_hashes':{p.name:digest(p) for p in Path(__file__).parent.glob('*.py')},'runtime_versions':runtime_versions(),'code_commit':git_reference(),'early_stopping':False,'missing_values':'Native partial-NaN routing. All-empty training columns are excluded (recorded per artifact); all-empty inputs use an intercept-only constant. No tree scaling or source-data imputation.','calibration':'M2 chronologically separate base/calibration/evaluation fitting; sigmoid on logit probabilities; isotonic conditional on coverage','qb':'Excluded from main comparison: no sufficient verified historical pregame coverage; M3 layer preserved','xgboost':config['xgboost'],'promotion':'Retain M2 champion; all candidates experimental.','interpretation':'Permutation importance is exploratory and noncausal; correlated features and multiple comparisons limit inference.','intervals':'M2 paired season-week percentile bootstrap; repeated teams/interweek dependence and limited seasons remain limitations','reproducibility':'Predictions/selection deterministic at fixed inputs/runtime; measured wall-clock runtimes vary.'}
    atomic_json(metadata,stage/'metadata.json')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    sample=predictions[predictions.season.isin([2024,2025])]
    if sample.empty:sample=predictions
    fig,ax=plt.subplots()
    for name,g in sample[sample.model.isin(['logistic','hgb_selected','hgb_sigmoid','hgb_isotonic','hgb_interactions','pregame_win_percentage'])].groupby('model'):
        b=buckets(g.target,g.probability);ax.plot(b.predicted,b.observed,'o-',label=name)
    ax.plot([0,1],[0,1],'k--');ax.set(xlabel='Predicted home win probability',ylabel='Observed home win frequency',title='M4 exploratory reliability');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(stage/'reliability.png');plt.close(fig)
    from .m4_report import write_run_report
    write_run_report(stage)
    atomic_json({p.name:digest(p) for p in stage.iterdir()},stage/'outputs.json');stage.rename(final);atomic_json({'run':final.name},directory/'latest.json')
    return final
