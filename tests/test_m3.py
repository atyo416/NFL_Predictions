import json
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from nfl_predictor.elo import EloParameters,probability,replay,rankings
from nfl_predictor.schedule_features import schedule_features
from nfl_predictor.quarterbacks import normalize_depth,context,validate_verified,COLUMNS

def game(gid='a',kickoff='2023-09-07T00:00:00Z',home='LV',away='KC',home_score=24,away_score=17,week=1,season=2023,**kw):
    return dict(game_id=gid,kickoff=pd.Timestamp(kickoff),home_team=home,away_team=away,home_score=home_score,away_score=away_score,week=week,season=season,game_type='REG',completed=True,neutral=0,**kw)

def test_equal_and_home_probability():
    assert probability(1500,1500,True)==.5
    assert probability(1500,1500)==pytest.approx(1/(1+10**(-50/400)))

def test_symmetric_win_loss_and_snapshots():
    pre,h,_=replay(pd.DataFrame([game()]))
    assert pre.home_elo.iloc[0]==1500 and pre.away_elo.iloc[0]==1500
    assert h.change.sum()==pytest.approx(0) and h.change.iloc[0]>0 and h.change.iloc[1]<0
    assert h.pregame_elo.eq(1500).all()

def test_ties():
    _,h,_=replay(pd.DataFrame([game(home_score=17)]))
    assert h.result.eq(.5).all() and h.change.sum()==pytest.approx(0)
    assert h.change.iloc[0]<0 # Tie underperformed the home-advantaged expectation.

def test_offseason_regression():
    f=pd.DataFrame([game(season=2022,kickoff='2022-09-01T00:00Z'),game('b',season=2023)])
    pre,h,_=replay(f)
    assert pre.iloc[1].home_elo==pytest.approx(1500+.67*h.iloc[0].change)

def test_determinism_aliases_and_duplicates():
    f=pd.DataFrame([game(home='OAK')]);a=replay(f);b=replay(pd.concat([f,f]))
    for left,right in zip(a,b):pd.testing.assert_frame_equal(left,right)
    assert a[0].home_team.iloc[0]=='LV'
    with pytest.raises(ValueError,match='duplicate'):replay(pd.concat([f,pd.DataFrame([game(home='OAK',home_score=30)])]))

def test_canceled_and_future_invariance():
    f=pd.DataFrame([game(),game('b',kickoff='2023-09-14T00:00Z',week=2)])
    pre,_,_=replay(f);f.loc[1,'home_score']=100
    assert replay(f)[0].iloc[0].equals(pre.iloc[0])
    f['status']='canceled'; assert replay(f)[1].empty

def test_simultaneous_and_equal_availability():
    f=pd.DataFrame([game(),game('b',home='BUF',away='NYJ')])
    pre,_,_=replay(f);assert pre.home_elo.eq(1500).all()
    # Artificially shared team checks the strict availability boundary explicitly.
    f=pd.DataFrame([game(),game('b',kickoff='2023-09-07T08:00Z',week=2)])
    pre,h,_=replay(f);assert pre.home_elo.eq(1500).all()
    assert replay(f,cutoff=pd.Timestamp('2023-09-07T08:00Z'))[1].empty

def test_delayed_final_and_margin_cap():
    f=pd.DataFrame([game(result_available_at=pd.Timestamp('2023-09-20T00:00Z')),game('b',kickoff='2023-09-14T00:00Z',week=2)])
    assert replay(f)[0].home_elo.eq(1500).all()
    _,h,_=replay(pd.DataFrame([game(home_score=1000,away_score=0)]),EloParameters(margin=True))
    assert h.margin_multiplier.le(3).all() and abs(h.change.iloc[0])<=60

def test_power_rankings_32_and_cutoff():
    f=pd.DataFrame([game()]);r,h=rankings(f,pd.Timestamp('2023-09-08T00:00Z'))
    assert len(r)==32 and r['rank'].tolist()==list(range(1,33))
    assert r.iloc[0].team=='LV' and r.iloc[0].record=='1-0-0'
    assert r.weekly_change.sum()==pytest.approx(0)
    assert len(h)==2

