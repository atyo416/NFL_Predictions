"""Cutoff-relative normalized weights; weighted scaler and estimators, never resampling."""
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from .boosting import fit_boosting,check_features
from .history_features import COMMON


def decay_weights(kickoffs,cutoff,half_life=None,normalize=True):
    cutoff=pd.Timestamp(cutoff)
    times=pd.Series(pd.to_datetime(kickoffs))
    if cutoff.tzinfo is None or times.dt.tz is None:raise ValueError('Decay cutoff and game times must be timezone aware')
    age=(cutoff-times).dt.total_seconds().to_numpy()/(365.25*86400)
    if not np.isfinite(age).all() or (age<0).any():raise ValueError('Training contains a future game relative to decay cutoff')
    if half_life is not None and (not np.isfinite(half_life) or half_life<=0):raise ValueError('Half-life must be positive')
    w=np.ones(len(times)) if half_life is None else np.power(.5,age/half_life)
    if not len(w):raise ValueError('No training games for sample weighting')
    return w/w.mean() if normalize else w

def fit_history(frame,algorithm,config,half_life=None,features=None):
    f=frame[frame.target.notna()].copy()
    if f.empty or f.target.nunique()!=2:raise ValueError('Historical training needs both binary classes')
    features=list(features or (COMMON if algorithm=='logistic' else COMMON+['elo_difference']))
    cutoff=f.kickoff.max()+pd.Timedelta(hours=8)
    # date-only source rows carry a deliberately later availability upper bound.
    if 'result_available_at' in f:
        actual=pd.to_datetime(f.result_available_at,utc=True)
        if actual.notna().any():cutoff=max(cutoff,actual.max())
    weights=decay_weights(f.kickoff,cutoff,half_life)
    if algorithm=='hgb':
        model=fit_boosting(f,features,config['hgb_parameters'],config['cpu_threads'],sample_weight=weights)
    elif algorithm=='logistic':
        x=check_features(f,features)
        pipeline=make_pipeline(SimpleImputer(strategy='mean',keep_empty_features=True),StandardScaler(),LogisticRegression(C=1.,max_iter=1000,random_state=42))
        with threadpool_limits(limits=config['cpu_threads']):
            pipeline.fit(x,f.target.astype(int),standardscaler__sample_weight=weights,logisticregression__sample_weight=weights)
        identity=hashlib.sha256(pd.util.hash_pandas_object(f[features+['target']],index=False).values.tobytes()+weights.tobytes()).hexdigest()
        model={'pipeline':pipeline,'version':'weighted-logistic-'+identity[:16],'features':features,'hyperparameters':{'C':1.0,'penalty':'L2','random_state':42,'max_iter':1000},'algorithm':'LogisticRegression','dataset_fingerprint':identity,'calibration':None}
    else:raise ValueError('Only existing logistic and shallow HGB algorithms are permitted')
    model.update({'training_cutoff':cutoff.isoformat(),'training_seasons':sorted(f.season.unique().tolist()),'feature_schema':'m5-v1','activation_blocked':True,'earliest_training_season':int(f.season.min()),'weighting':{'policy':'uniform' if half_life is None else 'exponential','half_life_years':half_life,'reference_cutoff':cutoff.isoformat(),'normalization':'mean_one','minimum':float(weights.min()),'maximum':float(weights.max()),'sum':float(weights.sum()),'effective_sample_size':float(weights.sum()**2/(weights@weights)),'preprocessing':'Training-only unweighted mean imputation; weighted StandardScaler and logistic loss' if algorithm=='logistic' else 'Weighted native HGB fit; no resampling or random early stopping'}})
    return model

from dataclasses import dataclass
from .analysis import logit
@dataclass
class LogisticCalibrator:
    pipeline: object
    method: str
    calibrator: object
    def predict_proba(self,frame):
        p=self.pipeline.predict_proba(frame)[:,1]
        calibrated=self.calibrator.predict_proba(logit(p))[:,1] if self.method=='sigmoid' else self.calibrator.predict(p)
        return np.column_stack([1-calibrated,calibrated])
