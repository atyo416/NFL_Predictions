"""Staged window/decay comparisons. No 2022–2025 outcome chooses a policy."""
from pathlib import Path
from dataclasses import replace
from time import perf_counter
import json
import uuid
import numpy as np
import pandas as pd
from .history_models import fit_history
from .history_features import COMMON
from .analysis import fingerprint,paired_intervals,calibration_diagnostic,fit_calibrators,runtime_versions
from .boosting import calibrated
from .evaluation import evaluate,buckets
from .integrity import atomic_json,digest
from .registry import register,load_candidate
from .model import train
from .m3 import git_reference
from .feature_engineering import FEATURES
from .boosting import fit_boosting


def split(frame,start,end,later):
    if not start<=end<later:raise ValueError('Window/training cutoff must precede forward period')
    f=frame[frame.target.notna()]
    tr=f[f.season.between(start,end)];ev=f[f.season.eq(later)]
    if tr.empty or ev.empty:raise ValueError(f'Missing training or forward data for {start}–{end} → {later}')
    if not set(range(start,end+1))<=set(tr.season):raise ValueError('Historical window contains missing seasons; inspect audit-history')
    available=tr.kickoff+pd.Timedelta(hours=8)
    if 'result_available_at' in tr:available=pd.to_datetime(tr.result_available_at,utc=True).fillna(available)
    if available.max()>=ev.kickoff.min():raise ValueError('Chronological periods overlap')
    return tr,ev

def develop(frame,config):
    if max(f['validation'] for f in config['development_folds'])>2021:raise ValueError('M5 development is frozen through 2021; later outcomes are reporting only')
    rows=[]
    def evaluate_policy(algorithm,window,half_life,stage):
        for fold in config['development_folds']:
            tr,val=split(frame,config['windows'][window],fold['train_end'],fold['validation'])
            start=perf_counter();model=fit_history(tr,algorithm,config,half_life);seconds=perf_counter()-start
            p=model['pipeline'].predict_proba(val[model['features']])[:,1]
            rows.append({'stage':stage,'algorithm':algorithm,'window':window,'half_life':0 if half_life is None else half_life,'earliest_training_season':config['windows'][window],'training_cutoff':model['training_cutoff'],'validation':fold['validation'],'training_games':len(tr),'effective_sample_size':model['weighting']['effective_sample_size'],'runtime_seconds':seconds,**evaluate(val.target,p)})
    for algorithm in ['logistic','hgb']:
        for window in config['windows']:evaluate_policy(algorithm,window,None,'uniform_windows')
    uniform=pd.DataFrame(rows)
    rank=uniform.groupby(['algorithm','window']).agg(brier=('brier','mean'),log_loss=('log_loss','mean')).reset_index().sort_values(['algorithm','brier','log_loss','window'])
    selected={algorithm:rank[rank.algorithm.eq(algorithm)].head(config['selected_windows_per_algorithm']).window.tolist() for algorithm in ['logistic','hgb']}
    for algorithm in selected:
        for window in selected[algorithm]:
            for half in config['half_lives']:evaluate_policy(algorithm,window,half,'decay')
    trials=pd.DataFrame(rows)
    eligible=trials[[window in selected[algorithm] for algorithm,window in zip(trials.algorithm,trials.window)]]
    scores=eligible.groupby(['algorithm','window','half_life']).agg(brier=('brier','mean'),log_loss=('log_loss','mean')).reset_index().sort_values(['algorithm','brier','log_loss','window','half_life'])
    chosen={algorithm:{'window':str(scores[scores.algorithm.eq(algorithm)].iloc[0].window),'half_life':float(scores[scores.algorithm.eq(algorithm)].iloc[0].half_life)} for algorithm in selected}
    return trials,rank,scores,selected,chosen

