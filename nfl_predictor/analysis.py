"""Exploratory forward evaluation. Never mutates production models or forecasts."""
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression
from .feature_engineering import FEATURES
from .model import train
from .evaluation import evaluate,buckets
from .integrity import atomic_json,digest

GROUPS = {
    'offensive_efficiency':['off_epa','off_success','off_yards'],
    'defensive_efficiency':['def_epa','def_success','def_yards'],
    'scoring':['scoring'], 'turnovers':['turnover'], 'win_percentage':['win'],
    'recent_performance':['recent_off_epa','recent_def_epa'],
    'rest_venue':['rest','neutral']}
DIVISIONS = {
 'AFC East':['BUF','MIA','NE','NYJ'],'AFC North':['BAL','CIN','CLE','PIT'],
 'AFC South':['HOU','IND','JAX','TEN'],'AFC West':['DEN','KC','LAC','LV'],
 'NFC East':['DAL','NYG','PHI','WAS'],'NFC North':['CHI','DET','GB','MIN'],
 'NFC South':['ATL','CAR','NO','TB'],'NFC West':['ARI','LA','SF','SEA']}
TEAM_DIVISION={team:division for division,teams in DIVISIONS.items() for team in teams}

def _probabilities(p):
    p=np.asarray(p,dtype=float)
    if p.ndim!=1 or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Probabilities must be finite one-dimensional values in [0,1]')
    return p

def logit(p):
    p=np.clip(_probabilities(p),1e-6,1-1e-6)
    return np.log(p/(1-p)).reshape(-1,1)

def calibration_diagnostic(y,p):
    if len(np.unique(y))<2:
        return {'intercept':None,'slope':None}
    if np.std(p)<1e-10:
        # Constant predictions cannot identify both an intercept and a slope.
        shift=float(logit([np.mean(y)])[0,0]-logit([np.mean(p)])[0,0])
        return {'intercept':shift,'slope':None}
    fit=LogisticRegression(C=1e12,max_iter=1000).fit(logit(p),y)
    return {'intercept':float(fit.intercept_[0]),'slope':float(fit.coef_[0,0])}

def fit_calibrators(base, calibration, evaluation_start, min_games=200):
    if calibration.empty or calibration.target.nunique()<2:
        raise ValueError('Calibration needs non-tie games in both classes')
    if pd.Timestamp(base['training_cutoff']) >= calibration.kickoff.min():
        raise ValueError('Training overlaps calibration period')
    if (calibration.kickoff+pd.Timedelta(hours=8)).max() >= pd.Timestamp(evaluation_start):
        raise ValueError('Calibration overlaps evaluation period')
    p=base['pipeline'].predict_proba(calibration[base['features']])[:,1]
    methods={'sigmoid':LogisticRegression(C=1e6,random_state=42,max_iter=1000).fit(logit(p),calibration.target)}
    if len(calibration)>=min_games and len(np.unique(p))>=10:
        methods['isotonic']=IsotonicRegression(out_of_bounds='clip').fit(p,calibration.target)
    return methods

