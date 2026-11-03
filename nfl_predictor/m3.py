"""M3 experiments extend M2's alignment, uncertainty and preprocessing contracts."""
from dataclasses import asdict,replace
from pathlib import Path
import json
import subprocess
import uuid
import numpy as np
import pandas as pd
from .analysis import fingerprint,paired_intervals,validate_fold,calibration_diagnostic,runtime_versions
from .feature_engineering import FEATURES,cached_build
from .model import train
from .elo import EloParameters,replay,rankings,ALGORITHM
from .schedule_features import schedule_features,REST_FEATURES,post_bye_diagnostic
from .quarterbacks import features as qb_features
from .integrity import atomic_json,digest
from .evaluation import evaluate,buckets
from .reporting import table

CANDIDATES={
 'logistic':FEATURES,
 'm2_elo':FEATURES+['elo_difference'],
 'm2_rest':[f for f in FEATURES if f!='rest']+REST_FEATURES,
 'm2_elo_rest':[f for f in FEATURES if f!='rest']+REST_FEATURES+['elo_difference'],
 'm2_rest_days':[f for f in FEATURES if f!='rest']+['rest_advantage'],
 'm2_bye':FEATURES+['bye_difference'],
 'm2_short_rest':FEATURES+['short_rest_difference'],
 'm2_extended_rest':FEATURES+['extended_rest_difference'],
 'm2_rest_redundancy_check':FEATURES+REST_FEATURES}


def git_reference():
    try:
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).parents[1],text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):
        return 'unavailable (source archive without Git metadata)'

def _existing(directory,key):
    final=Path(directory)/key[:16]
    if not final.exists():return None
    checks=json.loads((final/'outputs.json').read_text())
    if any(digest(final/name)!=sha for name,sha in checks.items()):raise ValueError('M3 artifacts corrupt; preserve evidence and select a new output directory')
    atomic_json({'run':final.name},Path(directory)/'latest.json')
    return final

def _publish(stage,final):
    atomic_json({p.name:digest(p) for p in stage.iterdir()},stage/'outputs.json')
    stage.rename(final);atomic_json({'run':final.name},final.parent/'latest.json')
    return final

def ratings_bundle(schedules,directory,cutoff,parameters=None,source_metadata=None):
    p=parameters or EloParameters(); cutoff=pd.Timestamp(cutoff)
    key=fingerprint(schedules,{'algorithm':ALGORITHM,'elo':asdict(p),'cutoff':cutoff.isoformat(),'sources':source_metadata or {}})
    existing=_existing(directory,key)
    if existing:return existing
    stage=Path(directory)/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    pre,h,_=replay(schedules,p,cutoff);r,_=rankings(schedules,cutoff,p)
    pre.to_parquet(stage/'pregame.parquet',index=False);h.to_parquet(stage/'history.parquet',index=False)
    r.to_parquet(stage/'rankings.parquet',index=False)
    h.to_csv(stage/'history.csv',index=False);r.to_csv(stage/'rankings.csv',index=False)
    atomic_json({'algorithm':ALGORITHM,'parameters':asdict(p),'cutoff':cutoff.isoformat(),'source_manifests':source_metadata or {},'warmup_season':int(schedules.season.min()),'availability':'verified result time if supplied, otherwise kickoff+8h; strict before cutoff','previous_week':'seven calendar days before cutoff; offseason regression may enter delta'},stage/'metadata.json')
    return _publish(stage,Path(directory)/key[:16])

def prepare(schedules,metrics,records,config,cache_directory):
    frame=cached_build(schedules,metrics,cache_directory)
    p=EloParameters(**config['elo'])
    pre,_,_=replay(schedules,p)
    margin,_,_=replay(schedules,replace(p,margin=True))
    rest=schedule_features(schedules,short_days=config['short_rest_days'],extended_days=config['extended_rest_days'])
    frame=frame.merge(pre[['game_id','home_elo','away_elo','elo_difference','elo_probability','warmup']],on='game_id',validate='one_to_one')
    frame=frame.merge(margin[['game_id','elo_probability']].rename(columns={'elo_probability':'elo_margin_probability'}),on='game_id',validate='one_to_one')
    return frame.merge(rest,on='game_id',validate='one_to_one').merge(qb_features(schedules,records),on='game_id',validate='one_to_one')

