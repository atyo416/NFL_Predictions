from datetime import datetime,timezone
import pandas as pd
from .feature_engineering import build, FEATURES
from .database import insert

def predict(schedules,metrics,model,db,cutoff=None):
    now=pd.Timestamp(datetime.now(timezone.utc))
    cutoff=pd.Timestamp(cutoff) if cutoff is not None else now
    if cutoff.tzinfo is None or cutoff>now:
        raise ValueError('Cutoff must be timezone aware and cannot be in the future')
    upcoming=schedules[schedules.season.eq(2026) & ~schedules.completed & schedules.kickoff.gt(now) & schedules.kickoff.gt(cutoff)]
    if not len(upcoming):
        return pd.DataFrame()
    # Preserve all history when computing only upcoming feature rows.
    f=build(schedules,metrics,cutoff,game_ids=upcoming.game_id)
    f=f[f.game_id.isin(upcoming.game_id)]
    if pd.Timestamp(model['training_cutoff']) >= cutoff:
        raise ValueError('Model training cutoff must precede prediction cutoff')
    probabilities=model['pipeline'].predict_proba(f[FEATURES])[:,1]
    records=[]
    for (_,g),p in zip(f.iterrows(),probabilities):
        record={'game_id':g.game_id,'season':int(g.season),'week':int(g.week),'home_team':g.home_team,'away_team':g.away_team,'kickoff':g.kickoff.isoformat(),'home_probability':float(p),'away_probability':float(1-p),'predicted_winner':g.home_team if p>=.5 else g.away_team,'model_version':model['version'],'created_at':now.isoformat(),'data_cutoff':cutoff.isoformat()}
        record['official']=bool(insert(db,record)); records.append(record)
    return pd.DataFrame(records)
