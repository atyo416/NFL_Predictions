from pathlib import Path
from copy import deepcopy
import json
import numpy as np
import pandas as pd
import pytest
from nfl_predictor.ensemble import (BASES,PROBABILITIES,CLASSIFICATION,validate_matrix,
    EnsemblePredictor,weights_array,transform,fit_policies,calibrated_policies,policy_parameters)
from nfl_predictor.ensemble_analysis import fit_fold,fold_samples,select_policy,run,complementarity
from nfl_predictor.ensemble_data import aligned,identity,build_matrix,elo_features
from nfl_predictor.integrity import digest
from test_m5 import history_dataset


@pytest.fixture
def config():
    c=json.loads((Path(__file__).parents[1]/'config/m7_protocol.json').read_text())
    c.update(minimum_meta_games=8,isotonic_min_games=5,bootstrap_replicates=20)
    c['hgb_parameters']={**c['hgb_parameters'],'max_iter':5,'min_samples_leaf':2}
    return c


@pytest.fixture
def matrix():
    rows=[]
    rng=np.random.default_rng(42)
    for year in range(2019,2026):
        for i in range(40):
            kickoff=pd.Timestamp(f'{year}-09-01T17:00Z')+pd.Timedelta(days=i)
            signal=float(rng.normal());p=1/(1+np.exp(-signal));y=int(rng.random()<p)
            rows.append({'game_id':f'{year}_{i}','season':year,'week':i//3+1,'kickoff':kickoff,'data_cutoff':kickoff,'available_at':kickoff+pd.Timedelta(hours=8),'target':y,'completed':True,'home_score':24 if y else 10,'away_score':17,'home_team':'LV','away_team':'KC','classification':CLASSIFICATION,'generated_at':'actual current generation time','p_logistic':p,'p_boosting':.8*p+.1,'p_elo_margin':float(np.clip(p+rng.normal(0,.1),.01,.99)),**{'training_cutoff_'+name:pd.Timestamp(f'{year}-02-01T00:00Z') for name in BASES}})
    return pd.DataFrame(rows)


@pytest.mark.parametrize('weights',[[1/3]*3,[0,.5,.5],[.2,.6,.2],[.25,.5,.25],[.1,.7,.2]])
def test_fixed_math_and_probability_orientation(matrix,weights):
    predictor=EnsemblePredictor('test',weights=weights)
    p=predictor.predict_proba(matrix)
    np.testing.assert_allclose(p[:,1],matrix[PROBABILITIES].to_numpy()@weights)
    np.testing.assert_allclose(p.sum(axis=1),1)
    assert ((p>=0)&(p<=1)).all()


@pytest.mark.parametrize('weights',[[-.1,.8,.3],[.2,.2,.2],[1,0],[np.nan,0,1]])
def test_invalid_weights_rejected(weights):
    with pytest.raises(ValueError,match='weights'):weights_array(weights)


def test_logodds_clipping_and_missing_probability_rejection(matrix):
    assert np.isfinite(transform(np.array([[0,1,.5]]),'logits')).all()
    bad=matrix.copy();bad.loc[0,'p_logistic']=np.nan
    with pytest.raises(ValueError,match='Missing or invalid'):validate_matrix(bad)
    bad.loc[0,'p_logistic']=1.1
    with pytest.raises(ValueError,match='invalid'):validate_matrix(bad)


def test_alignment_reports_missing_ties_future_and_duplicates(matrix):
    bad=matrix.copy();bad.loc[0,'p_boosting']=np.nan
    bad.loc[1,['target','home_score','away_score']]=[np.nan,17,17]
    bad.loc[2,['target','completed']]=[np.nan,False]
    bad.loc[3,'available_at']=pd.Timestamp('2030-01-01T00:00Z')
    f,audit=aligned(bad,pd.Timestamp('2026-01-01T00:00Z'))
    assert len(f)==len(matrix)-4
    assert [audit[k] for k in ['missing_base_predictions','ties','incomplete_labels','unavailable_or_delayed_labels']]==[1,1,1,1]
    with pytest.raises(ValueError,match='Duplicate'):aligned(pd.concat([matrix,matrix.iloc[:1]]),pd.Timestamp('2026-01-01T00:00Z'))


def test_oos_cutoffs_and_retrospective_contract(matrix):
    bad=matrix.copy();bad.loc[0,'training_cutoff_logistic']=bad.loc[0,'data_cutoff']
    with pytest.raises(ValueError,match='In-sample'):validate_matrix(bad)
    bad=matrix.copy();bad.loc[0,'classification']='production_artifact_applied_to_earlier_game'
    with pytest.raises(ValueError,match='out-of-sample'):validate_matrix(bad)
    bad=matrix.copy();bad.loc[0,'data_cutoff']=bad.loc[0,'kickoff']+pd.Timedelta(seconds=1)
    with pytest.raises(ValueError,match='follows kickoff'):validate_matrix(bad)


def test_result_times_must_be_aware_and_follow_kickoff(matrix):
    bad=matrix.copy();bad.loc[0,'available_at']=bad.loc[0,'kickoff']-pd.Timedelta(seconds=1)
    with pytest.raises(ValueError,match='precedes kickoff'):validate_matrix(bad)
    bad=matrix.copy();bad['available_at']=bad.available_at.dt.tz_localize(None)
    with pytest.raises(ValueError,match='timezone'):validate_matrix(bad)


def test_optimizer_regularized_stack_determinism_and_serialization(matrix,config,tmp_path):
    import joblib
    meta,cal,ev,audit=fold_samples(matrix,2024,config)
    a,optimizer=fit_policies(meta,cal.data_cutoff.min(),config);b,_=fit_policies(meta,cal.data_cutoff.min(),config)
    assert optimizer['success'] and sum(optimizer['weights'])==pytest.approx(1.) and min(optimizer['weights'])>=0
    for name in a:
        np.testing.assert_allclose(a[name].predict_proba(ev),b[name].predict_proba(ev),rtol=0,atol=0)
        joblib.dump(a[name],tmp_path/'p.joblib');np.testing.assert_array_equal(joblib.load(tmp_path/'p.joblib').predict_proba(ev),a[name].predict_proba(ev))
    assert a['E5_logits'].estimator.coef_.shape==(1,3)
    calibrated,skipped=calibrated_policies(a,cal,ev.data_cutoff.min(),config,audit['meta_outcome_cutoff'])
    assert not skipped and len(calibrated)==24


def test_meta_calibration_overlap_and_delayed_labels(matrix,config):
    meta,cal,ev,audit=fold_samples(matrix,2024,config)
    bad=meta.copy();bad.loc[bad.index[0],'available_at']=cal.data_cutoff.min()
    with pytest.raises(ValueError,match='overlap'):fit_policies(bad,cal.data_cutoff.min(),config)
    raw,_=fit_policies(meta,cal.data_cutoff.min(),config)
    with pytest.raises(ValueError,match='overlap'):calibrated_policies(raw,cal,cal.available_at.max(),config,audit['meta_outcome_cutoff'])
    with pytest.raises(ValueError,match='overlap'):calibrated_policies(raw,cal,ev.data_cutoff.min(),config,cal.data_cutoff.min())
    bad=matrix.copy();index=bad[bad.season.eq(2022)].index[0];bad.loc[index,'available_at']=pd.Timestamp('2023-09-01T17:00Z')
    *_,audit=fold_samples(bad,2024,config);assert audit['excluded_delayed_meta_labels']==1


def test_adversarial_future_outcomes_cannot_change_earlier_stacking_or_selection(matrix,config):
    original,predictions,audit=fit_fold(matrix,2024,config)
    altered=matrix.copy();altered.loc[altered.season.eq(2025),'target']=1-altered.loc[altered.season.eq(2025),'target']
    future,predictions2,audit2=fit_fold(altered,2024,config)
    pd.testing.assert_frame_equal(predictions,predictions2)
    assert {n:policy_parameters(p) for n,p in original.items()}=={n:policy_parameters(p) for n,p in future.items()}
    assert audit==audit2
    develop=lambda m:pd.concat([fit_fold(m,y,config)[1] for y in config['development_seasons']])
    a=select_policy(develop(matrix),config);b=select_policy(develop(altered),config)
    assert a[:2]==b[:2];pd.testing.assert_frame_equal(a[2],b[2])


def test_missing_development_candidate_cannot_win_and_pair_differences(matrix,config):
    p=pd.concat([fit_fold(matrix,y,config)[1] for y in config['development_seasons']])
    selected,_,summary=select_policy(p,config)
    assert selected in summary.model.tolist()
    p=p[~(p.model.eq(selected)&p.season.eq(2022))]
    assert select_policy(p,config)[0]!=selected
    from nfl_predictor.analysis import paired_intervals
    paired=paired_intervals(p[p.model.isin(BASES)],20,reference='boosting')
    row=paired[paired.model.eq('logistic')&paired.metric.eq('brier')].iloc[0]
    expected=np.mean((matrix.loc[matrix.season.isin([2022,2023]),'p_logistic']-matrix.loc[matrix.season.isin([2022,2023]),'target'])**2)-np.mean((matrix.loc[matrix.season.isin([2022,2023]),'p_boosting']-matrix.loc[matrix.season.isin([2022,2023]),'target'])**2)
    assert row.difference==pytest.approx(expected)
    assert row.difference_low<=row.difference_high
    corr,pairs=complementarity(matrix);assert corr.disagreement_fraction.between(0,1).all() and set(pairs.bucket)=={'agree','disagree'}


@pytest.fixture
def experiment(history_dataset,config,tmp_path):
    s,m=history_dataset
    root=tmp_path/'project';root.mkdir();(root/'models').mkdir();(root/'models/production.joblib').write_bytes(b'original champion must never load during historical evaluation')
    (root/'data').mkdir();(root/'data/predictions.db').write_bytes(b'original sqlite bytes')
    frame,directory=build_matrix(s,m,root/'data',root,config)
    meta=json.loads((directory/'metadata.json').read_text())
    out=run(frame,meta,root/'reports/m7',root/'models/registry',config)
    return s,m,root,frame,meta,out


def test_actual_base_refits_chronology_cache_registry_dashboard(experiment,config):
    from nfl_predictor.registry import load_candidate
    from nfl_predictor.ensemble_registry import load_ensemble
    s,m,root,frame,meta,out=experiment
    validate_matrix(frame,True)
    assert (pd.to_datetime(frame.training_cutoff_logistic)<frame.kickoff).all()
    assert (root/'models/production.joblib').read_bytes().startswith(b'original champion')
    assert (root/'data/predictions.db').read_bytes()==b'original sqlite bytes'
    for row in meta['training']:assert int(row['target_season'])>int(row['training_cutoff'][:4])
    pointer=json.loads((out/'prospective_model.json').read_text());model,bases,md=load_ensemble(root/'models/registry',pointer['version'])
    assert model['activation_blocked'] and set(bases)==set(BASES)
    assert run(frame,meta,root/'reports/m7',root/'models/registry',config)==out
    c=pd.read_csv(out/'comparison.csv');assert c[c.period.eq('examined_2024_2025')].games.nunique()==1
    from streamlit.testing.v1 import AppTest
    script=f"from pathlib import Path\nfrom nfl_predictor.ensemble_dashboard import render_analysis\nrender_analysis(Path({str(root)!r}),Path({str(root/'data')!r}))"
    app=AppTest.from_string(script,default_timeout=60).run();assert not app.exception


def test_base_future_injection_preserves_prior_predictions_and_coefficients(experiment,config):
    s,m,root,frame,meta,out=experiment
    changed=s.copy();changed.loc[changed.season.eq(2025),'target']=1-changed.loc[changed.season.eq(2025),'target']
    changed.loc[changed.season.eq(2025),'home_score']=40
    modified=m.copy();modified.loc[modified.game_id.str.startswith('2025_'),'off_epa']=1000
    other,_=build_matrix(changed,modified,root/'data',root,config)
    pd.testing.assert_frame_equal(frame[frame.season.le(2024)].drop(columns='generated_at'),other[other.season.le(2024)].drop(columns='generated_at'))
    a=fit_fold(frame,2024,config);b=fit_fold(other,2024,config)
    pd.testing.assert_frame_equal(a[1],b[1]);assert a[2]==b[2]


def test_registry_incompatible_features_missing_base_and_checksum_rejected(experiment):
    from nfl_predictor.ensemble_registry import load_ensemble,verify_references
    from nfl_predictor.registry import load_candidate
    s,m,root,frame,meta,out=experiment;registry=root/'models/registry'
    version=json.loads((out/'prospective_model.json').read_text())['version'];model,_,_=load_ensemble(registry,version)
    bad=deepcopy(model);bad['base_refs']['logistic']['feature_schema']='future-incompatible'
    with pytest.raises(ValueError,match='feature'):verify_references(bad,registry)
    bad=deepcopy(model);bad['base_refs']['logistic']['version']='missing'
    with pytest.raises(ValueError,match='Missing'):verify_references(bad,registry)
    base=registry/'candidates'/model['base_refs']['boosting']['version']/'model.joblib';base.write_bytes(b'bad')
    with pytest.raises(ValueError,match='checksum'):load_candidate(registry,version)


def test_simultaneous_delayed_elo_and_live_configuration(history_dataset,config):
    s,m=history_dataset;s=s.copy()
    a=s[s.season.eq(2020)].index[:2];s.loc[a,'kickoff']=s.loc[a[0],'kickoff'];s.loc[a,'result_available_at']=s.loc[a[0],'kickoff']+pd.Timedelta(days=20)
    original=elo_features(s,config)
    other=s.copy();other.loc[a[0],'home_score']=100
    updated=elo_features(other,config)
    ids=s[s.kickoff.le(s.loc[a[0],'result_available_at'])&s.season.ge(2018)].game_id
    pd.testing.assert_frame_equal(original[original.game_id.isin(ids)],updated[updated.game_id.isin(ids)])


def test_issuance_immutable_grading_and_no_backdating(experiment,config,monkeypatch):
    from nfl_predictor.ensemble_forecasts import issue,records,grade,prospective_summary,probabilities
    from nfl_predictor.ensemble_registry import load_ensemble
    s,m,root,frame,meta,out=experiment;registry=root/'models/registry'
    version=json.loads((out/'prospective_model.json').read_text())['version'];now=pd.Timestamp.now(tz='UTC')
    s=s.copy();index=s[s.season.eq(2026)].index[-1];gid=s.loc[index,'game_id']
    s.loc[index,'kickoff']=now+pd.Timedelta(days=1);s.loc[index,['completed','target','home_score','away_score','result_available_at']]=[False,np.nan,np.nan,np.nan,pd.NaT]
    ledger=root/'data/m7/experimental_forecasts';cutoff=now-pd.Timedelta(minutes=1)
    first=issue(s,m,registry,version,config,ledger,cutoff,gid)
    assert len(first)==1 and first.iloc[0].designation=='experimental'
    file=next((ledger/'forecasts').glob('*.json'));sha=digest(file)
    again=issue(s,m,registry,version,config,ledger,cutoff,gid);assert len(again)==1 and digest(file)==sha
    revised=m.copy();revised.loc[revised.game_id.str.startswith('2026_'),'off_epa']=100
    with pytest.raises(ValueError,match='immutable'):issue(s,revised,registry,version,config,ledger,cutoff,gid)
    with pytest.raises(ValueError,match='future'):issue(s,m,registry,version,config,ledger,now+pd.Timedelta(hours=1),gid)
    with pytest.raises(ValueError,match='precede'):issue(s,m,registry,version,config,ledger,pd.Timestamp('2020-01-01T00:00Z'),gid)
    bad=deepcopy(config);bad['margin_elo']['k']=21
    with pytest.raises(ValueError,match='incompatible'):issue(s,m,registry,version,bad,ledger,cutoff,gid)
    issue(s,m,registry,version,config,ledger,cutoff+pd.Timedelta(seconds=30),gid)
    assert len(records(ledger))==2 and prospective_summary(ledger)['unique_games']==1
    monkeypatch.setattr('nfl_predictor.ensemble_forecasts.utc_now',lambda:now+pd.Timedelta(days=2))
    with pytest.raises(ValueError,match='unstarted'):issue(s,m,registry,version,config,ledger,None,gid)
    s.loc[index,['completed','target','home_score','away_score']]=[True,1,24,17]
    assert len(grade(s,ledger))==2;grade(s,ledger);assert len(list((ledger/'results').glob('*.json')))==2
    assert prospective_summary(ledger)['graded']==2 and digest(file)==sha
    assert prospective_summary(ledger)['binary_metrics']['games']==1
    s.loc[index,['target','home_score']]=[np.nan,17]
    monkeypatch.setattr('nfl_predictor.ensemble_forecasts.utc_now',lambda:now+pd.Timedelta(days=2,hours=1))
    grade(s,ledger);assert prospective_summary(ledger)['ties']==1 and digest(file)==sha
    payload=json.loads(file.read_text());payload['payload']['home_probability']=.99;file.write_text(json.dumps(payload))
    with pytest.raises(ValueError,match='checksum'):records(ledger)


def test_cli_and_file_based_windows_contract(monkeypatch,capsys):
    from nfl_predictor.cli import main
    monkeypatch.setattr('sys.argv',['cli','--help'])
    with pytest.raises(SystemExit) as exc:main()
    assert exc.value.code==0
    out=capsys.readouterr().out
    for command in ['build-ensemble-predictions','compare-m7','report-m7','forecast-ensemble','grade-ensemble']:assert command in out
    windows=(Path(__file__).parents[1]/'scripts/windows_acceptance.ps1').read_text()
    assert "'report-m6'" in windows and "'report-m7'" in windows and "'forecast-ensemble'" in windows
    assert "'-c'" not in windows
