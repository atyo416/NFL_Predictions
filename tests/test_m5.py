from pathlib import Path
from dataclasses import replace
import copy
import json
import numpy as np
import pandas as pd
import pytest
from nfl_predictor.history_data import normalize_history,update_history,load_history,metrics_history
from nfl_predictor.history_features import reconstruct,attach_elo,COMMON
from nfl_predictor.history_models import decay_weights,fit_history
from nfl_predictor.history_analysis import develop,run,split
from nfl_predictor.integrity import digest
from nfl_predictor.registry import register,load_candidate,activate

@pytest.fixture
def config():
    c=json.loads((Path(__file__).parents[1]/'config/m5_protocol.json').read_text())
    c['hgb_parameters']={**c['hgb_parameters'],'max_iter':8,'min_samples_leaf':2}
    c['bootstrap_replicates']=20;c['selected_windows_per_algorithm']=1;c['folds']=c['folds'][:1]
    return c

@pytest.fixture
def history_dataset():
    games=[];stats=[]
    for year in range(1999,2027):
        for week in range(1,7):
            gid=f'{year}_{week}'
            games.append(dict(game_id=gid,season=year,week=week,game_type='REG',gameday=f'{year}-09-{week*4:02d}',gametime=None if year==1999 else '13:00',home_team='OAK',away_team='KC',home_score=24 if week%2 else 10,away_score=17,location='Home'))
            for team,v in [('LV',week),('KC',-week)]:stats.append(dict(game_id=gid,team=team,off_epa=v/10,def_epa=-v/10,off_success=.5+v/100,def_success=.5-v/100,off_yards=5+v/10,def_yards=5-v/10,off_turnovers=0,def_turnovers=1))
    return normalize_history(pd.DataFrame(games)),pd.DataFrame(stats)

@pytest.fixture
def historical_frame(history_dataset,config,tmp_path):
    s,m=history_dataset;frame,audit=reconstruct(s,m,tmp_path/'features')
    return attach_elo(frame,s,config['elo'])

def test_historical_clock_bounds_and_identity():
    raw=pd.DataFrame([dict(game_id='g',season=1999,week=1,game_type='REG',gameday='1999-09-12',gametime=None,home_team='STL',away_team='SD',home_score=17,away_score=10,location='Neutral')])
    s=normalize_history(raw);g=s.iloc[0]
    assert g.home_team=='LA' and g.away_team=='LAC' and g.neutral==1
    assert g.kickoff_precision=='date_lower_bound' and pd.isna(g.actual_kickoff)
    assert g.kickoff.tz_convert('America/New_York').hour==0
    assert g.result_available_at.tz_convert('America/New_York')==pd.Timestamp('1999-09-13T08:00:00-04:00')

def test_decay_at_known_ages_and_cutoff():
    cutoff=pd.Timestamp('2021-01-01T00:00Z')
    times=[cutoff-pd.Timedelta(days=365.25*age) for age in [0,3,6]]
    np.testing.assert_allclose(decay_weights(times,cutoff,3,normalize=False),[1,.5,.25])
    assert decay_weights(times,cutoff,3).mean()==pytest.approx(1.)
    np.testing.assert_array_equal(decay_weights(times,cutoff),np.ones(3))
    with pytest.raises(ValueError,match='future'):decay_weights([cutoff+pd.Timedelta(days=1)],cutoff,3)
    with pytest.raises(ValueError,match='timezone'):decay_weights(times,pd.Timestamp('2021-01-01'),3)
    with pytest.raises(ValueError,match='Half-life'):decay_weights(times,cutoff,0)

@pytest.mark.parametrize('algorithm',['logistic','hgb'])
def test_estimators_receive_weights_and_serialization(algorithm,config,tmp_path):
    import joblib
    n=160
    f=pd.DataFrame({'season':np.repeat(range(2001,2021),8),'kickoff':pd.date_range('2001-01-01',periods=n,freq='45D',tz='UTC'),'target':np.r_[np.zeros(120),np.ones(40)],'constant':0.})
    a=fit_history(f,algorithm,config,None,features=['constant']);b=fit_history(f,algorithm,config,3,features=['constant'])
    w=decay_weights(f.kickoff,b['training_cutoff'],3)
    assert b['pipeline'].predict_proba(f[['constant']])[0,1]>a['pipeline'].predict_proba(f[['constant']])[0,1]
    np.testing.assert_allclose(b['pipeline'].predict_proba(f[['constant']])[:,1],np.average(f.target,weights=w),atol=.002)
    joblib.dump(b,tmp_path/'weighted.joblib');loaded=joblib.load(tmp_path/'weighted.joblib')
    np.testing.assert_array_equal(b['pipeline'].predict_proba(f[['constant']]),loaded['pipeline'].predict_proba(f[['constant']]))
    assert b['weighting']['effective_sample_size']<n and b['activation_blocked']

