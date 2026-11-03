"""Predefined forward ensembles, disjoint calibration and development-only selection."""
from pathlib import Path
from time import perf_counter
import json
import uuid
import numpy as np
import pandas as pd
from .ensemble import BASES,PROBABILITIES,fit_policies,calibrated_policies,policy_parameters,validate_matrix,timestamp
from .ensemble_data import identity,code_identity,aligned
from .evaluation import evaluate,buckets
from .analysis import paired_intervals,calibration_diagnostic,runtime_versions
from .integrity import atomic_json,digest
from .registry import register,load_candidate


def fold_samples(matrix,year,config,evaluation_start=None):
    validate_matrix(matrix,True)
    cal=matrix[matrix.season.eq(year-1)].copy()
    if cal.empty:raise ValueError('Missing separate calibration season')
    start=cal.data_cutoff.min()
    meta_candidates=matrix[matrix.season.between(config['meta_start'],year-2)]
    meta=meta_candidates[meta_candidates.available_at.lt(start)].copy()
    ev=matrix[matrix.season.eq(year)].copy()
    evaluation_start=timestamp(evaluation_start) if evaluation_start is not None else (ev.data_cutoff.min() if len(ev) else pd.Timestamp(f'{year}-08-01',tz='UTC'))
    calibration_candidates=len(cal);cal=cal[cal.available_at.lt(evaluation_start)]
    if set(meta.game_id)&set(cal.game_id) or set(cal.game_id)&set(ev.game_id):raise ValueError('Meta/calibration/evaluation periods overlap')
    if len(meta) and meta.available_at.max()>=start:raise ValueError('Meta outcomes overlap calibration')
    audit={'evaluation':int(year),'meta_seasons':sorted(meta.season.unique().tolist()),'calibration_season':year-1,'meta_games':len(meta),'calibration_games':len(cal),'evaluation_games':len(ev),'meta_outcome_cutoff':meta.available_at.max().isoformat() if len(meta) else None,'calibration_start':start.isoformat(),'calibration_outcome_cutoff':cal.available_at.max().isoformat() if len(cal) else None,'evaluation_start':evaluation_start.isoformat(),'excluded_delayed_meta_labels':len(meta_candidates)-len(meta),'excluded_delayed_calibration_labels':calibration_candidates-len(cal)}
    return meta,cal,ev,audit


def fit_fold(matrix,year,config,evaluation_start=None):
    meta,cal,ev,audit=fold_samples(matrix,year,config,evaluation_start)
    raw,optimizer=fit_policies(meta,cal.data_cutoff.min(),config)
    policies,skipped=calibrated_policies(raw,cal,audit['evaluation_start'],config,audit['meta_outcome_cutoff'])
    audit.update(optimizer=optimizer,skipped_calibrations=skipped,meta_fingerprint=identity(meta.drop(columns=['generated_at'],errors='ignore')),calibration_fingerprint=identity(cal.drop(columns=['generated_at'],errors='ignore')))
    rows=[]
    for name in BASES:
        f=ev[['game_id','season','week','target']].copy();f['model']=name;f['probability']=ev['p_'+name];rows.append(f)
    for name,policy in policies.items():
        f=ev[['game_id','season','week','target']].copy();f['model']=name
        f['probability']=policy.predict_proba(ev)[:,1] if len(ev) else np.array([]);rows.append(f)
    return policies,pd.concat(rows,ignore_index=True),audit


def select_policy(development,config):
    f=development[development.season.isin(config['development_seasons'])]
    seasons=set(config['development_seasons'])
    if set(f.season)!=seasons:raise ValueError('Missing predefined development seasons')
    # Paired completeness is required before any candidate can participate in selection.
    ids=f.groupby('season').game_id.apply(set).to_dict()
    rows=[]
    for name,g in f.groupby('model'):
        if set(g.season)!=seasons or any(set(g[g.season.eq(year)].game_id)!=ids[year] for year in seasons):continue
        yearly=[evaluate(v.target,v.probability) for _,v in g.groupby('season')]
        rows.append({'model':name,'brier':float(np.mean([r['brier'] for r in yearly])),'log_loss':float(np.mean([r['log_loss'] for r in yearly])),'seasons':len(yearly)})
    summary=pd.DataFrame(rows).sort_values(['brier','log_loss','model'])
    alternatives=summary[~summary.model.isin(BASES)]
    individuals=summary[summary.model.isin(BASES)]
    if alternatives.empty or len(individuals)!=3:raise ValueError('Insufficient complete development candidates')
    return alternatives.iloc[0].model,individuals.iloc[0].model,summary


