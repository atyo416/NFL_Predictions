"""Small offline contract tests for historical margin research."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
import pytest
from nfl_predictor import spread_benchmark as sb


@pytest.fixture
def margin_data():
    rows=[]
    for year in range(2008,2026):
        for week in range(1,5):
            at=pd.Timestamp(f'{year}-09-{week*4:02d}T17:00:00Z')
            rows.append(dict(game_id=f'{year}_{week}',season=year,week=week,game_type='REG',kickoff=at,
                home_team='KC',away_team='BUF',completed=True,home_score=20+week,away_score=20,
                neutral=0,spread_line=3.,home_spread_odds=-110,away_spread_odds=-110,
                data_cutoff=at,**{c:float(week) for c in sb.FEATURES if c!='neutral'}))
    s=pd.DataFrame(rows);f=s[['game_id','season','kickoff','home_team','away_team','data_cutoff']+sb.FEATURES].copy()
    return s,f


def test_margin_sign_ties_and_missing_labels(margin_data):
    s,f=margin_data
    s.loc[0,['home_score','away_score','spread_line']]=[28,20,7]
    s.loc[1,['home_score','away_score','spread_line']]=[17,20,-3]
    s.loc[2,['home_score','away_score']]=[20,20]
    s.loc[3,'home_score']=np.nan;s.loc[4,'completed']=False
    s.loc[5,'spread_line']=np.inf
    result,coverage=sb.prepare(s,f)
    assert result.iloc[0].actual_home_margin==8 and result.iloc[0].market_home_margin==7
    assert result.iloc[1].actual_home_margin==-3 and result.iloc[1].market_home_margin==-3
    assert result.iloc[2].actual_home_margin==0
    assert not result.game_id.isin(s.loc[[3,4],'game_id']).any()
    assert result.loc[result.game_id.eq(s.loc[5,'game_id']),'market_home_margin'].isna().all()
    assert coverage.missing_invalid_spread.sum()==1 and coverage.ties_included.sum()==1
    with pytest.raises(ValueError,match='Missing schedule'):sb.prepare(s.drop(columns='away_score'),f)
    with pytest.raises(ValueError,match='duplicate'):sb.prepare(pd.concat([s,s.iloc[:1]]),f)


def test_ats_grades_and_predefined_thresholds():
    f=pd.DataFrame({'game_id':list('abcdef'),'ridge':[10,-6,7,3,10,5],
                    'market_home_margin':[7,-3,7,0,7,0],'actual_home_margin':[8,-4,10,0,6,2]})
    f['boosted']=f.ridge
    selected=sb.grade(f,'ridge',0)
    assert selected.game_id.tolist()==list('abdef')  # zero edge c never selected
    assert selected.ats_result.tolist()==['win','win','push','loss','win']
    assert selected.selected_side.tolist()==['home','away','home','home','home']
    assert sb.grade(f,'ridge',3).game_id.tolist()==list('abdef')
    assert sb.grade(f,'ridge',5).game_id.tolist()==['f']
    row=sb.ats_metrics(f).iloc[0]
    assert (row.wins,row.losses,row.pushes)==(3,1,1)
    assert row.win_rate_ex_push==.75 and row.push_rate==.2
    low,high=sb.wilson(3,4);assert 0<low<.75<high<1
    assert np.isnan(sb.wilson(0,0)[0])


def test_forward_cutoff_and_training_only_preprocessing(margin_data,tmp_path):
    s,f=margin_data;frame,_=sb.prepare(s,f)
    frame.loc[0,'available_at']=pd.Timestamp('2019-09-04T17:00Z') # equal cutoff is excluded
    tr=frame[frame.season.lt(2019)&frame.available_at.lt(pd.Timestamp('2019-09-04T17:00Z'))]
    models=sb.fit(tr)
    np.testing.assert_allclose(models['ridge'][0].statistics_,tr[sb.FEATURES].mean())
    np.testing.assert_allclose(models['ridge'][1].mean_,tr[sb.FEATURES].mean())
    p,folds=sb.annual(frame,tmp_path,years=[2019])
    assert folds.iloc[0].training_games==len(tr)
    assert pd.Timestamp(folds.iloc[0].latest_training_result)<pd.Timestamp(folds.iloc[0].training_cutoff)
    assert p.season.eq(2019).all() and p.training_cutoff.lt(p.kickoff+pd.Timedelta(seconds=1)).all()
    again,meta=sb.annual(frame,tmp_path,years=[2019]);pd.testing.assert_frame_equal(p,again)
    assert meta.cache_reused.all()
    next(tmp_path.glob('*.joblib')).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='integrity'):sb.annual(frame,tmp_path,years=[2019])


def test_future_outcomes_and_closing_lines_cannot_change_frozen_fit(margin_data,tmp_path):
    s,f=margin_data;frame,_=sb.prepare(s,f)
    original,folds=sb.annual(frame,tmp_path,years=[2019])
    changed=frame.copy();changed.loc[changed.season.ge(2019),'actual_home_margin']=9999
    changed['market_home_margin']=-9999
    changed.loc[changed.season.ge(2020),sb.FEATURES]=9999
    attempt,meta=sb.annual(changed,tmp_path,years=[2019])
    np.testing.assert_array_equal(original[sb.MODELS],attempt[sb.MODELS])
    assert original.model_version.equals(attempt.model_version) and meta.cache_reused.all()
    bad=f.copy();bad.loc[0,'data_cutoff']+=pd.Timedelta(days=1)
    with pytest.raises(ValueError,match='after kickoff'):sb.prepare(s,bad)
    bad=f.copy();bad.loc[0,'home_team']='NE'
    with pytest.raises(ValueError,match='mismatch'):sb.prepare(s,bad)


def test_missing_features_training_only_and_no_market_inputs(margin_data):
    s,f=margin_data;frame,_=sb.prepare(s,f)
    frame['neutral']=np.nan
    models=sb.fit(frame[frame.season.lt(2019)])
    assert 'neutral' not in models['active']
    assert not set(sb.FEATURES)&{'spread_line','home_score','away_score','actual_home_margin','market_home_margin','home_spread_odds','away_spread_odds','target'}
    before=sb.predict(models,frame)
    frame[['spread_line','market_home_margin','actual_home_margin','home_spread_odds']]=9999
    after=sb.predict(models,frame)
    for name in sb.MODELS:np.testing.assert_array_equal(before[name],after[name])
    assert np.isfinite(before['ridge']).all() and np.isfinite(before['boosted']).all()


def test_paired_margin_metrics():
    f=pd.DataFrame({'season':[2022]*4,'week':[1,1,2,2],'actual_home_margin':[0,0,0,0],
                    'market_home_margin':[2,2,2,2],'ridge':[1,1,1,1],'boosted':[3,3,3,3]})
    m=sb.margin_metrics(f,replicates=20).set_index('model')
    assert m.loc['ridge','mae_minus_market']==-1 and m.loc['boosted','mae_minus_market']==1
    assert m.loc['ridge','difference_low']==-1 and m.loc['ridge','difference_high']==-1
    assert m.loc['closing_market','rmse']==2 and m.loc['closing_market','bias_predicted_minus_actual']==2


def test_generate_preserves_production_and_betting_files(margin_data,tmp_path,monkeypatch):
    s,f=margin_data
    paths=['models/champion.json','models/registry/boosting.joblib','models/ensemble.joblib',
           'data/predictions.db','data/m8/lab.db','data/m8/odds.json','M81_HISTORICAL_MARKET_REPORT.md']
    for name in paths:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'protected original')
    before={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() for name in paths}
    monkeypatch.setattr(sb,'load_compact',lambda data:(s,pd.DataFrame(),[]))
    monkeypatch.setattr(sb,'reconstruct',lambda *a:(f.drop(columns='elo_difference'),pd.DataFrame()))
    report=sb.generate(tmp_path)
    assert report.exists() and (tmp_path/'reports/m82/latest.json').exists()
    assert 'No realized ROI' in report.read_text()
    assert before=={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() for name in paths}
