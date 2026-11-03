from pathlib import Path
from dataclasses import replace
import copy
import json
import numpy as np
import pandas as pd
import pytest
from nfl_predictor.adjusted_efficiency import AdjustmentParameters,ratings_at,shrink_residual,build_adjusted,observations,matchup,ADJUSTED
from nfl_predictor.player_performance import aggregate_qbs,qb_rating
from nfl_predictor.personnel import normalize_evidence,team_context,eligible_evidence,import_evidence,load_evidence,save_prospective,coverage_gate
from test_m3 import game


def adjustment_history():
    rows=[]
    def add(team,opponent,y,i):rows.append({'game_id':str(i),'team':team,'opponent':opponent,'season':2020,'kickoff':pd.Timestamp('2020-09-01T00:00Z'),'available_at':pd.Timestamp('2020-09-01T08:00Z'),'off_epa':y,'off_success':.5+y/5})
    add('KC','DEN',.2,'a');add('LV','MIA',.2,'b')
    for i in range(8):add('BUF','DEN',-.4,f'c{i}');add('BUF','MIA',.4,f'd{i}')
    return pd.DataFrame(rows)


def test_opponent_signs_and_controlled_strong_weak():
    assert shrink_residual([.2],[-.2])>shrink_residual([.2],[.2])
    h=adjustment_history();state=ratings_at(h,2020,pd.Timestamp('2020-09-10T00:00Z')).set_index('team')
    assert state.loc['KC','off_epa_strength']>state.loc['LV','off_epa_strength']
    assert state.loc['DEN','def_epa_allowed_strength']<state.loc['MIA','def_epa_allowed_strength']
    m=matchup(state.loc['KC'],state.loc['LV'])
    assert m['adj_off_epa_diff']>0 and m['overall_epa_advantage']==pytest.approx(m['adj_off_epa_diff']+m['adj_def_epa_advantage'])


def test_equal_sparse_bounded_and_deterministic():
    h=adjustment_history();h['off_epa']=0.;h['off_success']=.5
    at=pd.Timestamp('2020-09-10T00:00Z');a=ratings_at(h,2020,at)
    assert a.off_epa_strength.eq(0).all() and a.def_epa_allowed_strength.eq(0).all()
    pd.testing.assert_frame_equal(a,ratings_at(h,2020,at))
    h.loc[0,'off_epa']=1e9;bounded=ratings_at(h,2020,at)
    assert bounded.off_epa_strength.abs().le(.5).all()
    rookie=bounded[bounded.team.eq('HOU')].iloc[0];assert rookie.epa_games==0
    with pytest.raises(ValueError):AdjustmentParameters(iterations=0)


def test_prior_transition_and_exact_availability():
    h=adjustment_history();at=pd.Timestamp('2020-09-01T08:00Z')
    assert ratings_at(h,2020,at).epa_games.eq(0).all()
    assert ratings_at(h,2020,at+pd.Timedelta(seconds=1)).epa_games.sum()>0
    prior=ratings_at(h,2021,pd.Timestamp('2021-09-01T00:00Z')).set_index('team')
    expected=.5*(.2-h.off_epa.mean())
    assert prior.loc['KC','off_epa_strength']==pytest.approx(expected)
    with pytest.raises(ValueError,match='timezone'):ratings_at(h,2020,pd.Timestamp('2020-09-10'))

from test_m5 import history_dataset


def test_adversarial_future_opponent_and_cache(history_dataset,tmp_path):
    s,m=history_dataset;s=s[s.season.between(2019,2021)];m=m[m.game_id.isin(s.game_id)]
    original=build_adjusted(s,m,directory=tmp_path/'a')
    altered=m.copy();altered.loc[altered.game_id.eq('2020_6'),'off_epa']=999999
    original_files=list((tmp_path/'a').glob('*.parquet'));old_count=len(original_files)
    other=build_adjusted(s,altered,directory=tmp_path/'a')
    assert len(list((tmp_path/'a').glob('*.parquet')))>old_count
    cutoff=s.loc[s.game_id.eq('2020_4'),'kickoff'].iloc[0];ids=s.loc[s.kickoff.le(cutoff),'game_id']
    pd.testing.assert_frame_equal(original[original.game_id.isin(ids)].reset_index(drop=True),other[other.game_id.isin(ids)].reset_index(drop=True))
    pd.testing.assert_frame_equal(original,build_adjusted(s,m,directory=tmp_path/'a'))
    original_files[0].write_bytes(b'bad')
    with pytest.raises(ValueError,match='checksum'):build_adjusted(s,m,directory=tmp_path/'a')