def run(frame,reference,directory,registry_directory,config,provenance=None,feature_audit=None):
    if any(f['evaluation']<=2021 or f['calibration']<2021 for f in config['folds']):raise ValueError('Evaluation must follow development and chronological calibration')
    key=fingerprint(frame,{'protocol':config,'provenance':provenance or {},'reference_hash':fingerprint(reference,{})})
    directory=Path(directory);final=directory/key[:16]
    if final.exists():
        checks=json.loads((final/'outputs.json').read_text())
        if any(digest(final/p)!=sha for p,sha in checks.items()):raise ValueError('M5 report checksum mismatch')
        for version in json.loads((final/'registry_versions.json').read_text()):load_candidate(registry_directory,version)
        atomic_json({'run':final.name},directory/'latest.json');return final
    stage=directory/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    trials,window_scores,decay_scores,selected,chosen=develop(frame,config)
    trials.to_csv(stage/'development_trials.csv',index=False);window_scores.to_csv(stage/'development_windows.csv',index=False);decay_scores.to_csv(stage/'development_decay.csv',index=False)
    if feature_audit is not None:feature_audit.to_csv(stage/'feature_completeness.csv',index=False)
    outputs=[];training=[];versions=[];fold_metadata=[]
    for fold in config['folds']:
        ev=frame[frame.season.eq(fold['evaluation'])&frame.target.notna()]
        ref_tr,ref_ev=split(reference,2018,fold['train_end'],fold['evaluation'])
        if set(ref_ev.game_id)!=set(ev.game_id):raise ValueError('Reference/common-feature evaluation games differ')
        labels=ev.set_index('game_id').target
        if not ref_ev.set_index('game_id').target.sort_index().equals(labels.sort_index()):raise ValueError('Historical revisions changed reference outcomes; inspect source audit')
        ref_logistic=train(ref_tr);ref_hgb=fit_boosting(ref_tr,FEATURES+['elo_difference'],config['hgb_parameters'],config['cpu_threads'])
        probabilities={'logistic':pd.Series(ref_logistic['pipeline'].predict_proba(ref_ev[FEATURES])[:,1],index=ref_ev.game_id).reindex(ev.game_id).to_numpy(),'original_hgb':pd.Series(ref_hgb['pipeline'].predict_proba(ref_ev[FEATURES+['elo_difference']])[:,1],index=ref_ev.game_id).reindex(ev.game_id).to_numpy(),'elo_extended':ev.elo_probability.to_numpy(),'margin_elo_extended':ev.elo_margin_probability.to_numpy(),'elo_original':pd.Series(ref_ev.elo_probability.to_numpy(),index=ref_ev.game_id).reindex(ev.game_id).to_numpy(),'margin_elo_original':pd.Series(ref_ev.elo_margin_probability.to_numpy(),index=ref_ev.game_id).reindex(ev.game_id).to_numpy(),'pregame_win_percentage':np.clip(.5+ev.win.fillna(0).to_numpy()/2,.05,.95)}
        for algorithm in ['logistic','hgb']:
            policies=[(window,None) for window in config['windows']]+[(window,half) for window in selected[algorithm] for half in config['half_lives']]
            for window,half in policies:
                tr,_=split(frame,config['windows'][window],fold['train_end'],fold['evaluation'])
                name=f"{algorithm}_{window}_"+('uniform' if half is None else f'half{half:g}')
                start=perf_counter();model=fit_history(tr,algorithm,config,half);seconds=perf_counter()-start
                model['version']='m5-'+key[:12]+'-'+str(fold['evaluation'])+'-'+name
                model['training_window']={'policy':window,'earliest_eligible_season':config['windows'][window],'latest_training_cutoff':model['training_cutoff']}
                p=model['pipeline'].predict_proba(ev[model['features']])[:,1];probabilities[name]=p
                path=register(model,registry_directory,{'run_id':key,'report_reference':str(final),'evaluation_season':fold['evaluation'],'training_window':model['training_window'],'weighting':model['weighting'],'activation_blocked':True,'evaluation':evaluate(ev.target,p),'code_commit':git_reference()});versions.append(path.name)
                training.append({'model':name,'algorithm':algorithm,'window':window,'half_life':0 if half is None else half,'evaluation':fold['evaluation'],'training_games':len(tr),'runtime_seconds':seconds,**model['weighting'],**{'train_'+k:v for k,v in evaluate(tr.target,model['pipeline'].predict_proba(tr[model['features']])[:,1]).items()}})
                policy=chosen[algorithm]
                if window==policy['window'] and float(half or 0)==policy['half_life']:
                    cal=frame[frame.season.eq(fold['calibration'])&frame.target.notna()]
                    methods=fit_calibrators(model,cal,ev.kickoff.min(),config['isotonic_min_games'])
                    for method,calibrator in methods.items():
                        if algorithm=='hgb':
                            cm=calibrated(model,method,calibrator,cal)
                        else:
                            from .history_models import LogisticCalibrator
                            cm={**model,'pipeline':LogisticCalibrator(model['pipeline'],method,calibrator),'calibration':{'method':method,'seasons':[fold['calibration']],'cutoff':(cal.kickoff.max()+pd.Timedelta(hours=8)).isoformat()}}
                            cm['training_cutoff']=cm['calibration']['cutoff']
                        cm['version']=model['version']+'-'+method
                        cp=cm['pipeline'].predict_proba(ev[model['features']])[:,1];probabilities[name+'_'+method]=cp
                        path=register(cm,registry_directory,{'run_id':key,'report_reference':str(final),'evaluation_season':fold['evaluation'],'training_window':model['training_window'],'weighting':model['weighting'],'activation_blocked':True,'evaluation':evaluate(ev.target,cp),'code_commit':git_reference()});versions.append(path.name)
        for name,p in probabilities.items():
            o=ev[['game_id','season','week','kickoff','home_team','away_team','target']].copy();o['model']=name;o['probability']=p;outputs.append(o)
        fold_metadata.append({**fold,'evaluation_games':len(ev),'evaluation_start':ev.kickoff.min().isoformat(),'reference_training_cutoff':(ref_tr.kickoff.max()+pd.Timedelta(hours=8)).isoformat()})
    predictions=pd.concat(outputs,ignore_index=True);predictions.to_parquet(stage/'predictions.parquet',index=False)
    comparisons=[];within=[];decay_effects=[];vs_boosting=[];elo_warmup=[];calibration=[];bands=[];confidence=[]
    for period,f in [('all_exploratory',predictions),('examined_2024_2025',predictions[predictions.season.isin([2024,2025])])]+[(str(y),predictions[predictions.season.eq(y)]) for y in sorted(predictions.season.unique())]:
        if f.empty:continue
        ci=paired_intervals(f,config['bootstrap_replicates'],config['seed'],config['confidence_level']);ci['period']=period;comparisons.append(ci)
        subset=f[f.model.str.startswith('hgb_W')|f.model.eq('original_hgb')]
        c=paired_intervals(subset,config['bootstrap_replicates'],config['seed'],config['confidence_level'],reference='original_hgb');c['period']=period;vs_boosting.append(c)
        for reference_name,extended in [('elo_original','elo_extended'),('margin_elo_original','margin_elo_extended')]:
            c=paired_intervals(f[f.model.isin([reference_name,extended])],config['bootstrap_replicates'],config['seed'],config['confidence_level'],reference=reference_name);c['period']=period;elo_warmup.append(c)
        for algorithm in ['logistic','hgb']:
            subset=f[f.model.str.startswith(algorithm+'_W')]
            c=paired_intervals(subset,config['bootstrap_replicates'],config['seed'],config['confidence_level'],reference=f'{algorithm}_W1_uniform');c['period']=period;within.append(c)
        for algorithm in ['logistic','hgb']:
            for window in selected[algorithm]:
                prefix=f'{algorithm}_{window}_'
                subset=f[f.model.str.startswith(prefix)]
                c=paired_intervals(subset,config['bootstrap_replicates'],config['seed'],config['confidence_level'],reference=prefix+'uniform');c['period']=period;decay_effects.append(c)
        for name,g in f.groupby('model'):
            calibration.append({'period':period,'model':name,**evaluate(g.target,g.probability),**calibration_diagnostic(g.target,g.probability)})
            b=buckets(g.target,g.probability);b['period']=period;b['model']=name;bands.append(b)
            b=buckets(g.target,g.probability,True);b['period']=period;b['model']=name;confidence.append(b)
    pd.concat(comparisons).to_csv(stage/'comparison.csv',index=False);pd.concat(within).to_csv(stage/'within_algorithm.csv',index=False)
    pd.concat(vs_boosting).to_csv(stage/'vs_original_boosting.csv',index=False)
    pd.concat(elo_warmup).to_csv(stage/'elo_warmup.csv',index=False)
    phases=[]
    for (name,year,phase),g in predictions.assign(phase=np.where(predictions.week.le(3),'weeks_1_3','weeks_4_plus')).groupby(['model','season','phase']):
        phases.append({'model':name,'season':year,'phase':phase,**evaluate(g.target,g.probability)})
    pd.DataFrame(phases).to_csv(stage/'season_phase.csv',index=False)
    pd.concat(decay_effects).to_csv(stage/'decay_effects.csv',index=False)
    pd.DataFrame(calibration).to_csv(stage/'calibration.csv',index=False);pd.concat(bands).to_csv(stage/'probability_buckets.csv',index=False);pd.concat(confidence).to_csv(stage/'confidence_buckets.csv',index=False)
    pd.DataFrame(training).to_csv(stage/'training_metadata.csv',index=False)
    atomic_json(versions,stage/'registry_versions.json')
    from .registry import list_candidates
    atomic_json([m for m in list_candidates(registry_directory) if m['version'] in versions],stage/'registry_metadata.json')
    try:
        import resource,sys
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    except ImportError:peak=None
    metadata={'linux_or_macos_peak_rss_bytes':peak,'run_id':key,'protocol':config,'selected_windows':selected,'selected_policies':chosen,'selection_end':2021,'folds':fold_metadata,'provenance':provenance or {},'common_features':{'logistic':COMMON,'hgb':COMMON+['elo_difference']},'feature_history':'All common-feature window policies use identical 1999-onward pregame state. W1 means earliest training label season, not resetting priors/Elo to 2018. Original full-feature M2/M4 references are separate and use only the original modern source history.','kickoff_limits':'Date-only games use local day start as feature lower bound and next day 08:00 Eastern as availability upper proxy; no actual clock fabricated. Rest excluded from every common-feature window.','warmup':'1999 initialization has no 1998 prior and Elo starts at 1500; first-season incomplete features are retained for training-only missing-data treatment, not evaluated as mature history.','prior_weight':'Four games unchanged for every window; no tuning on evaluation years.','code_commit':git_reference(),'module_hashes':{p.name:digest(p) for p in Path(__file__).parent.glob('*.py')},'runtime_versions':runtime_versions(),'promotion':'All M5 models experimental and activation-blocked; champion unchanged.','configuration_counts':{'development_fits':len(trials),'forward_uncalibrated_policies':len(training),'registered_fold_models':len(versions)},'inference_limits':'Previously examined seasons; paired week bootstrap unadjusted for multiplicity, repeated teams/interweek dependence, few independent seasons; interval exclusion alone is not confirmation.'}
    atomic_json(metadata,stage/'metadata.json')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    chosen_names=['logistic','original_hgb']+[f"{a}_{p['window']}_"+('uniform' if p['half_life']==0 else f"half{p['half_life']:g}") for a,p in chosen.items()]
    sample=predictions[predictions.season.isin([2024,2025])]
    if sample.empty:sample=predictions
    fig,ax=plt.subplots()
    for name,g in sample[sample.model.isin(chosen_names)].groupby('model'):
        b=buckets(g.target,g.probability);ax.plot(b.predicted,b.observed,'o-',label=name)
    ax.plot([0,1],[0,1],'k--');ax.set(xlabel='Predicted home win probability',ylabel='Observed home win fraction',title='M5 exploratory historical-training reliability');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(stage/'reliability.png');plt.close(fig)
    from .history_report import write_comparison
    write_comparison(stage)
    atomic_json({p.name:digest(p) for p in stage.iterdir()},stage/'outputs.json');stage.rename(final);atomic_json({'run':final.name},directory/'latest.json')
    return final
