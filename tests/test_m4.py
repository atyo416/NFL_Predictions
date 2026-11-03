from pathlib import Path
import copy
import json
import joblib
import numpy as np
import pandas as pd
import pytest
from test_engine import dataset
from nfl_predictor.boosting import fit_boosting,calibrated
from nfl_predictor.m4_features import FEATURE_SETS,prepare
from nfl_predictor.m4 import select_configuration,permutation_diagnostics,run
from nfl_predictor.analysis import fit_calibrators
from nfl_predictor.registry import register,load_candidate,activate,rollback
from nfl_predictor.integrity import digest

@pytest.fixture
def protocol():
    c=json.loads((Path(__file__).parents[1]/'config/m4_protocol.json').read_text())
    c['bootstrap_replicates']=20;c['permutation_repeats']=1
    c['configurations']={k:{**v,'max_iter':8,'min_samples_leaf':2} for k,v in list(c['configurations'].items())[:2]}
    c['folds']=c['folds'][:1]
    return c

@pytest.fixture
def frame(dataset,protocol,tmp_path):
    return prepare(*dataset,protocol,tmp_path/'features')

def test_boosting_probabilities_missing_and_serialization(frame,protocol,tmp_path):
    tr=frame[frame.season.le(2020)];features=FEATURE_SETS['elo'];params=protocol['configurations']['conservative']
    a=fit_boosting(tr,features,params);b=fit_boosting(tr,features,params)
    p=a['pipeline'].predict_proba(frame[features]);assert np.allclose(p.sum(axis=1),1) and ((p>=0)&(p<=1)).all()
    np.testing.assert_array_equal(p,b['pipeline'].predict_proba(frame[features]))
    joblib.dump(a,tmp_path/'candidate.joblib');np.testing.assert_array_equal(p,joblib.load(tmp_path/'candidate.joblib')['pipeline'].predict_proba(frame[features]))
    assert a['pipeline'].estimator.early_stopping is False
    assert frame.loc[frame.game_id.eq('2018_1'),'off_epa'].isna().all()
    with pytest.raises(ValueError,match='Missing'):a['pipeline'].predict_proba(frame.drop(columns=['off_epa']))
    with pytest.raises(ValueError,match='Unsafe'):fit_boosting(tr,['target'],params)
    with pytest.raises(ValueError,match='early stopping'):fit_boosting(tr,features,{**params,'early_stopping':True})

def test_development_selection_cannot_see_future_targets(frame,protocol):
    selected,a,_=select_configuration(frame,protocol)
    other=frame.copy();other.loc[other.season.ge(2022),'target']=1-other.loc[other.season.ge(2022),'target']
    selected_b,b,_=select_configuration(other,protocol)
    assert selected==selected_b and a.validation_season.max()==2021
    pd.testing.assert_frame_equal(a.drop(columns='runtime_seconds'),b.drop(columns='runtime_seconds'))

def test_m4_future_injection_and_live_elo_cutoff(dataset,protocol,tmp_path):
    s,m=dataset;a=prepare(s,m,protocol,tmp_path/'a')
    changed_s=s.copy();changed_m=m.copy()
    changed_s.loc[changed_s.season.eq(2025),'home_score']=1000
    changed_m.loc[changed_m.game_id.str.startswith('2025'),'off_epa']=1e9
    b=prepare(changed_s,changed_m,protocol,tmp_path/'b')
    features=FEATURE_SETS['interactions'];before=a.season.le(2024)
    pd.testing.assert_frame_equal(a.loc[before,features],b.loc[before,features])
    model=fit_boosting(a[a.season.le(2021)],features,protocol['configurations']['conservative'])
    np.testing.assert_array_equal(model['pipeline'].predict_proba(a.loc[before,features]),model['pipeline'].predict_proba(b.loc[before,features]))
    # A known result whose eligibility occurs AFTER issuance but BEFORE game kickoff
    # must not enter a live feature row.
    cutoff=s.loc[s.game_id.eq('2023_1'),'kickoff'].iloc[0]+pd.Timedelta(hours=1)
    upcoming=['2023_2']
    live=prepare(s,m,protocol,cutoff=cutoff,game_ids=upcoming)
    changed=s.copy();changed.loc[changed.game_id.eq('2023_1'),'away_score']=1000
    live_changed=prepare(changed,m,protocol,cutoff=cutoff,game_ids=upcoming)
    pd.testing.assert_frame_equal(live[features],live_changed[features])