def test_simultaneous_and_delayed_adjustment(history_dataset):
    s,m=history_dataset;s=s[s.season.eq(2020)].copy();m=m[m.game_id.isin(s.game_id)]
    first=s.iloc[0].kickoff;s.loc[s.index[1],'kickoff']=first
    pre=build_adjusted(s,m);assert pre.iloc[0][ADJUSTED].equals(pre.iloc[1][ADJUSTED])
    s.loc[s.index[0],'result_available_at']=s.iloc[-1].kickoff+pd.Timedelta(days=1)
    changed=m.copy();changed.loc[changed.game_id.eq(s.iloc[0].game_id),'off_epa']=99999
    pd.testing.assert_frame_equal(build_adjusted(s,m),build_adjusted(s,changed))


def qb_plays():
    return pd.DataFrame([{'game_id':'a','posteam':team,'play_type':'pass','epa':value,'qb_dropback':1,'qb_kneel':0,'qb_spike':0,'passer_player_id':player,'passer_player_name':player,'complete_pass':1,'pass_attempt':1,'interception':0,'sack':0} for team,player,value in [('LV','qb1',.3),('LV','qb2',-.2),('KC','qb3',.1)]])


def test_multiple_qbs_no_current_game_and_rookie():
    s=pd.DataFrame([game(home_qb_id='qb1',home_qb_name='QB One')])
    f=aggregate_qbs(qb_plays(),s);assert set(f.player_id)=={'qb1','qb2','qb3'}
    before=qb_rating(f,'qb1',s.iloc[0].kickoff,2023);assert before['epa_per_dropback'] is None
    after=qb_rating(f,'qb1',s.iloc[0].kickoff+pd.Timedelta(days=1),2023)
    assert after['dropbacks']==1 and after['epa_per_dropback']<.3
    assert qb_rating(f,'rookie',s.iloc[0].kickoff+pd.Timedelta(days=1),2023)['epa_per_dropback'] is None
    changed=qb_plays();changed.loc[0,'epa']=99999
    assert qb_rating(aggregate_qbs(changed,s),'qb1',s.iloc[0].kickoff,2023)==before


def test_qb_identity_team_change_and_meaningful_samples():
    s=pd.DataFrame([game(home_qb_id='qb1'),game('b',kickoff='2023-09-14T00:00Z',home='BUF',away='KC',week=2)])
    p=qb_plays();q=p.copy();q['game_id']='b';q.loc[q.passer_player_id.eq('qb1'),'posteam']='BUF'
    f=aggregate_qbs(pd.concat([p,q]),s)
    r=qb_rating(f,'qb1',pd.Timestamp('2023-09-20T00:00Z'),2023)
    assert r['career_dropbacks']==2 and r['last_team']=='BUF' and r['last_eligible_game']=='b'


def evidence(player='qb2',status='confirmed_starter',position='QB'):
    return {'game_id':'b','team':'LV','player_id':player,'position':position,'source_name':'reviewed source','source_reference':'https://example.test/report','source_at':'2023-09-12T00:00Z','observed_at':'2023-09-12T01:00Z','forecast_cutoff':'2023-09-13T00:00Z','availability':status,'quality':'independently verified archive','verification_status':'verified_pregame','is_starter':True,'coverage_groups':'[]'}


def context_sources():
    s=pd.DataFrame([game(home_qb_id='qb1'),game('b',kickoff='2023-09-14T00:00Z',week=2)])
    return s,aggregate_qbs(qb_plays(),s)


def test_evidence_timestamps_unknown_retrospective_and_conflicts():
    s,p=context_sources();at=pd.Timestamp('2023-09-14T00:00Z')
    r=normalize_evidence(pd.DataFrame([evidence()]));c=team_context(s,p,r,'b','LV',at)
    assert c['expected_starter_id']=='qb2' and c['previous_observed_starter']['player_id']=='qb1'
    assert c['expected_performance']['epa_per_dropback']<c['previous_performance']['epa_per_dropback']
    old=copy.deepcopy(evidence());old['verification_status']='retrospective';old['source_at']=None
    assert team_context(s,p,normalize_evidence(pd.DataFrame([old])),'b','LV',at)['expected_starter_id'] is None
    bad=evidence();bad['source_at']=None
    with pytest.raises(ValueError,match='Verified'):normalize_evidence(pd.DataFrame([bad]))
    late=evidence();late['source_at']='2023-09-14T00:00Z';late['observed_at']='2023-09-14T01:00Z';late['forecast_cutoff']='2023-09-14T02:00Z'
    assert eligible_evidence(normalize_evidence(pd.DataFrame([late])),'b','LV',at).empty
    conflict=evidence('qb3')
    assert team_context(s,p,normalize_evidence(pd.DataFrame([evidence(),conflict])),'b','LV',at)['expected_starter_id'] is None


