"""Small predefined ensemble policies. All learned inputs must be chronological OOS."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression

BASES=['logistic','boosting','elo_margin']
PROBABILITIES=['p_'+name for name in BASES]
CLASSIFICATION='retrospective_chronological_out_of_sample'


def timestamp(value):
    stamp=pd.Timestamp(value)
    if pd.isna(stamp) or stamp.tzinfo is None:
        raise ValueError('An explicit timezone-aware timestamp is required')
    return stamp.tz_convert('UTC')


def probability_matrix(frame):
    if set(PROBABILITIES)-set(frame):raise ValueError('Missing base probability columns')
    x=frame[PROBABILITIES].to_numpy(dtype=float)
    if not np.isfinite(x).all() or ((x<0)|(x>1)).any():
        raise ValueError('Missing or invalid base probabilities; never substitute 0.5')
    return x


def validate_matrix(frame, require_labels=False):
    required={'game_id','season','week','kickoff','data_cutoff','available_at','target','classification'}
    required.update('training_cutoff_'+name for name in BASES)
    if required-set(frame):raise ValueError(f'Missing prediction provenance: {sorted(required-set(frame))}')
    if frame.game_id.isna().any() or frame.game_id.duplicated().any():raise ValueError('Duplicate or missing prediction game IDs')
    kickoff=pd.to_datetime(frame.kickoff,utc=True);cutoff=pd.to_datetime(frame.data_cutoff,utc=True)
    if any(timestamp(v)>timestamp(k) for v,k in zip(frame.data_cutoff,frame.kickoff)):
        raise ValueError('Feature cutoff follows kickoff')
    if kickoff.isna().any() or cutoff.isna().any():raise ValueError('Missing feature/kickoff times')
    for value in frame.available_at.dropna():timestamp(value)
    available=pd.to_datetime(frame.available_at,utc=True)
    if (available.notna()&available.lt(kickoff)).any():raise ValueError('Result availability precedes kickoff')
    if not frame.classification.eq(CLASSIFICATION).all():raise ValueError('Meta inputs must be chronological out-of-sample predictions')
    for name in BASES:
        training=pd.Series([timestamp(v) for v in frame['training_cutoff_'+name]],index=frame.index)
        if (training>=cutoff).any():raise ValueError('In-sample base prediction or training cutoff overlap')
    if not frame.target.dropna().isin([0,1]).all():raise ValueError('Ties and incomplete outcomes are not binary labels')
    if require_labels and frame.target.isna().any():raise ValueError('Incomplete labels cannot fit or evaluate an ensemble')
    probability_matrix(frame)
    return frame


def weights_array(weights):
    w=np.asarray(weights,dtype=float)
    if w.shape!=(3,) or not np.isfinite(w).all() or (w<0).any() or not np.isclose(w.sum(),1,atol=1e-10):
        raise ValueError('Three nonnegative weights must sum to one')
    return w


def transform(x,representation,clip=1e-6):
    if representation=='probabilities':return x
    if representation!='logits' or not 0<clip<.5:raise ValueError('Invalid stacking representation or log-odds clipping')
    p=np.clip(x,clip,1-clip)
    return np.log(p/(1-p))


@dataclass
class EnsemblePredictor:
    method: str
    weights: object=None
    estimator: object=None
    representation: str='probabilities'
    clip: float=1e-6
    calibration_method: str='raw'
    calibrator: object=None

    def predict_proba(self,frame):
        x=probability_matrix(frame)
        p=x@weights_array(self.weights) if self.weights is not None else self.estimator.predict_proba(transform(x,self.representation,self.clip))[:,1]
        if self.calibrator is not None:
            p=self.calibrator.predict_proba(transform(np.asarray(p).reshape(-1,1),'logits',self.clip))[:,1] if self.calibration_method=='sigmoid' else self.calibrator.predict(p)
        if not np.isfinite(p).all() or ((p<0)|(p>1)).any():raise ValueError('Invalid ensemble output probability')
        return np.column_stack([1-p,p])


def fit_policies(meta,cutoff,config):
    """Caller supplies OOS rows; reject eligibility overlap even for fixed policies."""
    validate_matrix(meta,True);cutoff=timestamp(cutoff)
    if len(meta)<config['minimum_meta_games'] or meta.season.nunique()<config['minimum_meta_seasons'] or meta.target.nunique()!=2:
        raise ValueError('Insufficient chronological OOS meta-training games/seasons/classes')
    if pd.to_datetime(meta.available_at,utc=True).isna().any() or (pd.to_datetime(meta.available_at,utc=True)>=cutoff).any():
        raise ValueError('Meta-training outcomes overlap calibration/evaluation cutoff')
    x=probability_matrix(meta);y=meta.target.to_numpy(dtype=int)
    policies={name:EnsemblePredictor(name,weights_array(w)) for name,w in config['fixed_weights'].items()}
    prior=weights_array(config['weight_prior']);penalty=config['weight_penalty']
    if penalty<0:raise ValueError('Weight shrinkage must be nonnegative')
    objective=lambda w:np.mean((x@w-y)**2)+penalty*np.sum((w-prior)**2)
    jac=lambda w:2*x.T@(x@w-y)/len(y)+2*penalty*(w-prior)
    fit=minimize(objective,prior,jac=jac,method='SLSQP',bounds=[(0,1)]*3,
                 constraints={'type':'eq','fun':lambda w:w.sum()-1,'jac':lambda w:np.ones(3)},
                 options={'ftol':1e-12,'maxiter':500})
    if not fit.success:raise ValueError(f'Constrained weight optimization failed: {fit.message}')
    policies['E4_optimized']=EnsemblePredictor('E4_optimized',weights_array(fit.x))
    diagnostics={'optimizer':'SLSQP','success':bool(fit.success),'iterations':int(fit.nit),'objective':float(fit.fun),'weights':fit.x.tolist(),'prior':prior.tolist(),'penalty':penalty}
    for representation in ['probabilities','logits']:
        estimator=LogisticRegression(C=config['stack_C'],random_state=config['seed'],max_iter=1000)
        estimator.fit(transform(x,representation,config['logit_clip']),y)
        name='E5_'+representation;policies[name]=EnsemblePredictor(name,estimator=estimator,representation=representation,clip=config['logit_clip'])
    return policies,diagnostics


def calibrated_policies(raw,calibration,evaluation_start,config,meta_cutoff):
    from copy import deepcopy
    validate_matrix(calibration,True);evaluation_start=timestamp(evaluation_start)
    if calibration.empty or calibration.target.nunique()!=2:raise ValueError('Calibration requires both binary classes')
    if timestamp(meta_cutoff)>=calibration.data_cutoff.min():raise ValueError('Meta-training overlaps calibration predictions')
    times=pd.to_datetime(calibration.available_at,utc=True)
    if times.isna().any() or (times>=evaluation_start).any():raise ValueError('Calibration outcomes overlap evaluation')
    result={};skipped=[]
    for name,policy in raw.items():
        result[name+'__raw']=policy;p=policy.predict_proba(calibration)[:,1]
        methods={'sigmoid':LogisticRegression(C=1e6,random_state=config['seed'],max_iter=1000).fit(transform(p.reshape(-1,1),'logits',config['logit_clip']),calibration.target)}
        if len(calibration)>=config['isotonic_min_games'] and len(np.unique(p))>=10:
            methods['isotonic']=IsotonicRegression(out_of_bounds='clip').fit(p,calibration.target)
        else:skipped.append({'model':name+'__isotonic','reason':'Insufficient calibration games or distinct scores'})
        for method,calibrator in methods.items():
            policy_copy=deepcopy(policy);policy_copy.calibration_method=method;policy_copy.calibrator=calibrator
            result[name+'__'+method]=policy_copy
    return result,skipped


def policy_parameters(policy):
    return {'method':policy.method,'weights':None if policy.weights is None else np.asarray(policy.weights).tolist(),
            'representation':policy.representation,'coefficients':None if policy.estimator is None else policy.estimator.coef_.tolist(),
            'intercept':None if policy.estimator is None else policy.estimator.intercept_.tolist(),
            'calibration_method':policy.calibration_method}