def compare(frame,directory,config,source_metadata=None):
    key=fingerprint(frame,{'protocol':config,'source_manifests':source_metadata or {}})
    existing=_existing(directory,key)
    if existing:return existing
    directory=Path(directory);stage=directory/('.staging-'+uuid.uuid4().hex);stage.mkdir(parents=True)
    records=[];folds=[];coefficients=[];warmup_sensitivity=[];qb_predictions=[]
    for fold in config['folds']:
        tr,_,ev=validate_fold(frame,fold)
        if ev.warmup.any(): raise ValueError('Initialization season cannot be an evaluation season')
        rates=float(tr.target.mean())
        probabilities={'elo_only':ev.elo_probability.to_numpy(),'elo_margin':ev.elo_margin_probability.to_numpy(),'pregame_win_percentage':np.clip(.5+ev.win.fillna(0).to_numpy()/2,.05,.95),'always_home':np.full(len(ev),max(.500001,rates)),'historical_home_rate':np.full(len(ev),rates)}
        for name,features in CANDIDATES.items():
            model=train(tr,features)
            probabilities[name]=model['pipeline'].predict_proba(ev[features])[:,1]
            for feature,coef in zip(features,model['pipeline'][-1].coef_[0]): coefficients.append({'model':name,'evaluation':fold['evaluation'],'feature':feature,'coefficient':coef})
            # Matched sensitivity exercise excludes initialization season for all fitted models.
            warmed=tr[~tr.warmup]
            if len(warmed) and warmed.target.nunique()==2:
                fitted=train(warmed,features)
                warmup_sensitivity.append({'model':name,'evaluation':fold['evaluation'],'training_start':int(warmed.season.min()),**evaluate(ev.target,fitted['pipeline'].predict_proba(ev[features])[:,1])})
        for name,p in probabilities.items():
            out=ev.copy();out['model']=name;out['probability']=p;out['training_through']=fold['train_end'];out['evaluation_season']=fold['evaluation'];out['correct']=out.target.eq(out.probability.ge(.5));records.append(out)
        tq=tr[tr.qb_verified & tr.qb_change_difference.notna()];eq=ev[ev.qb_verified & ev.qb_change_difference.notna()]
        qb_status='Skipped: no sufficient matched, verified pregame QB coverage'
        if len(tq)>=20 and len(eq)>=10 and tq.target.nunique()==2:
            for name,features in [('logistic',FEATURES),('qb_experimental',FEATURES+['qb_change_difference'])]:
                fitted=train(tq,features);out=eq.copy();out['model']=name;out['probability']=fitted['pipeline'].predict_proba(eq[features])[:,1];qb_predictions.append(out)
            qb_status='Matched QB-only sample, evaluated separately'
        folds.append({**fold,'training_cutoff':(tr.kickoff.max()+pd.Timedelta(hours=8)).isoformat(),'evaluation_start':ev.kickoff.min().isoformat(),'evaluation_end':ev.kickoff.max().isoformat(),'training_games':len(tr),'evaluation_games':len(ev),'qb_training_games':len(tq),'qb_evaluation_games':len(eq),'qb_status':qb_status})
    predictions=pd.concat(records,ignore_index=True)
    if predictions.duplicated(['game_id','model']).any(): raise ValueError('Overlapping M3 evaluation folds')
    predictions.to_parquet(stage/'predictions.parquet',index=False)
    comparisons=[];calibration=[];bucket_tables=[];versus_win=[];elo_variants=[]
    for period,f in [('all_exploratory',predictions),('examined_2024_2025',predictions[predictions.season.isin([2024,2025])])]+[(str(y),predictions[predictions.season.eq(y)]) for y in sorted(predictions.season.unique())]:
        if f.empty:continue
        kwargs={'replicates':config['bootstrap_replicates'],'seed':config['seed'],'confidence':config['confidence_level']}
        c=paired_intervals(f,**kwargs);c['period']=period;comparisons.append(c)
        variants=paired_intervals(f[f.model.isin(['elo_only','elo_margin'])],reference='elo_only',**kwargs);variants['period']=period;elo_variants.append(variants)
        e=paired_intervals(f[f.model.isin(['elo_only','elo_margin','pregame_win_percentage'])],reference='pregame_win_percentage',**kwargs);e['period']=period;versus_win.append(e)
        for name,g in f.groupby('model'):
            calibration.append({'period':period,'model':name,**evaluate(g.target,g.probability),**calibration_diagnostic(g.target,g.probability)})
            b=buckets(g.target,g.probability);b['period']=period;b['model']=name;bucket_tables.append(b)
    pd.concat(comparisons).to_csv(stage/'comparison.csv',index=False)
    pd.concat(versus_win).to_csv(stage/'elo_vs_win_percentage.csv',index=False)
    pd.concat(elo_variants).to_csv(stage/'elo_variant_comparison.csv',index=False)
    pd.DataFrame(calibration).to_csv(stage/'calibration.csv',index=False)
    pd.concat(bucket_tables).to_csv(stage/'probability_buckets.csv',index=False)
    pd.DataFrame(coefficients).to_csv(stage/'coefficients.csv',index=False)
    pd.DataFrame(warmup_sensitivity).to_csv(stage/'warmup_sensitivity.csv',index=False)
    post_bye_diagnostic(frame[frame.season.le(2025)]).to_csv(stage/'post_bye_diagnostic.csv',index=False)
    missing=frame[frame.target.notna()].groupby('season')[REST_FEATURES+['qb_change_difference']].agg(lambda v:float(v.isna().mean()))
    missing.to_csv(stage/'feature_missingness.csv')
    if qb_predictions:
        qb=pd.concat(qb_predictions);qb.to_parquet(stage/'qb_matched_predictions.parquet',index=False)
        paired_intervals(qb,config['bootstrap_replicates'],config['seed'],config['confidence_level']).to_csv(stage/'qb_matched_comparison.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots();sample=predictions[predictions.season.isin([2024,2025])]
    if sample.empty:sample=predictions
    for name,g in sample[sample.model.isin(['logistic','elo_only','elo_margin','m2_elo','m2_rest','m2_elo_rest'])].groupby('model'):
        b=buckets(g.target,g.probability);ax.plot(b.predicted,b.observed,'o-',label=name)
    ax.plot([0,1],[0,1],'k--');ax.set(xlabel='Predicted home-win probability',ylabel='Observed home-win fraction',title='M3 exploratory reliability');ax.legend(fontsize=7);fig.tight_layout();fig.savefig(stage/'reliability.png');plt.close(fig)
    metadata={'run_id':key,'protocol':config,'folds':folds,'candidate_features':CANDIDATES,'elo_version':ALGORITHM,'source_manifests':source_metadata or {},'code_and_data_fingerprint':key,'module_hashes':{p.name:digest(p) for p in Path(__file__).parent.glob('*.py')},'runtime_versions':runtime_versions(),'code_commit':git_reference(),'preprocessing':'M2 training-only mean imputation, StandardScaler, logistic L2 C=1 seed=42 max_iter=1000','initialization':'First source season is warmup, never evaluated; logistic champion retains original training seasons; warmup-excluded matched training sensitivity also exported','promotion':'Retain M2 champion. All M3 candidates experimental.','qb':'Only verified source AND observation timestamps before game kickoff. No retrospective starters used as that game pregame features.','intervals':'M2 paired season-week percentile bootstrap; exploratory, unadjusted, repeated teams may violate independent-week assumptions','margin_formula':'clip(log1p(min(abs(margin),42))*2.2/(2.2+.001*clip(winner_pregame_elo_advantage,-1000,1000)),.5,3); ties multiplier=1','rest':'Joint model removes old rest; independent indicators and redundant-rest check are separate candidates. Schedule vintages are retrospective.'}
    atomic_json(metadata,stage/'metadata.json')
    results=pd.concat(comparisons);r=results[results.period.eq('examined_2024_2025')]
    if r.empty:r=results[results.period.eq('all_exploratory')]
    (stage/'MODEL_COMPARISON.md').write_text('# M3 exploratory comparisons\n\n'+table(r[['model','metric','estimate','low','high','difference','difference_low','difference_high','games']])+'\n\nDeltas are candidate minus the original M2 logistic benchmark. Positive accuracy and negative Brier/log-loss favor candidates. Identical evaluation games are required. No automatic promotion; 2024–2025 was previously examined. See calibration, individual season results, missingness, warmup sensitivity and Elo-versus-win-percentage tables before interpreting apparent improvements.\n\nQB: '+json.dumps([{'evaluation':f['evaluation'],'status':f['qb_status'],'training':f['qb_training_games'],'evaluation_games':f['qb_evaluation_games']} for f in folds])+'\n')
    return _publish(stage,directory/key[:16])