def test_ruled_out_supersedes_starter_and_coverage_unknown():
    s,p=context_sources();new=evidence('qb2','ruled_out');new.update(source_at='2023-09-13T01:00Z',observed_at='2023-09-13T02:00Z',forecast_cutoff='2023-09-13T03:00Z')
    r=normalize_evidence(pd.DataFrame([evidence(),new]));c=team_context(s,p,r,'b','LV',pd.Timestamp('2023-09-14T00:00Z'))
    assert c['expected_starter_id'] is None and c['position_groups']['OL']['unavailable_starters'] is None
    unavailable=evidence('lineman','ruled_out','OT');unavailable['coverage_groups']='["OL"]'
    c=team_context(s,p,normalize_evidence(pd.DataFrame([unavailable])),'b','LV',pd.Timestamp('2023-09-14T00:00Z'))
    assert c['position_groups']['OL']['unavailable_starters']==1


def test_evidence_append_integrity_and_genuine_context(tmp_path):
    s,p=context_sources();file=tmp_path/'evidence.json';file.write_text(json.dumps([evidence()]))
    directory=tmp_path/'ledger';a=import_evidence(file,directory);sha=__import__('hashlib').sha256(a.read_bytes()).hexdigest()
    import_evidence(file,directory);r=load_evidence(directory);assert len(r)==1 and __import__('hashlib').sha256(a.read_bytes()).hexdigest()==sha
    s.loc[s.game_id.eq('b'),'kickoff']=pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=5);s.loc[s.game_id.eq('b'),'completed']=False
    snapshot=save_prospective(s,p,r,'b',tmp_path/'snapshots');payload=json.loads(snapshot.read_text())
    assert payload['kind']=='prospective_personnel_context_not_official_forecast'
    with pytest.raises(ValueError,match='started'):save_prospective(s,p,r,'a',tmp_path/'snapshots')
    latest=json.loads((directory/'latest.json').read_text());(directory/latest['file']).write_bytes(b'bad')
    with pytest.raises(ValueError,match='checksum'):load_evidence(directory)

from test_m5 import config as history_config

@pytest.fixture
def m6_config():
    c=json.loads((Path(__file__).parents[1]/'config/m6_protocol.json').read_text())
    c['folds']=c['folds'][:1];c['bootstrap_replicates']=20;c['permutation_repeats']=1
    c['hgb_parameters']={**c['hgb_parameters'],'max_iter':8,'min_samples_leaf':2}
    return c


def test_efficiency_framework_serialization_and_coverage_gate(history_dataset,m6_config,tmp_path):
    from nfl_predictor.history_features import reconstruct,attach_elo
    from nfl_predictor.personnel import game_features,empty_evidence
    from nfl_predictor.m6 import run
    from nfl_predictor.registry import load_candidate
    s,m=history_dataset;f=reconstruct(s,m,tmp_path/'features')[0];f=attach_elo(f,s,m6_config['elo'])
    f=f.merge(build_adjusted(s,m),on='game_id').merge(game_features(s,pd.DataFrame(),empty_evidence()),on='game_id')
    modern=s[s.season.ge(2018)]
    from nfl_predictor.feature_engineering import build
    reference=build(modern,m[m.game_id.isin(modern.game_id)])
    run_a=run(f,reference,tmp_path/'reports',tmp_path/'registry',m6_config)
    run_b=run(f,reference,tmp_path/'repeated',tmp_path/'other-registry',m6_config)
    pd.testing.assert_frame_equal(pd.read_parquet(run_a/'predictions.parquet'),pd.read_parquet(run_b/'predictions.parquet'))
    coverage=pd.read_csv(run_a/'personnel_coverage.csv');assert coverage.status.eq('skipped_insufficient_verified_coverage').all()
    c=pd.read_csv(run_a/'comparison.csv');assert c.games.nunique()==1
    version=json.loads((run_a/'registry_versions.json').read_text())[0];model,metadata=load_candidate(tmp_path/'registry',version)
    assert model['activation_blocked'] and metadata['adjustment_version']=='opponent-additive-m6-v1'
    # Match serialized candidate probabilities on identical inputs.
    source=pd.read_parquet(run_a/'predictions.parquet');ev=f[f.season.eq(2022)&f.target.notna()]
    np.testing.assert_allclose(model['pipeline'].predict_proba(ev[model['features']])[:,1],source[source.model.eq('A_raw')].probability)
    assert run(f,reference,tmp_path/'reports',tmp_path/'registry',m6_config)==run_a
    from streamlit.testing.v1 import AppTest
    root=tmp_path/'ui';(root/'reports/m6').mkdir(parents=True)
    import shutil
    shutil.copytree(run_a,root/'reports/m6'/run_a.name)
    (root/'reports/m6/latest.json').write_text(json.dumps({'run':run_a.name}))
    script=f"from pathlib import Path\nfrom nfl_predictor.m6_dashboard import render_analysis\nrender_analysis(Path({str(root)!r}))"
    app=AppTest.from_string(script,default_timeout=60).run();assert not app.exception


