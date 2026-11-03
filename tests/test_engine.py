import numpy as np
import pandas as pd
import pytest
from nfl_predictor.data_loader import normalize_schedules,aggregate_pbp
from nfl_predictor.feature_engineering import build,FEATURES,team_games,rating
from nfl_predictor.model import train,save,load
from nfl_predictor.database import connect,insert,attach_results
from nfl_predictor.predictions import predict
from nfl_predictor.backtest import run

@pytest.fixture
def dataset():
    games=[]; stats=[]
    for season in range(2018,2027):
        for week in range(1,7):
            gid=f'{season}_{week}'
            games.append(dict(game_id=gid,season=season,week=week,game_type='REG',gameday=f'{season}-09-{week*4:02d}',gametime='13:00',home_team='OAK',away_team='KC',home_score=24 if week%2 else 10,away_score=17,location='Home'))
            for team,v in [('LV',week),('KC',-week)]:
                stats.append(dict(game_id=gid,team=team,off_epa=v/10,def_epa=-v/10,off_success=.5+v/100,def_success=.5-v/100,off_yards=5+v/10,def_yards=5-v/10,off_turnovers=0,def_turnovers=1))
    return normalize_schedules(pd.DataFrame(games)),pd.DataFrame(stats)

def test_normalization(dataset):
    s,_=dataset
    assert s.game_id.is_unique and set(s.home_team)=={'LV'} and s.completed.all()
    raw=pd.DataFrame([dict(game_id='x',season=2026,week=1,game_type='REG',gameday='2026-09-01',gametime='13:00',home_team='JAC',away_team='WSH',home_score=None,away_score=None)])
    n=normalize_schedules(pd.concat([raw,raw])); assert len(n)==1 and n.target.isna().all() and n.home_team.iloc[0]=='JAX'

def test_schema():
    with pytest.raises(ValueError,match='missing columns'): normalize_schedules(pd.DataFrame())
    with pytest.raises(ValueError,match='missing columns'): aggregate_pbp(pd.DataFrame())

def test_current_and_future_leakage(dataset):
    s,m=dataset; original=build(s,m)
    changed=m.copy(); changed.loc[changed.game_id.eq('2023_3'),'off_epa']=999999
    altered=build(s,changed)
    pd.testing.assert_frame_equal(original.loc[original.kickoff.le(s.loc[s.game_id.eq('2023_3'),'kickoff'].iloc[0]),FEATURES],altered.loc[altered.kickoff.le(s.loc[s.game_id.eq('2023_3'),'kickoff'].iloc[0]),FEATURES])

def test_reject_naive_cutoff(dataset):
    s,m=dataset
    with pytest.raises(ValueError,match='timezone'): rating(team_games(s,m),'LV',2023,pd.Timestamp('2023-09-01'))

def test_early_season_orientation(dataset):
    s,m=dataset; f=build(s,m)
    assert f.loc[f.game_id.eq('2018_1'),'off_epa'].isna().all()
    assert f.loc[f.game_id.eq('2023_1'),'off_epa'].iloc[0]>0
    assert f.loc[f.game_id.eq('2023_1'),'def_epa'].iloc[0]>0
    pd.testing.assert_frame_equal(f,build(s,m))

def test_model_pipeline_and_serialization(dataset,tmp_path):
    s,m=dataset; f=build(s,m); tr=f[f.season.le(2022)]
    model=train(tr); p=model['pipeline'].predict_proba(f[FEATURES])
    assert np.all((p>=0)&(p<=1)) and np.allclose(p.sum(axis=1),1)
    save(model,tmp_path/'model.joblib'); assert np.allclose(p,load(tmp_path/'model.joblib')['pipeline'].predict_proba(f[FEATURES]))
    assert np.allclose(model['pipeline'][0].statistics_,np.nan_to_num(tr[FEATURES].mean().to_numpy()))

def test_backtest(dataset,tmp_path):
    s,m=dataset; result=run(build(s,m),tmp_path)
    assert result['fixed']['test']['logistic']['games']==12
    assert all(v['training_through']==int(k)-1 for k,v in result['walk_forward'].items())
    assert 'training_rate' in result['fixed']['test']

