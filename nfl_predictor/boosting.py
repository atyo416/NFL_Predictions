"""Deterministic small-data CPU boosting with native missing-value handling."""
from dataclasses import dataclass
import hashlib
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits
from .analysis import logit

FORBIDDEN={'target','home_score','away_score','result','home_qb_id','away_qb_id','qb_change_difference'}
PARAMETERS={'learning_rate','max_leaf_nodes','max_depth','max_iter','min_samples_leaf','l2_regularization'}

def check_features(frame,features):
    if not features or len(features)!=len(set(features)) or set(features)&FORBIDDEN:
        raise ValueError('Unsafe or duplicate feature specification')
    missing=set(features)-set(frame)
    if missing: raise ValueError(f'Missing required model features: {sorted(missing)}')
    x=frame[features].astype(float)
    if np.isinf(x.to_numpy()).any():raise ValueError('Infinite model features are invalid; NaN missing values are supported')
    return x

@dataclass
class BoundedPredictor:
    """Bound OpenMP on both fitting and later scoring (including joblib reloads)."""
    estimator: object
    features: list
    threads: int=2
    calibrator: object=None
    calibration_method: str=None
    active_features: list=None

    def predict_proba(self,frame):
        x=check_features(frame,self.features)
        if self.active_features is not None:
            x=x[self.active_features]
            if not self.active_features:x=pd.DataFrame({'__training_intercept__':np.zeros(len(frame))},index=frame.index)
        with threadpool_limits(limits=self.threads):
            p=self.estimator.predict_proba(x)[:,1]
            if self.calibrator is not None:
                p=self.calibrator.predict_proba(logit(p))[:,1] if self.calibration_method=='sigmoid' else self.calibrator.predict(p)
        p=np.asarray(p,dtype=float)
        if not np.isfinite(p).all() or ((p<0)|(p>1)).any():raise ValueError('Invalid model probabilities')
        return np.column_stack([1-p,p])

def fit_boosting(frame,features,parameters,threads=2,sample_weight=None):
    if set(parameters)-PARAMETERS:raise ValueError('Unsupported parameters; internal/random early stopping is prohibited')
    if threads<1:raise ValueError('CPU thread count must be positive')
    f=frame[frame.target.notna()].copy()
    if f.empty or f.target.nunique()!=2 or not f.target.isin([0,1]).all():raise ValueError('Training requires both binary outcome classes')
    if f.kickoff.dt.tz is None:raise ValueError('Training kickoff must be timezone aware')
    if 'data_cutoff' in f and (f.data_cutoff>f.kickoff).any():raise ValueError('Feature cutoff after kickoff')
    weights=None
    if sample_weight is not None:
        weights=np.asarray(sample_weight,dtype=float)
        if weights.shape!=(len(frame),) or not np.isfinite(weights).all() or (weights<=0).any():raise ValueError('Sample weights must be positive finite values aligned to the training frame')
        weights=weights[frame.target.notna().to_numpy()]
    x=check_features(f,features)
    # sklearn 1.9's binning fails on entirely missing columns. Exclude them
    # based only on training rows; never learn replacement values from later data.
    active_features=[name for name in features if x[name].notna().any()]
    x=x[active_features]
    if not active_features:x=pd.DataFrame({'__training_intercept__':np.zeros(len(f))},index=f.index)
    estimator=HistGradientBoostingClassifier(loss='log_loss',early_stopping=False,random_state=42,**parameters)
    with threadpool_limits(limits=threads):estimator.fit(x,f.target.astype(int),sample_weight=weights)
    cutoff=(f.kickoff.max()+pd.Timedelta(hours=8)).isoformat()
    identity=hashlib.sha256(pd.util.hash_pandas_object(f[features+['target']],index=False).values.tobytes()+json.dumps({'features':features,'parameters':parameters,'cutoff':cutoff},sort_keys=True).encode()).hexdigest()
    if weights is not None:identity=hashlib.sha256(identity.encode()+weights.tobytes()).hexdigest()
    return {'pipeline':BoundedPredictor(estimator,list(features),threads,active_features=active_features),'version':'hgb-'+identity[:20],'excluded_all_missing_features':[c for c in features if c not in active_features],'algorithm':'HistGradientBoostingClassifier','feature_schema':'m4-v1','features':list(features),'hyperparameters':{**parameters,'loss':'log_loss','early_stopping':False,'random_state':42},'training_cutoff':cutoff,'training_seasons':sorted(f.season.unique().tolist()),'dataset_fingerprint':identity,'calibration':None}

def calibrated(base,method,calibrator,calibration_frame):
    result={k:v for k,v in base.items() if k!='pipeline'}
    p=base['pipeline']
    result['pipeline']=BoundedPredictor(p.estimator,p.features,p.threads,calibrator,method,p.active_features)
    result['version']=base['version']+'-'+method
    result['calibration']={'method':method,'seasons':sorted(calibration_frame.season.unique().tolist()),'cutoff':(calibration_frame.kickoff.max()+pd.Timedelta(hours=8)).isoformat(),'games':len(calibration_frame)}
    # Both model fitting AND calibration labels must precede a genuine issuance cutoff.
    result['training_cutoff']=result['calibration']['cutoff']
    return result