def season_schedule():
    # Complete 17-game team schedules; week 8 is the scheduled bye.
    rows=[]
    for team,other,offset in [('LV','KC',0),('BUF','NYJ',1)]:
        for week in range(1,19):
            if week==8:continue
            at=pd.Timestamp('2023-09-07T00:00Z')+pd.Timedelta(days=7*(week-1)+offset)
            rows.append(game(f'{team}-{week}',str(at),home=team,away=other,week=week))
    return pd.DataFrame(rows)

def test_normal_short_bye_and_advantage():
    f=season_schedule();r=schedule_features(f)
    normal=r[r.game_id.eq('LV-2')].iloc[0]
    assert normal.home_rest_days==7 and normal.home_short_rest==0
    bye=r[r.game_id.eq('LV-9')].iloc[0];assert bye.home_bye==1 and bye.home_rest_days==14 and bye.home_extended_rest==0
    f.loc[f.game_id.eq('LV-2'),'kickoff']-=pd.Timedelta(days=3)
    assert schedule_features(f).loc[lambda x:x.game_id.eq('LV-2'),'home_short_rest'].iloc[0]==1
    f.loc[f.game_id.eq('LV-3'),'away_team']='BUF'
    feature=schedule_features(f).loc[lambda x:x.game_id.eq('LV-3')].iloc[0]
    assert feature.rest_advantage==pytest.approx(4.)

def test_postponed_long_rest_and_missing_prior():
    f=season_schedule();f.loc[f.game_id.eq('LV-2'),'status']='postponed'
    r=schedule_features(f);row=r[r.game_id.eq('LV-3')].iloc[0]
    assert row.home_rest_days==14 and row.home_bye==0 and row.home_extended_rest==1
    assert pd.isna(r.loc[r.game_id.eq('LV-1'),'home_rest_days'].iloc[0])
    assert pd.isna(schedule_features(f.iloc[:4]).iloc[-1].home_bye)

def evidence():
    return pd.DataFrame([dict(zip(COLUMNS,['LV','id-new','New QB','reviewed report','2023-09-13T00:00Z','2023-09-13T01:00Z','verified_pregame','questionable','candidate','b',2023,2,'independently reviewed']))])

def test_qb_cutoff_retrospective_unknown_and_player_ids():
    f=pd.DataFrame([game(home_qb_id='id-old',home_qb_name='Old QB'),game('b',kickoff='2023-09-14T00:00Z',week=2)])
    records=validate_verified(evidence()); at=pd.Timestamp('2023-09-14T00:00Z')
    ctx=context(f,records,'OAK','b',at)
    assert ctx['most_recent_observed_id']=='id-old' and ctx['candidate_id']=='id-new' and ctx['starter_change']==1
    assert context(f,records,'LV','b',pd.Timestamp('2023-09-12T00:00Z'))['candidate_id'] is None
    records['classification']='retrospective'
    c=context(f,records,'LV','b',at);assert c['candidate_id'] is None and c['availability_status']=='unknown'

def test_qb_received_after_cutoff_and_unknown_injury():
    f=pd.DataFrame([game()]);r=evidence();r['observed_at']='2024-01-01T00:00Z'
    c=context(f,r,'LV','b',pd.Timestamp('2023-09-14T00:00Z')); assert c['candidate_id'] is None and c['availability_status']=='unknown'
    r['source_at']='2023-09-12'
    with pytest.raises(ValueError,match='timezone'): validate_verified(r)

def test_depth_chart_schema_differences():
    old=pd.DataFrame([dict(club_code='OAK',gsis_id='id',full_name='QB',position='QB',depth_team='1',week=1)])
    new=pd.DataFrame([dict(dt='2023-09-01T00:00Z',team='LV',gsis_id='id',player_name='QB',pos_abb='QB',pos_rank=1)])
    a=normalize_depth(old,'2023-09-02T00:00Z',2023);b=normalize_depth(new,'2023-09-02T00:00Z',2023)
    assert a.player_id.iloc[0]==b.player_id.iloc[0] and a.team.iloc[0]=='LV'
    assert a.classification.eq('retrospective').all() and b.classification.eq('unknown').all()
    assert a.availability_status.eq('unknown').all()
    with pytest.raises(ValueError,match='schema'):normalize_depth(pd.DataFrame(),'2023-09-02T00:00Z',2023)

from test_engine import dataset

