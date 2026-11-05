import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from nfl_predictor import prediction_errors as e
from nfl_predictor.historical_market import prepare
from nfl_predictor.integrity import digest
from test_m81 import inputs


def diagnostic():
    s,b,ensemble=inputs();groups,audit=prepare(s,b,ensemble,'2024-01-01T00:00Z')
    f=groups['all_base_history'];market=f[f.model.eq('closing_market')][['game_id','probability']].rename(columns={'probability':'market_probability'})
    f=f[f.model.ne('closing_market')].merge(market,on='game_id').merge(s[['game_id','home_team','away_team','home_score','away_score']],on='game_id')
    for column in e.FEATURES+['elo_difference']:f[column]=.1
    return e.classify(f)


def test_error_brier_residual_and_market():
    f=diagnostic();r=f.query("game_id=='a' and model=='logistic_oos'").iloc[0]
    assert r.correct and not r.error and r.predicted_winner=='LV'
    assert r.confidence==pytest.approx(.6) and r.brier==pytest.approx(.16)
    assert r.log_loss==pytest.approx(-np.log(.6)) and r.signed_residual==pytest.approx(.4)
    assert r.absolute_error==pytest.approx(.4)
    assert r.favorite_agreement=='opposite_favorite' and r.picked_market_role=='underdog'
    assert r.market_probability_difference==pytest.approx(r.probability-r.market_probability)
    assert r.brier_minus_market==pytest.approx(r.brier-(1-r.market_probability)**2)
    f.loc[0,'market_probability']=np.nan
    with pytest.raises(ValueError,match='closing-market'):e.classify(f)


def test_confidence_boundaries_and_calibration():
    f=diagnostic().iloc[[0]*7].copy();f['game_id']=list('abcdefg');f['probability']=[.5,.55,.6,.7,.8,.9,1]
    f=e.classify(f)
    assert f.confidence_bucket.tolist()==e.CONFIDENCE_LABELS+['90–100%']
    assert np.isfinite(f.log_loss).all()
    result=e.summarize(f,['model'],replicates=20).iloc[0]
    assert result.expected_error_rate==pytest.approx((1-f.confidence).mean())
    assert result.excess_error==pytest.approx(f.error.mean()-(1-f.confidence).mean())
    assert result.calibration_gap_actual_minus_expected_win==pytest.approx(-result.excess_error)
    assert result.games==7 and result.small_sample


def test_shared_counts_unique_games_and_failure_groups():
    f=diagnostic();games,summary=e.shared_failures(f)
    assert len(games)==2 and summary.games.sum()==2
    f.loc[f.game_id.eq('a'),'probability']=.1;f=e.classify(f)
    games,summary=e.shared_failures(f)
    assert games.set_index('game_id').loc['a','category']=='all_incorrect'
    f.loc[(f.game_id.eq('a'))&f.model.eq('margin_elo'),'probability']=.9;f=e.classify(f)
    games,_=e.shared_failures(f);assert games.set_index('game_id').loc['a','category']=='two_incorrect'
    assert games.set_index('game_id').loc['a','winner_disagreement']
    with pytest.raises(ValueError,match='three identical'):e.shared_failures(f.iloc[1:])


def test_matching_missing_ties_and_orientation():
    s,b,ensemble=inputs();g,audit=prepare(s,b.iloc[::-1],ensemble,'2024-01-01T00:00Z')
    assert audit['ties_excluded']==1 and audit['incomplete_scores']==1
    assert set(g['all_base_history'].game_id)=={'a','b'}
    b.loc[0,'home_team']='KC';_,audit=prepare(s,b);assert audit['metadata_conflicts']==1
    s.loc[1,'home_moneyline']=np.nan;g,audit=prepare(s,b);assert g['all_base_history'].empty
    with pytest.raises(ValueError,match='Duplicate'):e.classify(pd.concat([diagnostic(),diagnostic().iloc[:1]]))
    f=diagnostic();f['target']=f.target.astype(float);f.loc[0,'target']=.5
    with pytest.raises(ValueError,match='binary'):e.classify(f)


def cached_fixture(root):
    s,b,ensemble=inputs();run=root/'reports/m7/frozen';run.mkdir(parents=True)
    (run.parent/'latest.json').write_text('{"run":"frozen"}')
    b['elo_difference']=[10.,-10.]
    b.to_parquet(run/'base_predictions.parquet',index=False)
    ensemble['model']='E1';ensemble.to_parquet(run/'predictions.parquet',index=False)
    (run/'selection.json').write_text('{"method":"E1","outcome_cutoff":"2024-01-01T00:00Z"}')
    (run/'metadata.json').write_text(json.dumps({'folds':[{'evaluation':y,'meta_outcome_cutoff':'2023-01-01T00:00Z','calibration_outcome_cutoff':'2023-01-01T00:00Z'} for y in [2024,2025]]}))
    required=['base_predictions.parquet','predictions.parquet','selection.json','metadata.json']
    (run/'outputs.json').write_text(json.dumps({name:digest(run/name) for name in required}))
    for year,g in s.groupby('season'):
        directory=root/f'data/generations/{year}';directory.mkdir(parents=True);path=directory/'s.parquet';g.to_parquet(path,index=False)
        manifest=root/'data/manifests';manifest.mkdir(exist_ok=True)
        (manifest/f'{year}.json').write_text(json.dumps({'generation':str(year),'files':{'schedules':{'file':path.name,'sha256':digest(path)}}}))
        feature=b[b.season.eq(year)][['game_id','season','week','kickoff','home_team','away_team','data_cutoff']].copy()
        for c in e.FEATURES:feature[c]=.1
        cache=root/'data/history_features';cache.mkdir(exist_ok=True);path=cache/f'{year}-fixture.parquet';feature.to_parquet(path,index=False)
        path.with_suffix('.json').write_text(json.dumps({'sha256':digest(path)}))
    return run


def test_report_cached_only_and_preservation(tmp_path,monkeypatch):
    run=cached_fixture(tmp_path)
    protected=['data/predictions.db','data/m8/lab.db','data/m83/forecast.json','data/m91/receipt.json','models/production.joblib','M81_HISTORICAL_MARKET_REPORT.md']
    for name in protected:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'preserve original')
    before={str(p):digest(p) for p in tmp_path.rglob('*') if p.is_file()}
    import nfl_predictor.model as model
    monkeypatch.setattr(model,'train',lambda *a,**kw:pytest.fail('Training prohibited'))
    output=e.generate(tmp_path,replicates=20)
    assert output.exists() and (tmp_path/'M91A_CLASSIFIED_ERRORS.csv').exists()
    assert all(digest(Path(p))==sha for p,sha in before.items())
    assert 'No M9.2' in output.read_text()
    f=pd.read_csv(tmp_path/'M91A_CLASSIFIED_ERRORS.csv')
    assert f.groupby(['sample','model']).size().eq(2).all()
    (run/'base_predictions.parquet').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='integrity'):e.load_inputs(tmp_path,tmp_path/'data')


def test_future_feature_cutoff_rejected(tmp_path):
    cached_fixture(tmp_path);path=tmp_path/'data/history_features/2024-fixture.parquet'
    f=pd.read_parquet(path);f['data_cutoff']+=pd.Timedelta(hours=1);f.to_parquet(path,index=False)
    path.with_suffix('.json').write_text(json.dumps({'sha256':digest(path)}))
    with pytest.raises(ValueError,match='provenance mismatch'):e.load_inputs(tmp_path,tmp_path/'data')
