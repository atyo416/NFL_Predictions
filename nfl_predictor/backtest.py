import json
from pathlib import Path
import numpy as np
import pandas as pd
from .model import train
from .feature_engineering import FEATURES
from .evaluation import evaluate,buckets

def run(frame, directory):
    directory = Path(directory); directory.mkdir(parents=True,exist_ok=True)
    eligible = frame[frame.target.notna()].copy()
    tr = eligible[eligible.season.between(2018,2022)]
    model = train(tr)
    report = {'training':[2018,2022],'validation':[2023],'held_out':[2024,2025], 'features':FEATURES,'ties':int((frame.completed & frame.target.isna()).sum()),'fixed':{},'walk_forward':{}}
    predictions = []
    for name,years in [('validation',[2023]),('test',[2024,2025])]:
        f = eligible[eligible.season.isin(years)].copy()
        if f.empty:
            raise ValueError(f'Missing required {name} data: {years}')
        p = model['pipeline'].predict_proba(f[FEATURES])[:,1]
        rate = float(tr.target.mean())
        report['fixed'][name] = {'logistic':evaluate(f.target,p),'home_pick':evaluate(f.target,np.full(len(f),max(.500001,rate))),'training_rate':evaluate(f.target,np.full(len(f),rate)), 'pregame_win_percentage':evaluate(f.target,np.clip(.5+f.win.fillna(0).to_numpy()/2,.05,.95))}
        f['probability']=p; f['evaluation']=name; predictions.append(f)
        buckets(f.target,p).to_csv(directory/f'{name}_calibration.csv',index=False)
        buckets(f.target,p,True).to_csv(directory/f'{name}_confidence.csv',index=False)
        report['fixed'][name]['seasons'] = {str(int(y)):evaluate(f.loc[f.season.eq(y),'target'],p[f.season.eq(y)]) for y in years}
    for year in [2023,2024,2025]:
        t = eligible[eligible.season.between(2018,year-1)]
        f = eligible[eligible.season.eq(year)].copy()
        m = train(t)
        p = m['pipeline'].predict_proba(f[FEATURES])[:,1]
        report['walk_forward'][str(year)] = {'training_through':year-1,**evaluate(f.target,p)}
        f['probability']=p; f['evaluation']='walk_forward'; predictions.append(f)
    pd.concat(predictions).to_parquet(directory/'historical_predictions.parquet',index=False)
    (directory/'backtest.json').write_text(json.dumps(report,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    b = pd.read_csv(directory/'test_calibration.csv')
    fig,ax=plt.subplots(); ax.plot([0,1],[0,1],'--'); ax.plot(b.predicted,b.observed,'o-'); ax.set(xlabel='Predicted home win probability',ylabel='Observed home win frequency',title='Held-out reliability'); fig.savefig(directory/'reliability.png'); plt.close(fig)
    return report