def test_ties(dataset):
    s,m=dataset; s.loc[0,['home_score','away_score']]=17
    # Target normalization is tested using the source schema.
    raw=pd.DataFrame([dict(game_id='tie',season=2023,week=1,game_type='REG',gameday='2023-09-01',gametime='13:00',home_team='LV',away_team='KC',home_score=17,away_score=17)])
    assert normalize_schedules(raw).target.isna().all()

def record():
    return dict(game_id='g',model_version='m',created_at='2026-01-01T00:00:00+00:00',data_cutoff='2026-01-01T00:00:00+00:00',kickoff='2026-12-01T00:00:00+00:00',home_probability=.6)

def test_official_immutable(tmp_path):
    db=connect(tmp_path/'p.db'); r=record()
    assert insert(db,r)==1
    r['home_probability']=.8; assert insert(db,r)==0
    assert db.execute('SELECT home_probability FROM predictions WHERE official=1').fetchone()[0]==.6
    with pytest.raises(Exception,match='immutable'): db.execute('UPDATE predictions SET home_probability=.9')

def test_retroactive_rejected(tmp_path):
    db=connect(tmp_path/'p.db'); r=record(); r['created_at']='2027-01-01T00:00:00+00:00'
    with pytest.raises(ValueError,match='before kickoff'): insert(db,r)

def test_upcoming_only(dataset,tmp_path):
    s,m=dataset; f=build(s,m); model=train(f[f.season.le(2025)])
    s.loc[s.season.eq(2026),'kickoff']=pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=30)
    s.loc[s.season.eq(2026),['home_score','away_score','target']]=np.nan
    s.loc[s.season.eq(2026),'completed']=False
    db=connect(tmp_path/'p.db'); result=predict(s,m,model,db)
    assert len(result)==6 and result.official.all()
    assert not predict(s,m,model,db).official.any()
    with pytest.raises(ValueError,match='future'): predict(s,m,model,db,pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=1))

def test_results_do_not_rewrite_forecast(dataset,tmp_path):
    s,m=dataset; db=connect(tmp_path/'p.db'); r=record(); r['game_id']=s.iloc[0].game_id; insert(db,r)
    attach_results(db,s); s.loc[0,'home_score']=0; attach_results(db,s)
    assert db.execute('SELECT home_probability,result FROM predictions').fetchone()==(.6,0.)

def test_failed_download_preserves_cache(tmp_path,monkeypatch):
    import nfl_predictor.data_loader as loader
    import nflreadpy
    monkeypatch.setattr(loader,'DATA',tmp_path)
    existing=tmp_path/'processed/schedule_2025.parquet'; existing.parent.mkdir()
    existing.write_bytes(b'previous-cache')
    def fail(*args,**kwargs): raise OSError('network unavailable')
    monkeypatch.setattr(nflreadpy,'load_schedules',fail)
    with pytest.raises(RuntimeError,match='2025'): loader.update([2025],True)
    assert existing.read_bytes()==b'previous-cache'

def test_refresh_idempotent_and_future_scores():
    raw=pd.DataFrame([dict(game_id='future',season=2026,week=1,game_type='REG',gameday='2099-09-01',gametime='13:00',home_team='LV',away_team='KC',home_score=30,away_score=10)])
    n=normalize_schedules(pd.concat([raw,raw])); assert len(n)==1 and n.target.isna().all() and not n.completed.any()

def test_deliberate_future_injection_rejected(dataset,tmp_path):
    s,m=dataset; model=train(build(s,m))
    with pytest.raises(ValueError,match='future'): predict(s,m,model,connect(tmp_path/'x.db'),pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=10))

def test_overlap_availability(dataset):
    s,m=dataset; baseline=build(s,m)
    s.loc[s.game_id.eq('2023_2'),'kickoff']=s.loc[s.game_id.eq('2023_1'),'kickoff'].iloc[0]+pd.Timedelta(hours=1)
    f=build(s,m)
    assert f.loc[f.game_id.eq('2023_2'),'off_epa'].iloc[0]==baseline.loc[baseline.game_id.eq('2023_1'),'off_epa'].iloc[0]
