"""Coverage diagnostics; absent metrics remain missing, never zero-filled."""
import warnings
import pandas as pd

def coverage(schedules,metrics):
    eligible=schedules[schedules.completed & (schedules.kickoff+pd.Timedelta(hours=8)).lt(pd.Timestamp.now(tz='UTC'))]
    missing=[]
    for side in ['home','away']:
        joined=eligible.merge(metrics,left_on=['game_id',side+'_team'],right_on=['game_id','team'],how='left')
        missing.extend(joined.loc[joined.off_epa.isna(),'game_id'].tolist())
    missing=sorted(set(missing))
    if missing:
        warnings.warn(f'Missing eligible play-by-play metrics for {len(missing)} games: {missing[:10]}; refresh source. Metrics remain NaN.',stacklevel=2)
    if 'off_plays' in metrics:
        low = metrics[metrics.off_plays.lt(40)]
        if len(low):
            warnings.warn(f'{len(low)} team-games have fewer than 40 eligible scrimmage plays; review for partial play-by-play (not proof of incompleteness).',stacklevel=2)
    return {'missing_metric_games':missing,'regular_season_games':len(schedules),'completed_games':int(schedules.completed.sum())}
