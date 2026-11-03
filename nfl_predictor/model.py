from datetime import datetime, timezone
from pathlib import Path
import uuid
import joblib
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from .feature_engineering import FEATURES

def train(frame, features=None):
    features = FEATURES if features is None else list(features)
    f = frame[frame.target.notna()].copy()
    if f.empty or f.target.nunique() < 2:
        raise ValueError('Training requires completed non-tie games and both outcome classes')
    pipe = make_pipeline(SimpleImputer(strategy='mean',keep_empty_features=True),StandardScaler(),LogisticRegression(C=1.,random_state=42,max_iter=1000))
    pipe.fit(f[features],f.target.astype(int))
    return {'pipeline':pipe,'version':datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8], 'features':features,'training_seasons': sorted(f.season.unique().tolist()),'training_cutoff':(f.kickoff.max() + pd.Timedelta(hours=8)).isoformat()}

def save(model,path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,path)

def load(path):
    return joblib.load(path)
