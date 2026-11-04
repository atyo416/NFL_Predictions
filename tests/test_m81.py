from pathlib import Path
import json
import pandas as pd
import numpy as np
import pytest
from nfl_predictor.historical_market import prepare,generate
from nfl_predictor.ensemble import BASES,CLASSIFICATION
from nfl_predictor.analysis import paired_intervals
from nfl_predictor.integrity import digest


def inputs():
    s=pd.DataFrame({'game_id':['a','b','tie','future'],'season':[2024,2025,2025,2025],'week':[1,1,2,3],
        'game_type':'REG','home_team':['LV','BUF','LV','BAL'],'away_team':['KC','MIA','KC','CIN'],
        'kickoff':pd.to_datetime(['2024-09-01T17:00Z','2025-09-01T17:00Z','2025-09-08T17:00Z','2025-09-15T17:00Z']),
        'home_score':[24,10,17,np.nan],'away_score':[17,17,17,np.nan],'completed':[True,True,True,False],
        'home_moneyline':[150,-150,-110,200],'away_moneyline':[-170,130,-110,-240]})
    b=s.iloc[:2][['game_id','season','week','kickoff','home_team','away_team']].copy()
    b['target']=[1,0];b['data_cutoff']=b.kickoff;b['available_at']=b.kickoff+pd.Timedelta(hours=8);b['classification']=CLASSIFICATION
    for name in BASES:b['training_cutoff_'+name]=pd.to_datetime(b.season.astype(str)+'-02-01',utc=True)
    b['p_logistic']=[.6,.4];b['p_boosting']=[.55,.45];b['p_elo_margin']=[.7,.3]
    e=b[['game_id','season','week','target']].copy();e['probability']=[.62,.38]
    return s,b,e


def test_two_sided_reference_uses_existing_moneyline_math():
    s,b,e=inputs();groups,audit=prepare(s,b,e,'2024-01-01T00:00Z')
    market=groups['all_base_history'].query("model=='closing_market'").set_index('game_id')
    assert market.loc['a','probability']==pytest.approx(.4/(.4+170/270))
    assert market.loc['b','probability']==pytest.approx(.6/(.6+100/230))
    assert audit['ties_excluded']==1 and audit['incomplete_scores']==1
    assert audit['source_classification']=='historical_closing_reference'


def test_missing_invalid_odds_and_absent_pair_columns_are_excluded():
    s,b,e=inputs();s.loc[0,'home_moneyline']=np.nan;s.loc[1,'away_moneyline']=0
    groups,audit=prepare(s,b)
    assert audit['missing_closing_pair']==1 and audit['invalid_closing_pair']==1
    assert groups['all_base_history'].empty
    groups,audit=prepare(s.drop(columns=['home_moneyline','away_moneyline']),b)
    assert audit['missing_closing_pair']==2 and groups['all_base_history'].empty


def test_ids_orientation_and_outcomes_are_matched_not_row_positions():
    s,b,e=inputs();orphan=b.iloc[:1].copy();orphan['game_id']='unmatched'
    groups,audit=prepare(s,pd.concat([b.iloc[::-1],orphan],ignore_index=True))
    assert audit['unmatched_prediction_ids']==1 and audit['base_matched_games']==2
    wrong=b.copy();wrong.loc[0,'home_team']='ARI'
    groups,audit=prepare(s,wrong);assert audit['metadata_conflicts']==1
    assert set(groups['all_base_history'].game_id)=={'b'}
    with pytest.raises(ValueError,match='Duplicate'):prepare(s,pd.concat([b,b.iloc[:1]],ignore_index=True))


def test_each_comparison_uses_identical_games_and_frozen_policy_cutoff():
    s,b,e=inputs();groups,audit=prepare(s,b,e.iloc[:1],'2024-01-01T00:00Z')
    for f in groups.values():
        sets=f.groupby('model').game_id.apply(set).tolist();assert all(value==sets[0] for value in sets)
        metrics=paired_intervals(f,replicates=20,reference='closing_market');assert metrics.games.nunique()==1
    assert audit['base_matched_games']==2 and audit['ensemble_matched_games']==1
    _,audit=prepare(s,b,e,'2025-01-01T00:00Z');assert audit['ensemble_matched_games']==1
    b.loc[0,'p_boosting']=np.nan
    groups,audit=prepare(s,b,e,'2024-01-01T00:00Z')
    assert audit['missing_or_invalid_model_probabilities']==1
    assert set(groups['all_base_history'].game_id)=={'b'}


def test_report_only_reads_cached_inputs_and_preserves_forecasts_and_ledgers(tmp_path):
    s,b,e=inputs();run=tmp_path/'reports/m7/frozen';run.mkdir(parents=True)
    (run.parent/'latest.json').write_text('{"run":"frozen"}')
    b.to_parquet(run/'base_predictions.parquet',index=False)
    e['model']='E1_equal__raw';e.to_parquet(run/'predictions.parquet',index=False)
    (run/'selection.json').write_text('{"method":"E1_equal__raw","outcome_cutoff":"2024-01-01T00:00:00Z"}')
    folds=[{'evaluation':year,'meta_outcome_cutoff':f'{year-1}-02-01T00:00:00Z','calibration_outcome_cutoff':f'{year}-02-01T00:00:00Z'} for year in [2024,2025]]
    (run/'metadata.json').write_text(json.dumps({'folds':folds}))
    (run/'outputs.json').write_text(json.dumps({p.name:digest(p) for p in run.iterdir()}))
    for year,g in s.groupby('season'):
        generation=tmp_path/f'data/generations/g{year}';generation.mkdir(parents=True)
        path=generation/'schedules.parquet';g.to_parquet(path,index=False)
        manifest=tmp_path/'data/manifests'/f'{year}.json';manifest.parent.mkdir(exist_ok=True)
        manifest.write_text(json.dumps({'generation':f'g{year}','files':{'schedules':{'file':'schedules.parquet','sha256':digest(path),'columns':list(g.columns)}}}))
    for name in ['models/production.joblib','data/predictions.db','data/m8/lab.db','data/m7/experimental_forecasts/original.json']:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'original artifact: must not be opened for writing or model fitting')
    before={p:digest(p) for p in tmp_path.rglob('*') if p.is_file()}
    report=generate(tmp_path,replicates=20)
    assert 'Five-way frozen-policy sample' in report.read_text()
    assert 'historical_closing_reference' in report.read_text()
    assert 'Bookmaker identity' in report.read_text()
    assert all(digest(p)==sha for p,sha in before.items())