def complementarity(matrix):
    rows=[];pairs=[]
    for period,f in [('development',matrix[matrix.season.isin([2022,2023])]),('examined_2024_2025',matrix[matrix.season.isin([2024,2025])])]:
        for i,a in enumerate(BASES):
            for b in BASES[i+1:]:
                pa=f['p_'+a];pb=f['p_'+b];disagree=pa.ge(.5).ne(pb.ge(.5))
                rows.append({'period':period,'first':a,'second':b,'games':len(f),'probability_correlation':pa.corr(pb),'error_correlation':(pa-f.target).corr(pb-f.target),'disagreement_fraction':float(disagree.mean()),'mean_absolute_probability_gap':float((pa-pb).abs().mean()),'mean_confidence_first':float(np.maximum(pa,1-pa).mean()),'mean_confidence_second':float(np.maximum(pb,1-pb).mean())})
                for label,mask in [('agree',~disagree),('disagree',disagree)]:
                    if mask.any():
                        for name in [a,b]:pairs.append({'period':period,'first':a,'second':b,'bucket':label,'model':name,**evaluate(f.loc[mask,'target'],f.loc[mask,'p_'+name])})
    return pd.DataFrame(rows),pd.DataFrame(pairs)


def bundle(policy,name,year,refs,audit,selection,config):
    cutoff=max([timestamp(audit['meta_outcome_cutoff']),timestamp(audit['calibration_outcome_cutoff'])]+[timestamp(r['training_cutoff']) for r in refs.values()])
    if selection is not None:cutoff=max(cutoff,timestamp(selection['outcome_cutoff']))
    info={'method':name,'target_season':int(year),'refs':refs,'audit':audit,'selection':selection,'parameters':policy_parameters(policy),'code':code_identity()}
    # Optimizer diagnostics are deterministic; measured timing is never part of identity.
    key=identity(info)
    return {'version':f'm7-ensemble-{year}-{key[:20]}','pipeline':policy,'features':PROBABILITIES,'feature_schema':'m7-ensemble-v1','algorithm':'chronological ensemble','training_cutoff':cutoff.isoformat(),'base_refs':refs,'ensemble_method':name,'parameters':policy_parameters(policy),'fold':audit,'selection':selection,'target_season':int(year),'calibration':{'method':policy.calibration_method,'season':year-1,'cutoff':audit['calibration_outcome_cutoff']},'dataset_fingerprint':audit['meta_fingerprint'],'activation_blocked':True,'activation_block_reason':'M7 ensembles remain experimental; production champion activation is prohibited.'}