def test_personnel_matched_experiments_only_on_eligible_games(history_dataset,m6_config,tmp_path):
    from nfl_predictor.history_features import reconstruct,attach_elo
    from nfl_predictor.personnel import game_features,empty_evidence,QB_FEATURES,PLAYER_FEATURES
    from nfl_predictor.m6 import run
    from nfl_predictor.feature_engineering import build
    s,m=history_dataset;f=attach_elo(reconstruct(s,m,tmp_path/'f')[0],s,m6_config['elo'])
    f=f.merge(build_adjusted(s,m),on='game_id').merge(game_features(s,pd.DataFrame(),empty_evidence()),on='game_id')
    f['qb_verified']=f.week.le(3);f['player_verified']=f.week.le(3);f['verified_qb_team_count']=2*f.qb_verified.astype(int)
    for name in QB_FEATURES+PLAYER_FEATURES:f[name]=np.where(f.week.mod(2).eq(0),.1,-.1)
    m6_config.update(personnel_min_training_games=5,personnel_min_evaluation_games=2)
    modern=s[s.season.ge(2018)];reference=build(modern,m[m.game_id.isin(modern.game_id)])
    result=run(f,reference,tmp_path/'reports',tmp_path/'registry',m6_config)
    matched=pd.read_parquet(result/'personnel_matched_predictions.parquet')
    assert set(matched.experiment)=={'E_qb','F_ol','G_adjusted_qb_ol'}
    for _,g in matched.groupby('experiment'):
        groups=g.groupby('model').game_id.apply(set).tolist();assert groups[0]==groups[1]
        assert g.game_id.nunique()==3


def test_unknown_roles_and_conflicting_nonqb_reports():
    s,p=context_sources();out=evidence('tackle','ruled_out','OT');out['coverage_groups']='["OL"]';out['is_starter']=None
    context=team_context(s,p,normalize_evidence(pd.DataFrame([out])),'b','LV',pd.Timestamp('2023-09-14T00:00Z'))
    assert context['position_groups']['OL']['unavailable_starters'] is None
    other=copy.deepcopy(out);other['availability']='questionable';other['is_starter']=True
    context=team_context(s,p,normalize_evidence(pd.DataFrame([out,other])),'b','LV',pd.Timestamp('2023-09-14T00:00Z'))
    assert context['position_groups']['OL']['unavailable_starters'] is None


def test_cli_contract_and_qb_missing_optional_data(monkeypatch,capsys):
    from nfl_predictor.cli import main
    monkeypatch.setattr('sys.argv',['cli','--help'])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==0
    out=capsys.readouterr().out
    assert all(command in out for command in ['build-adjusted-efficiency','audit-personnel','compare-m6','report-m6','import-personnel','snapshot-personnel'])
    p=qb_plays().drop(columns=['complete_pass','pass_attempt','interception','sack'])
    f=aggregate_qbs(p,pd.DataFrame([game()]))
    assert f.dropbacks.sum()==3 and f.cpoe.isna().all()


def test_prospective_snapshot_tampering_and_bad_context_cutoffs(tmp_path):
    from nfl_predictor.personnel import empty_evidence,read_prospective
    s,p=context_sources();records=empty_evidence()
    with pytest.raises(ValueError,match='timezone'):team_context(s,p,records,'b','LV',pd.Timestamp('2023-09-13'))
    with pytest.raises(ValueError,match='not in'):team_context(s,p,records,'b','BUF',pd.Timestamp('2023-09-13T00:00Z'))
    s.loc[s.game_id.eq('b'),'kickoff']=pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=1);s.loc[s.game_id.eq('b'),'completed']=False
    file=save_prospective(s,p,records,'b',tmp_path);assert read_prospective(file)['game_id']=='b'
    value=json.loads(file.read_text());value['game_id']='tampered';file.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='checksum'):read_prospective(file)
