import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

def evaluate(y,p):
    y,p = np.asarray(y,dtype=int), np.asarray(p,dtype=float)
    if not len(y):
        raise ValueError('No binary games to evaluate')
    return {'games':len(y),'accuracy':accuracy_score(y,p>=.5),'brier':brier_score_loss(y,p),'log_loss':log_loss(y,np.clip(p,1e-6,1-1e-6),labels=[0,1]),'home_win_rate':float(y.mean())}

def buckets(y,p,confidence=False):
    f = pd.DataFrame({'actual':np.asarray(y),'probability':np.asarray(p)})
    if confidence:
        f['actual'] = (f.actual.eq(f.probability.ge(.5))).astype(int)
        f['probability'] = np.maximum(f.probability,1-f.probability)
    f['bucket'] = pd.cut(f.probability,np.linspace(0,1,11),include_lowest=True)
    return f.groupby('bucket',observed=True).agg(games=('actual','size'),predicted=('probability','mean'),observed=('actual','mean')).reset_index().astype({'bucket':str})