def test_m3_reproduction_and_future_features(dataset,tmp_path):
    from nfl_predictor.m3 import prepare,compare
    from nfl_predictor.quarterbacks import empty
    s,m=dataset
    config=json.loads((__import__('pathlib').Path(__file__).parents[1]/'config/m3_protocol.json').read_text())
    config['folds']=config['folds'][:1];config['bootstrap_replicates']=20
    frame=prepare(s,m,empty(),config,tmp_path/'features')
    altered=s.copy();altered.loc[altered.season.eq(2025),'home_score']=1000
    changed=prepare(altered,m,empty(),config,tmp_path/'features')
    before=frame.season.le(2024)
    pd.testing.assert_frame_equal(frame.loc[before,['elo_difference','elo_probability','elo_margin_probability']],changed.loc[before,['elo_difference','elo_probability','elo_margin_probability']])
    a=compare(frame,tmp_path/'a',config);b=compare(frame,tmp_path/'b',config)
    assert json.loads((a/'outputs.json').read_text())==json.loads((b/'outputs.json').read_text())
    assert compare(frame,tmp_path/'a',config)==a
    c=pd.read_csv(a/'comparison.csv');assert c.games.nunique()==1
    metadata=json.loads((a/'metadata.json').read_text());assert all('Skipped' in f['qb_status'] for f in metadata['folds'])
    from nfl_predictor.model import train
    from nfl_predictor.m3 import CANDIDATES
    model=train(frame[frame.season.le(2021)],CANDIDATES['m2_elo_rest'])
    np.testing.assert_array_equal(model['pipeline'].predict_proba(frame.loc[before,model['features']]),model['pipeline'].predict_proba(changed.loc[before,model['features']]))

def test_consecutive_unusual_rest_is_not_invented_bye():
    f=pd.DataFrame([game(week=1),game('b',kickoff='2023-09-21T00:00Z',week=3),game('c',kickoff='2023-10-05T00:00Z',week=5)])
    r=schedule_features(f)
    assert r.home_bye.iloc[0]==0 and r.home_bye.iloc[1:].isna().all() and r.home_rest_days.iloc[1:].eq(14).all()

def test_qb_missing_status_and_conflicting_designations():
    f=pd.DataFrame([game()]);r=evidence();r['availability_status']=None
    records=validate_verified(r)
    cutoff=pd.Timestamp('2023-09-14T00:00Z')
    assert context(f,records,'LV','b',cutoff)['availability_status']=='unknown'
    conflicting=records.copy();conflicting['player_id']='different'
    assert context(f,pd.concat([records,conflicting]),'LV','b',cutoff)['candidate_id'] is None
    # Exact source timestamp at cutoff is excluded.
    assert context(f,records,'LV','b',pd.Timestamp('2023-09-13T00:00Z'))['candidate_id'] is None

def test_new_cli_help_preserves_contract(monkeypatch,capsys):
    from nfl_predictor.cli import main
    monkeypatch.setattr('sys.argv',['cli','--help'])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==0
    help=capsys.readouterr().out
    for name in ['update','features','train','backtest','predict','analyze','recover-cache','ratings','rankings','compare-m3','report-m3']:
        assert name in help

def test_all_five_dashboard_pages_offline(dataset,tmp_path,monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    import nfl_predictor.data_loader as loader
    s,m=dataset
    monkeypatch.setattr(loader,'cached',lambda:(s,m));monkeypatch.setattr(loader,'ROOT',tmp_path);monkeypatch.setattr(loader,'DATA',tmp_path/'data')
    app=AppTest.from_file(str(Path(__file__).parents[1]/'app.py'),default_timeout=60).run()
    for page in ['Upcoming Games','Team Comparison','Model Performance','Model Analysis','Team Power Rankings']:
        app.sidebar.radio[0].set_value(page).run();assert not app.exception

def test_rankings_dashboard_with_history(tmp_path):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from nfl_predictor.m3 import ratings_bundle
    data=tmp_path/'data';f=season_schedule()
    ratings_bundle(f,data/'ratings',pd.Timestamp('2023-10-01T00:00Z'))
    script=f"from pathlib import Path\nfrom nfl_predictor.m3_dashboard import render_rankings,render_matchup\nrender_rankings(Path({str(data)!r}), Path({str(tmp_path/'reports')!r}))"
    app=AppTest.from_string(script,default_timeout=60).run();assert not app.exception


def test_rating_export_integrity(tmp_path):
    from nfl_predictor.m3 import ratings_bundle
    f=pd.DataFrame([game()]);cutoff=pd.Timestamp('2023-09-08T00:00Z')
    a=ratings_bundle(f,tmp_path,cutoff);assert ratings_bundle(f,tmp_path,cutoff)==a
    (a/'history.csv').write_text('bad')
    with pytest.raises(ValueError,match='corrupt'):ratings_bundle(f,tmp_path,cutoff)

def test_targeted_features_preserve_full_history(dataset):
    from nfl_predictor.feature_engineering import build
    s,m=dataset;full=build(s,m)
    targeted=build(s,m,game_ids=['2023_5'])
    pd.testing.assert_frame_equal(full[full.game_id.eq('2023_5')].reset_index(drop=True),targeted.reset_index(drop=True))

def test_qb_evidence_rejects_future_observation():
    r=evidence();r['observed_at']=(pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=1)).isoformat()
    with pytest.raises(ValueError,match='future'):validate_verified(r)