def test_interaction_perspectives_and_cache(frame,dataset,protocol,tmp_path):
    valid=frame.home_rating_off_epa.notna()&frame.away_rating_def_epa.notna()
    np.testing.assert_allclose(frame.loc[valid,'home_attack_defense'],frame.loc[valid,'home_rating_off_epa']*frame.loc[valid,'away_rating_def_epa'])
    a=prepare(*dataset,protocol,tmp_path)
    pd.testing.assert_frame_equal(a,prepare(*dataset,protocol,tmp_path))
    p=next(tmp_path.glob('*.parquet'));p.write_bytes(b'bad')
    with pytest.raises(ValueError,match='checksum'):prepare(*dataset,protocol,tmp_path)

def test_calibration_separation(frame,protocol):
    model=fit_boosting(frame[frame.season.le(2020)],FEATURE_SETS['elo'],protocol['configurations']['conservative'])
    cal=frame[frame.season.eq(2021)];ev=frame[frame.season.eq(2022)]
    methods=fit_calibrators(model,cal,ev.kickoff.min(),min_games=200)
    fitted=calibrated(model,'sigmoid',methods['sigmoid'],cal)
    assert fitted['training_cutoff']>model['training_cutoff']
    assert np.allclose(fitted['pipeline'].predict_proba(ev[model['features']]).sum(axis=1),1)
    with pytest.raises(ValueError,match='overlaps'):fit_calibrators(model,cal,cal.kickoff.min())


def test_candidate_registry_and_reviewed_rollback(frame,protocol,tmp_path):
    model=fit_boosting(frame[frame.season.le(2020)],FEATURE_SETS['elo'],protocol['configurations']['conservative'])
    model['feature_config']={k:protocol[k] for k in ['elo','short_rest_days','extended_rest_days']}
    registry=tmp_path/'registry';prod=tmp_path/'production.joblib'
    legacy={'version':'original','features':['off_epa'],'pipeline':None};joblib.dump(legacy,prod);original=digest(prod)
    path=register(model,registry,{'report_reference':'report.md'})
    assert register(model,registry,{'report_reference':'report.md'})==path
    loaded,metadata=load_candidate(registry,model['version']);assert metadata['designation']=='experimental'
    assert digest(prod)==original
    report=tmp_path/'review.md';report.write_text('Independent evaluation and Windows acceptance reviewed by operator.')
    decision={'candidate_version':model['version'],'decision':'approve','reviewer':'test operator','rationale':'synthetic workflow verification only','windows_verified':False,'artifact_sha256':metadata['artifact_sha256'],'evidence_report':str(report),'evidence_sha256':digest(report)}
    d=tmp_path/'decision.json';d.write_text(json.dumps(decision))
    with pytest.raises(ValueError,match='Windows'):activate(registry,prod,d)
    assert digest(prod)==original
    decision['windows_verified']=True;d.write_text(json.dumps(decision));event=activate(registry,prod,d)
    assert digest(prod)==metadata['artifact_sha256'] and joblib.load(prod)['version']==model['version']
    assert (registry/'champions'/f'{original}.joblib').exists()
    rollback(registry,prod,event['event_id']);assert digest(prod)==original and joblib.load(prod)['version']=='original'
    with pytest.raises(ValueError,match='unrelated'):rollback(registry,prod,event['event_id'])
    (path/'model.joblib').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):load_candidate(registry,model['version'])

def test_permutation_importance_uses_signal_and_is_deterministic(protocol):
    rng=np.random.default_rng(3);n=240
    signal=rng.normal(size=n)
    f=pd.DataFrame({'season':2020,'kickoff':pd.date_range('2020-01-01',periods=n,tz='UTC'),'target':(signal>0).astype(int),'signal':signal,'noise':rng.normal(size=n)})
    model=fit_boosting(f,['signal','noise'],{**protocol['configurations']['conservative'],'max_iter':60})
    result=permutation_diagnostics(model,f,{'signal':['signal'],'noise':['noise']},3)
    pd.testing.assert_frame_equal(result,permutation_diagnostics(model,f,{'signal':['signal'],'noise':['noise']},3))
    assert result.groupby('group').brier_increase.mean()['signal']>result.groupby('group').brier_increase.mean()['noise']