def test_reconstruction_common_and_future_injection(history_dataset,config,tmp_path):
    s,m=history_dataset;a,audit=reconstruct(s,m,tmp_path/'a')
    assert audit.loc[audit.season.eq(1999),'clock_known_fraction'].iloc[0]==0
    assert a.loc[a.season.eq(1999),'rest'].isna().all() and 'rest' not in COMMON
    b=reconstruct(s,m,tmp_path/'a')[0];pd.testing.assert_frame_equal(a,b)
    modified=m.copy();modified.loc[modified.game_id.eq('2013_3'),'off_epa']=1e9
    other=reconstruct(s,modified,tmp_path/'b')[0]
    cutoff=s.loc[s.game_id.eq('2013_3'),'kickoff'].iloc[0]
    pd.testing.assert_frame_equal(a.loc[a.kickoff.le(cutoff),COMMON],other.loc[other.kickoff.le(cutoff),COMMON])
    model=fit_history(a[a.season.le(2008)],'logistic',config,3)
    selected=a.kickoff.le(cutoff)&a.season.ge(2009)
    np.testing.assert_array_equal(model['pipeline'].predict_proba(a.loc[selected,model['features']]),model['pipeline'].predict_proba(other.loc[selected,model['features']]))
    with pytest.raises(ValueError,match='corrupt'):
        next((tmp_path/'a').glob('*.parquet')).write_bytes(b'bad');reconstruct(s,m,tmp_path/'a')

def test_window_boundaries_and_selection_isolation(historical_frame,config):
    tr,ev=split(historical_frame,2013,2020,2022)
    assert tr.season.min()==2013 and tr.season.max()==2020 and ev.season.eq(2022).all()
    a=develop(historical_frame,config)
    changed=historical_frame.copy();changed.loc[changed.season.ge(2022),'target']=1-changed.loc[changed.season.ge(2022),'target']
    b=develop(changed,config)
    assert a[3:]==b[3:]
    pd.testing.assert_frame_equal(a[0].drop(columns='runtime_seconds'),b[0].drop(columns='runtime_seconds'))
    with pytest.raises(ValueError,match='missing seasons'):split(historical_frame[historical_frame.season.ne(2004)],1999,2020,2022)
    bad=copy.deepcopy(config);bad['development_folds'][-1]['validation']=2024
    with pytest.raises(ValueError,match='through 2021'):develop(historical_frame,bad)


def source_frames(year):
    s=pd.DataFrame([dict(game_id=f'{year}_1',season=year,week=1,game_type='REG',gameday=f'{year}-09-12',gametime=None if year==1999 else '13:00',home_team='OAK',away_team='KC',home_score=24,away_score=10,location='Home')])
    p=pd.DataFrame([dict(game_id=f'{year}_1',posteam=a,defteam=b,play_type=kind,epa=value,yards_gained=yards,interception=0.,fumble_lost=0.,qb_kneel=0.,qb_spike=0.) for a,b,kind,value,yards in [('OAK','KC','pass',.2,8),('KC','OAK','run',-.1,2)]])
    return s,p

def test_resumable_ingestion_and_original_default_scope(tmp_path,monkeypatch):
    import nflreadpy as nfl,polars as pl
    import nfl_predictor.data_loader as loader
    calls=[]
    monkeypatch.setattr(nfl,'load_schedules',lambda years:pl.from_pandas(source_frames(years[0])[0]))
    def pbp(years):
        calls.append(years[0])
        if years[0]==2000:raise OSError('interrupted source')
        return pl.from_pandas(source_frames(years[0])[1])
    monkeypatch.setattr(nfl,'load_pbp',pbp)
    with pytest.raises(RuntimeError,match='2000'):update_history(tmp_path,1999,2000)
    pointer=tmp_path/'manifests/1999.json';sha=digest(pointer)
    monkeypatch.setattr(nfl,'load_pbp',lambda years:pl.from_pandas(source_frames(years[0])[1]))
    update_history(tmp_path,1999,2000);assert digest(pointer)==sha
    s,m=load_history(tmp_path,1999,2000);assert len(s)==2 and s.game_id.is_unique
    monkeypatch.setattr(loader,'DATA',tmp_path)
    with pytest.raises(FileNotFoundError):loader.cached() # Modern default must not silently expand.
    assert len(loader.cached([1999,2000])[0])==2
    current=json.loads(pointer.read_text());path=tmp_path/'generations'/current['generation']/'metrics.parquet';path.write_bytes(b'bad')
    with pytest.raises(ValueError,match='corruption'):load_history(tmp_path,1999,2000)


