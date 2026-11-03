import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from test_engine import dataset
from nfl_predictor.analysis import paired_intervals,fit_calibrators,validate_fold,run_analysis
from nfl_predictor.feature_engineering import build,cached_build,FEATURES,team_games,rating
from nfl_predictor.data_loader import normalize_schedules
from nfl_predictor.integrity import publish,read_season,recover,digest
from nfl_predictor.model import train

@pytest.fixture
def comparison():
    rows=[]
    for i in range(30):
        for name in ['logistic','same']:
            rows.append(dict(game_id=str(i),season=2023,week=i//3,target=i%2,model=name,probability=.6 if i%2 else .4))
    return pd.DataFrame(rows)

def test_paired_identical_models(comparison):
    result=paired_intervals(comparison,100,42)
    assert (result.difference==0).all() and (result.difference_low==0).all() and (result.difference_high==0).all()
    pd.testing.assert_frame_equal(result,paired_intervals(comparison,100,42))
    assert (result.low<=result.high).all() and result.clusters.eq(10).all()
    assert result.loc[result.metric.eq('accuracy'),'low'].eq(1).all()

def test_comparisons_reject_misalignment(comparison):
    with pytest.raises(ValueError,match='identical'): paired_intervals(comparison.iloc[1:])
    with pytest.raises(ValueError,match='Duplicate'): paired_intervals(pd.concat([comparison,comparison]))
    comparison.loc[0,'probability']=2
    with pytest.raises(ValueError,match='Probabilities'): paired_intervals(comparison)

def test_intervals_detect_known_difference(comparison):
    comparison.loc[comparison.model.eq('same'),'probability']=.5
    r=paired_intervals(comparison,300)
    row=r[r.model.eq('same')&r.metric.eq('brier')].iloc[0]
    assert row.difference_low>0 and row.difference_high>0

def test_chronological_calibration(dataset):
    s,m=dataset; f=build(s,m)
    base=train(f[f.season.le(2021)])
    cal=f[f.season.eq(2022)]
    methods=fit_calibrators(base,cal,f[f.season.eq(2023)].kickoff.min(),min_games=200)
    assert set(methods)=={'sigmoid'}
    with pytest.raises(ValueError,match='evaluation'): fit_calibrators(base,cal,cal.kickoff.min())
    with pytest.raises(ValueError,match='Training'): fit_calibrators(base,f[f.season.eq(2021)],cal.kickoff.min())
    with pytest.raises(ValueError,match='Fold'): validate_fold(f,dict(train_start=2018,train_end=2022,calibration=2021,evaluation=2023))

def test_eval_target_isolation(dataset):
    s,m=dataset; f=build(s,m); base=train(f[f.season.le(2021)])
    cal=f[f.season.eq(2022)]
    a=fit_calibrators(base,cal,f[f.season.eq(2023)].kickoff.min())['sigmoid']
    f.loc[f.season.eq(2023),'target']=1-f.loc[f.season.eq(2023),'target']
    b=fit_calibrators(base,f[f.season.eq(2022)],f[f.season.eq(2023)].kickoff.min())['sigmoid']
    np.testing.assert_array_equal(a.coef_,b.coef_)

def test_future_statistics_cannot_change_predictions(dataset):
    s,m=dataset; f=build(s,m); base=train(f[f.season.le(2021)])
    altered=m.copy(); altered.loc[altered.game_id.str.startswith('2025'),'off_epa']=1e9
    g=build(s,altered)
    before=f.season.le(2024)
    np.testing.assert_array_equal(base['pipeline'].predict_proba(f.loc[before,FEATURES]),base['pipeline'].predict_proba(g.loc[before,FEATURES]))

@pytest.mark.parametrize('days',[1,3,4,7])
def test_short_holiday_and_monday_rest(dataset,days):
    s,m=dataset; s=s[~(s.season.eq(2023)&s.week.gt(1))]; h=team_games(s,m)
    game=s[s.game_id.eq('2023_1')].iloc[0]
    result=rating(h,'LV',2023,game.kickoff+pd.Timedelta(days=days))
    assert result['rest']==days

def test_suspended_and_explicit_final_time(dataset):
    s,m=dataset; game=s[s.game_id.eq('2023_1')].iloc[0]
    s['result_available_at']=pd.Series(pd.NaT,index=s.index,dtype='datetime64[ns, UTC]')
    s.loc[s.game_id.eq(game.game_id),'result_available_at']=game.kickoff+pd.Timedelta(days=5)
    h=team_games(s,m)
    before=rating(h,'LV',2023,game.kickoff+pd.Timedelta(days=1))
    baseline=rating(h,'LV',2023,game.kickoff)
    assert before['off_epa']==baseline['off_epa']
    s['status']='final'; s.loc[s.game_id.eq(game.game_id),'status']='suspended'
    h=team_games(s,m); assert h.loc[h.game_id.eq(game.game_id),'available_at'].isna().all()
    s.loc[s.game_id.eq(game.game_id),'result_available_at']=game.kickoff-pd.Timedelta(days=1)
    with pytest.raises(ValueError,match='precedes'): team_games(s,m)

def test_postponed_incomplete_and_missing_pbp(dataset):
    s,m=dataset; raw=s.iloc[:1].copy(); raw['status']='postponed'
    n=normalize_schedules(raw); assert not n.completed.any() and n.target.isna().all()
    from nfl_predictor.data_validation import coverage
    with pytest.warns(UserWarning,match='Missing'): assert coverage(s,m.iloc[0:0])['missing_metric_games']

def test_manifest_corruption_recovery_revision(dataset,tmp_path):
    s,m=dataset; pbp=pd.DataFrame({'game_id':['x'],'epa':[1.]})
    a=publish(tmp_path,2023,s,m,pbp)
    altered=m.copy(); altered.loc[0,'off_epa']=50
    with pytest.warns(UserWarning,match='revision'): b=publish(tmp_path,2023,s,altered,pbp)
    read_season(tmp_path,2023)
    (tmp_path/'generations'/b['generation']/'metrics.parquet').write_bytes(b'bad')
    with pytest.raises(ValueError,match='corruption'): read_season(tmp_path,2023)
    assert recover(tmp_path,2023)['generation']==a['generation']
    frames,_=read_season(tmp_path,2023); pd.testing.assert_frame_equal(frames['metrics'],m)

def test_interrupted_generation_keeps_pointer(dataset,tmp_path,monkeypatch):
    s,m=dataset; pbp=pd.DataFrame({'x':[1]}); a=publish(tmp_path,2023,s,m,pbp)
    original=pd.DataFrame.to_parquet
    def fail(self,path,*args,**kw):
        if Path(path).name=='metrics.parquet': raise OSError('disk failure')
        return original(self,path,*args,**kw)
    monkeypatch.setattr(pd.DataFrame,'to_parquet',fail)
    with pytest.raises(OSError): publish(tmp_path,2023,s,m,pbp)
    assert read_season(tmp_path,2023)[1]['generation']==a['generation']

def test_cached_features_reused_and_invalidated(dataset,tmp_path,monkeypatch):
    s,m=dataset; a=cached_build(s,m,tmp_path)
    import nfl_predictor.feature_engineering as fe
    original=fe.build
    def fail(*args,**kw): raise RuntimeError('rebuilt')
    monkeypatch.setattr(fe,'build',fail)
    pd.testing.assert_frame_equal(a,cached_build(s,m,tmp_path))
    m.loc[0,'off_epa']=999
    with pytest.raises(RuntimeError,match='rebuilt'): cached_build(s,m,tmp_path)

def test_experiment_reproduction(dataset,tmp_path):
    s,m=dataset; f=build(s,m)
    config={'folds':[dict(train_start=2018,train_end=2020,calibration=2021,evaluation=2022)],'bootstrap_replicates':20,'seed':42,'confidence_level':.95,'isotonic_min_games':200}
    a=run_analysis(f,tmp_path,config); assert run_analysis(f,tmp_path,config)==a
    assert (a/'incorrect_predictions.csv').exists()
    b=run_analysis(f,tmp_path/'repeated',config)
    assert json.loads((a/'outputs.json').read_text())==json.loads((b/'outputs.json').read_text())
    from streamlit.testing.v1 import AppTest
    script=f"from pathlib import Path\nfrom nfl_predictor.dashboard import render\nrender(Path({str(tmp_path)!r}), Path({str(tmp_path/'absent.db')!r}))"
    app=AppTest.from_string(script,default_timeout=60).run()
    assert not app.exception
    (a/'comparison.csv').write_text('corrupted')
    with pytest.raises(ValueError,match='corrupted'): run_analysis(f,tmp_path,config)

def test_existing_prediction_database_is_readable_without_migration(tmp_path):
    import sqlite3
    from nfl_predictor.database import connect
    path=tmp_path/'old.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE predictions(id INTEGER PRIMARY KEY,game_id TEXT NOT NULL,model_version TEXT NOT NULL,created_at TEXT NOT NULL,data_cutoff TEXT NOT NULL,kickoff TEXT NOT NULL,home_probability REAL NOT NULL,official INTEGER NOT NULL,payload TEXT NOT NULL,result REAL)')
        db.execute("INSERT INTO predictions VALUES(1,'old','M1','2026-01-01','2026-01-01','2026-12-01',.6,1,'{}',NULL)")
    with connect(path) as db:
        assert db.execute('SELECT game_id,home_probability FROM predictions').fetchone()==('old',.6)

def test_dashboard_all_pages_offline(dataset,tmp_path,monkeypatch):
    from streamlit.testing.v1 import AppTest
    import nfl_predictor.data_loader as loader
    s,m=dataset
    monkeypatch.setattr(loader,'cached',lambda:(s,m))
    monkeypatch.setattr(loader,'ROOT',tmp_path)
    monkeypatch.setattr(loader,'DATA',tmp_path/'data')
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    for page in ['Upcoming Games','Team Comparison','Model Performance','Model Analysis']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception

def test_constant_calibration_diagnostic_is_identifiable():
    from nfl_predictor.analysis import calibration_diagnostic
    diagnostic=calibration_diagnostic([0,1,0,1],[.5]*4)
    assert diagnostic['slope'] is None and diagnostic['intercept']==0

def test_feature_cache_corruption_requires_explicit_refresh(dataset,tmp_path):
    s,m=dataset; cached_build(s,m,tmp_path)
    p=next(tmp_path.glob('*.parquet')); p.write_bytes(b'bad')
    with pytest.raises(ValueError,match='Feature cache corruption'): cached_build(s,m,tmp_path)
    assert len(cached_build(s,m,tmp_path,refresh=True))==len(s)
