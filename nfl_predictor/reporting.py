"""Human-readable reports from measured, aligned experiment outputs."""
import json
import numpy as np
import pandas as pd

def table(frame):
    def cell(v):
        if isinstance(v,float): return f'{v:.6f}'
        return str(v).replace('|','/').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(map(str,frame.columns))+' |','| '+' | '.join(['---']*len(frame.columns))+' |']+['| '+' | '.join(map(cell,row))+' |' for row in frame.itertuples(index=False,name=None)])

def season_gap(predictions,replicates=2000,seed=42):
    rng=np.random.default_rng(seed); draws={}; observed={}
    for year in [2024,2025]:
        f=predictions[predictions.model.eq('logistic')&predictions.season.eq(year)]
        if f.empty: return None
        g=f.assign(correct=f.probability.ge(.5).eq(f.target.eq(1)).astype(float)).groupby('week').agg(total=('target','size'),correct=('correct','sum'))
        weights=rng.multinomial(len(g),np.full(len(g),1/len(g)),size=replicates)
        draws[year]=(weights@g.correct.to_numpy())/(weights@g.total.to_numpy())
        observed[year]=float(g.correct.sum()/g.total.sum())
    delta=draws[2024]-draws[2025]
    return {'accuracy_2024':observed[2024],'accuracy_2025':observed[2025],'difference_2024_minus_2025':observed[2024]-observed[2025],'low':float(np.quantile(delta,.025)),'high':float(np.quantile(delta,.975)),'method':'Independent within-season week-block percentile bootstrap; descriptive 95% interval, two seasons only'}

def write_reports(directory,predictions,metadata):
    compare=pd.read_csv(directory/'comparison.csv')
    period='examined_2024_2025' if compare.period.eq('examined_2024_2025').any() else 'all_exploratory'
    recent=compare[compare.period.eq(period)]
    columns=['model','metric','estimate','low','high','difference','difference_low','difference_high','games']
    (directory/'MODEL_COMPARISON.md').write_text('# Exploratory model comparison\n\n'+period+'\n\n'+table(recent[columns])+'\n\nDifferences are model minus uncalibrated logistic. Positive accuracy and negative Brier/log-loss favor the candidate. Intervals use identical resampled season-week clusters for each model. They are unadjusted for multiplicity, rely on independence across weeks, and do not capture all repeated-team dependence. No superiority claim or champion promotion is made. The 2024–2025 results were already inspected in M1 and are not an untouched confirmation set.\n')
    rank=pd.read_csv(directory/'feature_ranking.csv')
    (directory/'FEATURE_ABLATION.md').write_text('# Feature ablation\n\n'+table(rank)+'\n\nPositive Brier contribution means that removing the group worsened Brier score. These are exploratory equal-season means over the configured forward folds. Full and reduced models use identical games and training-only preprocessing. See ablations.csv for each fold and ablation_uncertainty.csv for paired cluster intervals (reduced minus full).\n\nThe standardized coefficients are descriptive conditional associations, not causal effects. EPA, success, yards, scoring and win percentage are correlated; removal effects depend on which related features remain. training_feature_correlations.csv records training-period pairwise correlations. No features were deleted and the champion is unchanged.\n')
    calibration=pd.read_csv(directory/'calibration.csv')
    (directory/'CALIBRATION.md').write_text('# Chronological calibration\n\nEach base estimator is fitted before the calibration year. Sigmoid fits a logistic map of logit probabilities on that year only. Isotonic requires at least the configured calibration game count and ten distinct probabilities. Neither method sees evaluation-period outcomes during fitting.\n\n'+table(calibration[calibration.period.eq(period)])+'\n\nDiagnostic intercept/slope are fitted on evaluation outcomes solely for assessment (ideal 0/1); they are not deployed. They can be unstable in small or separated samples. Buckets and reliability.png use out-of-period predictions. Compare Brier and log-loss intervals in MODEL_COMPARISON.md before considering calibration. No automatic promotion is supported.\n')
    gap=season_gap(predictions,metadata['protocol']['bootstrap_replicates'],metadata['protocol']['seed'])
    (directory/'season_gap.json').write_text(json.dumps(gap,indent=2))
    g=predictions[predictions.model.eq('logistic')]
    season=g.groupby('season').agg(games=('target','size'),accuracy=('correct','mean'),mean_home_probability=('probability','mean'),observed_home_wins=('target','mean'))
    (directory/'ERROR_ANALYSIS.md').write_text('# Historical error analysis\n\n'+table(season.reset_index())+'\n\n2024 minus 2025 accuracy, with independent week resampling: '+json.dumps(gap)+'.\n\nThe observed seasonal difference alone does not identify a cause. Sampling variation, changing schedule composition, strength volatility and calibration can all contribute. Only two recent seasons are available. Intervals are descriptive and do not establish a football mechanism. Inspect season calibration and error_slices.csv before advancing a hypothesis.\n\nSlices cover season, week, actual home/away winner, model favorite/underdog outcome, probability, division matchup (documented current franchise mapping), recent offensive EPA difference and weeks 1–4 versus 5+. These overlapping post-hoc groups do not constitute independent significance tests.\n\nDownload incorrect_predictions.csv from Model Analysis. It includes original pregame features, predicted probability and standardized feature × coefficient contributions to home-win log odds, plus the intercept. Contributions explain the linear score, not causal responsibility for an error.\n')