def test_history_registry_preserves_m4_and_blocks_activation(historical_frame,config,tmp_path):
    import joblib
    model=fit_history(historical_frame[historical_frame.season.le(2020)],'hgb',config,3)
    path=register(model,tmp_path/'registry',{'training_window':{'policy':'W4','start':1999},'weighting':model['weighting'],'activation_blocked':True})
    loaded,meta=load_candidate(tmp_path/'registry',model['version']);assert meta['designation']=='experimental'
    prod=tmp_path/'production.joblib';joblib.dump({'version':'original'},prod);sha=digest(prod)
    report=tmp_path/'review.txt';report.write_text('test review')
    decision=tmp_path/'decision.json';decision.write_text(json.dumps({'candidate_version':model['version'],'reviewer':'operator','rationale':'test','evidence_report':str(report),'evidence_sha256':digest(report),'artifact_sha256':meta['artifact_sha256'],'decision':'approve','windows_verified':True}))
    with pytest.raises(ValueError,match='M5 candidates'):activate(tmp_path/'registry',prod,decision)
    assert digest(prod)==sha

def test_comparison_alignment_calibration_reproduction_and_dashboard(historical_frame,history_dataset,config,tmp_path):
    from nfl_predictor.feature_engineering import build
    from nfl_predictor.history_features import attach_elo
    s,m=history_dataset;modern=s[s.season.ge(2018)].copy();modern=modern.drop(columns=['result_available_at','kickoff_precision','actual_kickoff','neutral_known'])
    reference=attach_elo(build(modern,m[m.game_id.isin(modern.game_id)]),modern,config['elo'])
    a=run(historical_frame,reference,tmp_path/'reports/m5',tmp_path/'registry-a',config)
    b=run(historical_frame,reference,tmp_path/'repeat',tmp_path/'registry-b',config)
    pd.testing.assert_frame_equal(pd.read_parquet(a/'predictions.parquet'),pd.read_parquet(b/'predictions.parquet'))
    assert run(historical_frame,reference,tmp_path/'reports/m5',tmp_path/'registry-a',config)==a
    c=pd.read_csv(a/'comparison.csv');assert c.games.nunique()==1
    metadata=json.loads((a/'metadata.json').read_text());assert metadata['selected_policies'] and metadata['selection_end']==2021
    from streamlit.testing.v1 import AppTest
    script=f"from pathlib import Path\nfrom nfl_predictor.history_dashboard import render\nrender(Path({str(tmp_path)!r}))"
    app=AppTest.from_string(script,default_timeout=90).run();assert not app.exception
    changed=reference.copy();changed.loc[changed.season.eq(2022),'target']=1-changed.loc[changed.season.eq(2022),'target']
    with pytest.raises(ValueError,match='reference outcomes'):run(historical_frame,changed,tmp_path/'bad',tmp_path/'registry-c',config)
    (a/'comparison.csv').write_text('bad')
    with pytest.raises(ValueError,match='checksum'):run(historical_frame,reference,tmp_path/'reports/m5',tmp_path/'registry-a',config)


def test_longer_elo_warmup_and_prior_fallback(history_dataset,config,tmp_path):
    from nfl_predictor.elo import replay,EloParameters
    from nfl_predictor.feature_engineering import team_games,rating
    s,m=history_dataset
    pre,_,_=replay(s,EloParameters(**config['elo']))
    assert pre[pre.season.eq(1999)].iloc[0].home_elo==1500 and pre[pre.season.eq(1999)].warmup.all()
    altered=s.copy();altered.loc[altered.season.eq(2020),'home_score']=1000
    changed=replay(altered,EloParameters(**config['elo']))[0]
    pd.testing.assert_frame_equal(pre.loc[pre.season.le(2019)],changed.loc[changed.season.le(2019)])
    modern=replay(s[s.season.ge(2018)],EloParameters(**config['elo']))[0]
    assert modern[modern.season.eq(2018)].iloc[0].home_elo==1500
    cutoff=s[s.game_id.eq('2000_1')].kickoff.iloc[0]
    history=team_games(s,m)
    prior=rating(history,'LV',2000,cutoff)
    league=history[history.season.eq(1999)][['off_epa']].mean().iloc[0]
    own=history[history.season.eq(1999)&history.team.eq('LV')].off_epa.mean()
    assert prior['off_epa']==pytest.approx(.5*own+.5*league)
    assert rating(history,'HOU',2000,cutoff)['off_epa']==pytest.approx(league)


def test_weighted_scaler_uses_training_weights(historical_frame,config):
    frame=historical_frame[historical_frame.season.le(2020)]
    model=fit_history(frame,'logistic',config,3,features=['off_epa'])
    weights=decay_weights(frame.kickoff,model['training_cutoff'],3)
    imputed=model['pipeline'][0].transform(frame[['off_epa']])
    np.testing.assert_allclose(model['pipeline'][1].mean_,np.average(imputed,axis=0,weights=weights))


def test_history_cli_contract(monkeypatch,capsys):
    from nfl_predictor.cli import main
    monkeypatch.setattr('sys.argv',['cli','--help'])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==0
    text=capsys.readouterr().out
    assert all(cmd in text for cmd in ['update-history','audit-history','compare-history','report-m5','--start','--end'])