def paired_intervals(frame, replicates=2000, seed=42, confidence=.95, reference='logistic'):
    """Paired season-week cluster percentile bootstrap. Deltas: model minus reference.
    Higher accuracy is better; lower Brier/log-loss is better. Weeks are assumed
    independent; within-season persistence and only two recent seasons limit inference.
    """
    if replicates<2 or not 0<confidence<1:
        raise ValueError('Invalid bootstrap configuration')
    if frame.duplicated(['game_id','model']).any():
        raise ValueError('Duplicate model/game pairs')
    ids=frame[['game_id','season','week','target']].drop_duplicates()
    if ids.game_id.duplicated().any() or not ids.target.isin([0,1]).all():
        raise ValueError('Inconsistent game metadata or binary outcomes')
    wide=frame.pivot(index='game_id',columns='model',values='probability').reindex(ids.game_id)
    if wide.isna().any().any() or reference not in wide:
        raise ValueError('Models must use identical evaluation games')
    y=ids.target.to_numpy(dtype=int)
    cluster=pd.factorize(pd.MultiIndex.from_frame(ids[['season','week']]))[0]
    k=int(cluster.max()+1)
    rng=np.random.default_rng(seed)
    weights=rng.multinomial(k,np.full(k,1/k),size=replicates)
    counts=np.bincount(cluster,minlength=k)
    denominator=weights@counts
    alpha=(1-confidence)/2
    metrics={}; draws={}
    for name in wide:
        p=_probabilities(wide[name].to_numpy())
        losses={'accuracy':((p>=.5)==y).astype(float),'brier':(p-y)**2,
                'log_loss':-(y*np.log(np.clip(p,1e-6,1-1e-6))+(1-y)*np.log(np.clip(1-p,1e-6,1-1e-6)))}
        draws[name]={metric:(weights@np.bincount(cluster,weights=values,minlength=k))/denominator for metric,values in losses.items()}
        metrics[name]=evaluate(y,p)
    records=[]
    for name in wide:
        for metric in ['accuracy','brier','log_loss']:
            interval=np.quantile(draws[name][metric],[alpha,1-alpha])
            delta=draws[name][metric]-draws[reference][metric]
            low,high=np.quantile(delta,[alpha,1-alpha])
            records.append({'model':name,'metric':metric,'estimate':metrics[name][metric], 'low':float(interval[0]),'high':float(interval[1]),'difference':metrics[name][metric]-metrics[reference][metric], 'difference_low':float(low),'difference_high':float(high),'clusters':k,'games':len(ids),'confidence':confidence,'replicates':replicates,'reference':reference})
    return pd.DataFrame(records)

def validate_fold(frame,fold):
    a,b,c,d=[fold[k] for k in ['train_start','train_end','calibration','evaluation']]
    if not a<=b<c<d:
        raise ValueError('Fold must have train < calibration < evaluation')
    f=frame[frame.target.notna()]
    parts=[f[f.season.between(a,b)],f[f.season.eq(c)],f[f.season.eq(d)]]
    if any(x.empty for x in parts):
        raise ValueError(f'Missing required fold data: {fold}')
    for earlier,later in zip(parts,parts[1:]):
        if (earlier.kickoff+pd.Timedelta(hours=8)).max() >= later.kickoff.min():
            raise ValueError('Periods overlap in time')
    return parts

def error_slices(frame):
    f=frame.copy()
    f['home_outcome']=np.where(f.target.eq(1),'home_won','away_won')
    f['pick']=np.where(f.probability.ge(.5),'home_favored','away_favored')
    f['favorite_outcome']=np.where(f.probability.ge(.5).eq(f.target.eq(1)),'model_favorite_won','model_underdog_won')
    f['division']=np.where(f.home_team.map(TEAM_DIVISION).eq(f.away_team.map(TEAM_DIVISION)),'division','nondivision')
    f['phase']=np.where(f.week.le(4),'weeks_1_4','weeks_5_plus')
    f['recent_band']=pd.cut(f.recent_off_epa,[-np.inf,-.1,.1,np.inf],labels=['away_advantage','similar','home_advantage']).astype(str)
    f['probability_band']=pd.cut(f.probability,np.linspace(0,1,11),include_lowest=True).astype(str)
    out=[]
    for key in ['season','week','home_outcome','pick','favorite_outcome','division','recent_band','phase','probability_band']:
        for value,g in f.groupby(key):
            out.append({'dimension':key,'value':str(value),**evaluate(g.target,g.probability)})
    return pd.DataFrame(out)

def runtime_versions():
    from importlib.metadata import version
    import platform
    return {'python':platform.python_version(),**{name:version(name) for name in ['numpy','pandas','scikit-learn','polars','nflreadpy']}}

def fingerprint(frame,config):
    h=hashlib.sha256(json.dumps(config,sort_keys=True).encode())
    h.update(json.dumps(runtime_versions(),sort_keys=True).encode())
    h.update(pd.util.hash_pandas_object(frame,index=False).values.tobytes())
    h.update(str(list(frame.columns)).encode())
    for p in sorted(Path(__file__).parent.glob('*.py')):
        h.update(p.name.encode()); h.update(p.read_bytes())
    lock=Path(__file__).parents[1]/'requirements.lock.txt'
    if lock.exists(): h.update(lock.read_bytes())
    return h.hexdigest()