def test_qb_refresh_preserves_verified_evidence_and_failure(tmp_path,monkeypatch):
    import nflreadpy as nfl
    import polars as pl
    from nfl_predictor.quarterbacks import save_context,cached_context,update_sources
    from nfl_predictor.integrity import digest
    initial=save_context(validate_verified(evidence()),tmp_path/'qb_context',[]);sha=digest(initial)
    raw=pl.DataFrame([dict(dt='2024-09-01T00:00Z',team='LV',gsis_id='id',player_name='QB',pos_abb='QB',pos_rank=1)])
    monkeypatch.setattr(nfl,'load_depth_charts',lambda _:raw)
    monkeypatch.setattr(nfl,'load_injuries',lambda _:pl.DataFrame())
    monkeypatch.setattr(nfl,'load_rosters_weekly',lambda _:pl.DataFrame())
    update_sources(tmp_path,[2024])
    f=cached_context(tmp_path/'qb_context');assert set(f.classification)=={'unknown','verified_pregame'} and digest(initial)==sha
    pointer=tmp_path/'qb_context/latest.json';pointer_hash=digest(pointer)
    def fail(_):raise OSError('source unavailable')
    monkeypatch.setattr(nfl,'load_injuries',fail)
    with pytest.raises(OSError):update_sources(tmp_path,[2024])
    assert digest(pointer)==pointer_hash
    metadata=json.loads(pointer.read_text());(pointer.parent/metadata['file']).write_bytes(b'bad')
    with pytest.raises(ValueError,match='checksum'):cached_context(tmp_path/'qb_context')

def test_source_zip_does_not_require_git(monkeypatch):
    from nfl_predictor.m3 import git_reference
    import subprocess
    def absent(*args,**kwargs):raise FileNotFoundError('git not installed')
    monkeypatch.setattr(subprocess,'check_output',absent)
    assert 'unavailable' in git_reference()

def test_verified_qb_experiments_use_matched_samples(dataset,tmp_path):
    from pathlib import Path
    from nfl_predictor.m3 import prepare,compare
    from nfl_predictor.quarterbacks import empty
    s,m=dataset;config=json.loads((Path(__file__).parents[1]/'config/m3_protocol.json').read_text())
    config['folds']=config['folds'][:1];config['bootstrap_replicates']=20
    frame=prepare(s,m,empty(),config,tmp_path/'features')
    extras=frame[frame.season.isin([2019,2020,2022])].copy()
    extras['game_id']='extra-'+extras.game_id
    extras['kickoff']=extras.kickoff+pd.Timedelta(days=30)
    frame=pd.concat([frame,extras],ignore_index=True)
    frame['qb_verified']=True;frame['qb_change_difference']=np.where(frame.week.mod(2).eq(0),1.,-1.)
    run=compare(frame,tmp_path/'reports',config)
    results=pd.read_parquet(run/'qb_matched_predictions.parquet')
    assert set(results.model)=={'logistic','qb_experimental'}
    assert results.groupby('model').game_id.nunique().nunique()==1
    assert json.loads((run/'metadata.json').read_text())['folds'][0]['qb_status']=='Matched QB-only sample, evaluated separately'