def test_experiment_alignment_registry_dashboard_and_reproduction(frame,protocol,tmp_path):
    registry=tmp_path/'registry'
    a=run(frame,tmp_path/'a',registry,protocol)
    b=run(frame,tmp_path/'b',tmp_path/'registry-b',protocol)
    assert run(frame,tmp_path/'a',registry,protocol)==a
    pd.testing.assert_frame_equal(pd.read_parquet(a/'predictions.parquet'),pd.read_parquet(b/'predictions.parquet'))
    pd.testing.assert_frame_equal(pd.read_csv(a/'comparison.csv'),pd.read_csv(b/'comparison.csv'))
    assert json.loads((a/'metadata.json').read_text())['selected_configuration']==json.loads((b/'metadata.json').read_text())['selected_configuration']
    c=pd.read_csv(a/'comparison.csv');assert c.games.nunique()==1
    from streamlit.testing.v1 import AppTest
    script=f"from pathlib import Path\nfrom nfl_predictor.m4_dashboard import render\nrender(Path({str(tmp_path/'a')!r}))"
    app=AppTest.from_string(script,default_timeout=60).run();assert not app.exception
    meta=json.loads((a/'registry_metadata.json').read_text());assert meta and all(v['designation']=='experimental' for v in meta)
    bad=copy.deepcopy(protocol);bad['development_folds'][-1]['validation']=2023
    with pytest.raises(ValueError,match='Development outcomes'):run(frame,tmp_path/'bad',registry,bad)
    (a/'comparison.csv').write_text('corrupt')
    with pytest.raises(ValueError,match='checksum'):run(frame,tmp_path/'a',registry,protocol)

def test_production_dispatch_supports_reviewed_candidate(dataset,frame,protocol,tmp_path):
    from nfl_predictor.database import connect
    from nfl_predictor.predictions import predict
    model=fit_boosting(frame[frame.season.le(2021)],FEATURE_SETS['interactions'],protocol['configurations']['conservative'])
    model['feature_config']={k:protocol[k] for k in ['elo','short_rest_days','extended_rest_days']}
    s,m=dataset;s=s.copy()
    s.loc[s.season.eq(2026),'kickoff']=pd.Timestamp.now(tz='UTC')+pd.Timedelta(days=10)
    s.loc[s.season.eq(2026),['home_score','away_score','target']]=np.nan;s.loc[s.season.eq(2026),'completed']=False
    db=connect(tmp_path/'p.db');p=predict(s,m,model,db)
    assert len(p)==6 and p.official.all() and np.allclose(p.home_probability+p.away_probability,1)

def test_m4_cli_contract(monkeypatch,capsys):
    from nfl_predictor.cli import main
    monkeypatch.setattr('sys.argv',['cli','--help'])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==0
    output=capsys.readouterr().out
    for command in ['train-m4','compare-m4','report-m4','activate-model','rollback-model']:
        assert command in output

def test_registry_rejects_path_identifiers(tmp_path):
    with pytest.raises(ValueError,match='Unsafe'):load_candidate(tmp_path,'..')

def test_all_empty_training_columns_do_not_learn_from_future(frame,protocol):
    f=frame[frame.season.le(2020)].copy();f['all_empty']=np.nan
    model=fit_boosting(f,['off_epa','all_empty'],protocol['configurations']['conservative'])
    assert model['excluded_all_missing_features']==['all_empty']
    before=model['pipeline'].predict_proba(f[['off_epa','all_empty']])
    f['all_empty']=1000
    np.testing.assert_array_equal(before,model['pipeline'].predict_proba(f[['off_epa','all_empty']]))
    f['all_empty']=np.nan
    intercept=fit_boosting(f,['all_empty'],protocol['configurations']['conservative'])
    probabilities=intercept['pipeline'].predict_proba(f[['all_empty']])[:,1]
    np.testing.assert_allclose(probabilities,np.full(len(f),f.target.mean()))