def run_analysis(frame,directory,config,source_metadata=None):
    directory=Path(directory)
    run_id=fingerprint(frame,{'protocol':config,'source_manifests':source_metadata or {}})
    final=directory/run_id[:16]
    if final.exists():
        manifest=json.loads((final/'outputs.json').read_text())
        if any(digest(final/name)!=sha for name,sha in manifest.items()):
            raise ValueError('Experiment artifact corrupted; preserve evidence and rerun in another output directory')
        atomic_json({'run':final.name},directory/'latest.json')
        return final
    import uuid
    stage=directory/('.staging-'+uuid.uuid4().hex); stage.mkdir(parents=True)
    records=[]; ablations=[]; ablation_predictions=[]; coefficients=[]; fold_metadata=[]; skipped=[]
    for fold in config['folds']:
        tr,cal,ev=validate_fold(frame,fold)
        base=train(tr)
        p=base['pipeline'].predict_proba(ev[FEATURES])[:,1]
        rate=float(tr.target.mean())
        probabilities={'logistic':p,'always_home':np.full(len(ev),max(.500001,rate)), 'historical_home_rate':np.full(len(ev),rate),'pregame_win_percentage':np.clip(.5+ev.win.fillna(0).to_numpy()/2,.05,.95)}
        methods=fit_calibrators(base,cal,ev.kickoff.min(),config['isotonic_min_games'])
        if 'isotonic' not in methods: skipped.append({'evaluation':fold['evaluation'],'method':'isotonic','reason':'Insufficient calibration size/distinct probabilities'})
        for name,method in methods.items():
            probabilities[name]=method.predict_proba(logit(p))[:,1] if name=='sigmoid' else method.predict(p)
        standardized=base['pipeline'][1].transform(base['pipeline'][0].transform(ev[FEATURES]))
        contributions=standardized*base['pipeline'][-1].coef_[0]
        for name,probs in probabilities.items():
            f=ev.copy(); f['model']=name; f['probability']=probs; f['correct']=f.target.eq(f.probability.ge(.5)); f['training_through']=fold['train_end']; f['calibration_season']=fold['calibration']; f['training_cutoff']=base['training_cutoff']
            if name=='logistic':
                for i,feature in enumerate(FEATURES): f['contribution_'+feature]=contributions[:,i]
                f['intercept']=float(base['pipeline'][-1].intercept_[0])
            records.append(f)
        full=evaluate(ev.target,p)
        for group,removed in GROUPS.items():
            features=[x for x in FEATURES if x not in removed]
            reduced=train(tr,features); reduced_p=reduced['pipeline'].predict_proba(ev[features])[:,1]; without=evaluate(ev.target,reduced_p)
            for name,probs in [('logistic',p),('without_'+group,reduced_p)]:
                trial=ev[['game_id','season','week','target']].copy(); trial['model']=name; trial['probability']=probs; trial['group']=group; ablation_predictions.append(trial)
            ablations.append({'group':group,'evaluation':fold['evaluation'],'train_end':fold['train_end'],'features_without':json.dumps(features),**{'full_'+k:v for k,v in full.items()},**{'without_'+k:v for k,v in without.items()},'brier_contribution':without['brier']-full['brier'],'accuracy_contribution':full['accuracy']-without['accuracy'],'log_loss_contribution':without['log_loss']-full['log_loss']})
        for name,coefficient in zip(FEATURES,base['pipeline'][-1].coef_[0]):
            coefficients.append({'evaluation':fold['evaluation'],'feature':name,'standardized_coefficient':float(coefficient)})
        fold_metadata.append({**fold,'training_cutoff':base['training_cutoff'],'calibration_cutoff':(cal.kickoff.max()+pd.Timedelta(hours=8)).isoformat(),'evaluation_start':ev.kickoff.min().isoformat(),'evaluation_end':ev.kickoff.max().isoformat(),'train_games':len(tr),'calibration_games':len(cal),'evaluation_games':len(ev),'features':FEATURES})
    predictions=pd.concat(records,ignore_index=True)
    if predictions.duplicated(['game_id','model']).any(): raise ValueError('Evaluation folds overlap')
    predictions.to_parquet(stage/'predictions.parquet',index=False)
    comparison=[]; calibration=[]; bands=[]
    for period,f in [('all_exploratory',predictions),('examined_2024_2025',predictions[predictions.season.isin([2024,2025])])]+[(str(y),predictions[predictions.season.eq(y)]) for y in sorted(predictions.season.unique())]:
        if f.empty: continue
        intervals=paired_intervals(f,config['bootstrap_replicates'],config['seed'],config['confidence_level'])
        intervals['period']=period; comparison.append(intervals)
        for name,g in f.groupby('model'):
            calibration.append({'period':period,'model':name,**calibration_diagnostic(g.target,g.probability)})
            b=buckets(g.target,g.probability); b['model']=name; b['period']=period; bands.append(b)
    pd.concat(comparison).to_csv(stage/'comparison.csv',index=False)
    pd.DataFrame(calibration).to_csv(stage/'calibration.csv',index=False)
    pd.concat(bands).to_csv(stage/'probability_buckets.csv',index=False)
    abl=pd.DataFrame(ablations); abl.to_csv(stage/'ablations.csv',index=False)
    ranking=abl.groupby('group').agg(mean_brier_contribution=('brier_contribution','mean'),positive_seasons=('brier_contribution',lambda v:int((v>0).sum())),seasons=('evaluation','size'),mean_accuracy_contribution=('accuracy_contribution','mean'),mean_log_loss_contribution=('log_loss_contribution','mean')).sort_values('mean_brier_contribution',ascending=False)
    ranking.to_csv(stage/'feature_ranking.csv')
    ablation_intervals=[]
    for group,g in pd.concat(ablation_predictions).groupby('group'):
        ci=paired_intervals(g,config['bootstrap_replicates'],config['seed'],config['confidence_level']); ci['group']=group; ablation_intervals.append(ci)
    pd.concat(ablation_intervals).to_csv(stage/'ablation_uncertainty.csv',index=False)
    tr[FEATURES].corr().to_csv(stage/'training_feature_correlations.csv')
    pd.DataFrame(coefficients).to_csv(stage/'coefficients.csv',index=False)
    champion=predictions[predictions.model.eq('logistic')]
    error_slices(champion).to_csv(stage/'error_slices.csv',index=False)
    champion[~champion.correct].to_csv(stage/'incorrect_predictions.csv',index=False)
    buckets(champion.target,champion.probability,True).to_csv(stage/'confidence_buckets.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots()
    reliability_sample=predictions[predictions.season.isin([2024,2025])]
    if reliability_sample.empty: reliability_sample=predictions
    for name,g in reliability_sample.groupby('model'):
        b=buckets(g.target,g.probability); ax.plot(b.predicted,b.observed,'o-',label=name)
    ax.plot([0,1],[0,1],'k--'); ax.set(xlabel='Mean predicted home-win probability',ylabel='Observed home-win frequency',title='Exploratory reliability, previously examined 2024–2025'); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(stage/'reliability.png'); plt.close(fig)
    try:
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).parents[1],text=True).strip()
    except (OSError,subprocess.CalledProcessError): commit='unavailable'
    metadata={'run_id':run_id,'source_manifests':source_metadata or {},'protocol':config,'folds':fold_metadata,'code_commit':commit,'code_and_data_fingerprint':run_id,'data_fingerprint':hashlib.sha256(pd.util.hash_pandas_object(frame,index=False).values.tobytes()).hexdigest(),'module_hashes':{p.name:digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))},'preprocessing':'training-only mean imputation (all-empty=0), StandardScaler, L2 logistic C=1 max_iter=1000 seed=42','sigmoid':'logit(p) logistic C=1e6 fitted only calibration year','isotonic':'calibration-year predictions, out_of_bounds=clip','skipped':skipped,'runtime_versions':runtime_versions(),'status':'exploratory; no champion promotion','interval_method':'paired season-week cluster percentile bootstrap; unadjusted 95% intervals, no multiplicity correction; correlated weeks and few seasons limit inference','data_max_kickoff':frame.kickoff.max().isoformat()}
    atomic_json(metadata,stage/'metadata.json')
    from .reporting import write_reports
    write_reports(stage,predictions,metadata)
    atomic_json({p.name:digest(p) for p in stage.iterdir()},stage/'outputs.json')
    stage.rename(final)
    atomic_json({'run':final.name},directory/'latest.json')
    return final