def run(matrix,matrix_meta,directory,registry,config,observed_before=None):
    observed_before=timestamp(observed_before or pd.Timestamp.now(tz='UTC'))
    matrix,audit_alignment=aligned(matrix,observed_before)
    # Current-season labels are never research selection inputs.
    historical=matrix[matrix.season.le(2025)]
    key=identity(code_identity(),config,historical.drop(columns=['generated_at'],errors='ignore'),matrix_meta['annual_base_refs'])
    final=Path(directory)/key[:16]
    if final.exists():
        checks=json.loads((final/'outputs.json').read_text())
        if any(digest(final/name)!=sha for name,sha in checks.items()):raise ValueError('M7 result integrity failure')
        for version in json.loads((final/'registry_versions.json').read_text()):load_candidate(registry,version)
        atomic_json({'run':final.name},Path(directory)/'latest.json');return final
    started=perf_counter();stage=Path(directory)/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    predictions=[];fitted={};folds=[];timings=[]
    for year in config['development_seasons']+config['evaluation_seasons']:
        tick=perf_counter();policies,p,audit=fit_fold(historical,year,config);fitted[year]=policies;predictions.append(p);folds.append(audit)
        timings.append({'evaluation':year,'fitting_prediction_seconds':perf_counter()-tick})
    all_predictions=pd.concat(predictions,ignore_index=True)
    selected,strongest,selection_table=select_policy(all_predictions,config)
    development=historical[historical.season.isin(config['development_seasons'])]
    selection={'method':selected,'strongest_individual':strongest,'seasons':config['development_seasons'],'outcome_cutoff':development.available_at.max().isoformat(),'rules':config['selection'],'ensemble_configurations_compared':len(selection_table[~selection_table.model.isin(BASES)])}
    if timestamp(selection['outcome_cutoff'])>=historical.loc[historical.season.eq(min(config['evaluation_seasons'])),'data_cutoff'].min():raise ValueError('Model selection overlaps historical evaluation')
    versions=[];parameter_rows=[]
    for year,policies in fitted.items():
        audit=next(a for a in folds if a['evaluation']==year)
        for name,policy in policies.items():
            m=bundle(policy,name,year,matrix_meta['annual_base_refs'][str(year)],audit,selection if year in config['evaluation_seasons'] else None,config)
            register(m,registry,{'report_reference':str(final),'evaluation_protocol':config,'stacking_data_fingerprint':audit['meta_fingerprint'],'base_training_cutoffs':{n:r['training_cutoff'] for n,r in m['base_refs'].items()},'meta_training_cutoff':audit['meta_outcome_cutoff'],'selection':m['selection'],'parameters':m['parameters'],'classification':'retrospective research; not an issued forecast'})
            versions.append(m['version']);parameter_rows.append({'evaluation':year,'model':name,**policy_parameters(policy)})
    live_year=2026
    live_policies,_,live_audit=fit_fold(historical,live_year,config,matrix_meta['season_starts'][str(live_year)])
    if selected not in live_policies:raise ValueError('Selected policy unavailable for prospective calendar; no silent substitute')
    live=bundle(live_policies[selected],selected,live_year,matrix_meta['annual_base_refs'][str(live_year)],live_audit,selection,config)
    register(live,registry,{'report_reference':str(final),'evaluation_protocol':config,'stacking_data_fingerprint':live_audit['meta_fingerprint'],'parameters':live['parameters'],'selection':selection,'classification':'experimental prospective adapter; forecasts issued separately'})
    versions.append(live['version']);folds.append(live_audit)
    all_predictions['role']=np.where(all_predictions.season.isin(config['development_seasons']),'development','examined_historical')
    all_predictions.to_parquet(stage/'predictions.parquet',index=False)
    summaries=[];calibration=[];confidence=[];probability_buckets=[];phase=[];favorite=[];disagreement=[]
    periods=[('development',config['development_seasons']),('examined_2024_2025',config['evaluation_seasons'])]+[(str(y),[y]) for y in config['development_seasons']+config['evaluation_seasons']]
    for period,years in periods:
        f=all_predictions[all_predictions.season.isin(years)]
        for reference in dict.fromkeys(['boosting','logistic',strongest]):
            c=paired_intervals(f,config['bootstrap_replicates'],config['seed'],config['confidence_level'],reference);c['period']=period;summaries.append(c)
        for name,g in f.groupby('model'):
            calibration.append({'period':period,'model':name,**evaluate(g.target,g.probability),**calibration_diagnostic(g.target,g.probability)})
            b=buckets(g.target,g.probability,True);b['period']=period;b['model']=name;confidence.append(b)
            b=buckets(g.target,g.probability);b['period']=period;b['model']=name;probability_buckets.append(b)
    joined=all_predictions.merge(historical[['game_id']+PROBABILITIES],on='game_id',validate='many_to_one')
    for (name,year),g in joined.groupby(['model','season']):
        for label,mask in [('weeks_1_3',g.week.le(3)),('weeks_4_plus',g.week.gt(3))]:
            if mask.any():phase.append({'model':name,'season':year,'phase':label,**evaluate(g.loc[mask,'target'],g.loc[mask,'probability'])})
        # Favorite means a model's >=50% choice; no market odds are used.
        p=g.probability.to_numpy();y=g.target.to_numpy();predicted_home=p>=.5
        favorite.append({'model':name,'season':year,'games':len(g),'favorite_win_rate':float(np.mean(predicted_home==y)),'mean_favorite_probability':float(np.mean(np.maximum(p,1-p))),'underdog_win_rate':float(np.mean(predicted_home!=y))})
        agrees=g[PROBABILITIES].ge(.5).nunique(axis=1).eq(1)
        for label,mask in [('bases_agree',agrees),('bases_disagree',~agrees)]:
            if mask.any():disagreement.append({'model':name,'season':year,'bucket':label,**evaluate(g.loc[mask,'target'],g.loc[mask,'probability'])})
    pd.concat(summaries).to_csv(stage/'comparison.csv',index=False);pd.DataFrame(calibration).to_csv(stage/'calibration.csv',index=False)
    pd.concat(confidence).to_csv(stage/'confidence_buckets.csv',index=False);pd.DataFrame(phase).to_csv(stage/'season_phase.csv',index=False)
    pd.concat(probability_buckets).to_csv(stage/'probability_buckets.csv',index=False)
    pd.DataFrame(favorite).to_csv(stage/'favorite_underdog.csv',index=False);pd.DataFrame(disagreement).to_csv(stage/'disagreement.csv',index=False)
    correlations,pairs=complementarity(historical);correlations.to_csv(stage/'complementarity.csv',index=False);pairs.to_csv(stage/'pair_disagreements.csv',index=False)
    selection_table.to_csv(stage/'development_selection.csv',index=False);pd.DataFrame(parameter_rows).to_csv(stage/'parameters.csv',index=False)
    pd.DataFrame(timings).to_csv(stage/'runtime.csv',index=False)
    atomic_json(selection,stage/'selection.json');atomic_json(versions,stage/'registry_versions.json')
    atomic_json({'version':live['version'],'method':selected,'target_season':2026},stage/'prospective_model.json')
    # Publish the requested prediction matrix as a derived research artifact;
    # retain excluded rows in the source cache and audit their counts separately.
    historical.to_parquet(stage/'base_predictions.parquet',index=False)
    atomic_json(matrix_meta,stage/'base_prediction_metadata.json')
    try:
        import resource,sys
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    except ImportError:peak=None
    atomic_json({'run':key,'protocol':config,'folds':folds,'alignment':audit_alignment,'matrix_fingerprint':matrix_meta['key'],'selection':selection,'runtime_seconds':perf_counter()-started,'peak_rss_bytes':peak,'runtime_versions':runtime_versions(),'code_fingerprint':code_identity(),'classification':'development and repeatedly examined historical results; no independent prospective outcome claim','promotion':'All M7 artifacts activation-blocked. M2 production preserved.','annual_reference':'Annual prior-season refits differ from M5 frozen-2022 evaluation; use matched M7 boosting benchmark.'},stage/'metadata.json')
    from .ensemble_report import comparison_report
    comparison_report(stage)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots()
    for name in BASES+[selected]:
        g=all_predictions[all_predictions.season.isin(config['evaluation_seasons'])&all_predictions.model.eq(name)]
        b=buckets(g.target,g.probability);ax.plot(b.predicted,b.observed,'o-',label=name)
    ax.plot([0,1],[0,1],'k--');ax.set(xlabel='Predicted home win probability',ylabel='Observed home win fraction',title='M7 exploratory reliability');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(stage/'reliability.png');plt.close(fig)
    atomic_json({p.name:digest(p) for p in stage.iterdir()},stage/'outputs.json');stage.rename(final)
    atomic_json({'run':final.name},Path(directory)/'latest.json');return final
