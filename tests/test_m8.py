from pathlib import Path
from copy import deepcopy
import json
import sqlite3
import pandas as pd
import numpy as np
import pytest
from nfl_predictor.market_math import decimal_odds,implied,market_pair,value_at_probability,payout
from nfl_predictor.odds_store import connect,rows,key
from nfl_predictor.odds_provider import ingest,OddsAPIv4,ENDPOINT
from nfl_predictor.odds_matching import match,team
from nfl_predictor.betting_demo import fixture_data,run_demo
from nfl_predictor.market_comparison import compare_at,audit_matches,quote_issues
from nfl_predictor.paper_betting import issue,settle,ledger_view,performance,void_wager,closing_line
from nfl_predictor.market_benchmark import benchmark,write_benchmark
from nfl_predictor.integrity import digest

ROOT=Path(__file__).parents[1]
AT=pd.Timestamp('2023-10-07T17:00:00Z')


@pytest.fixture
def config():
    c=json.loads((ROOT/'config/m8_protocol.json').read_text());c['bootstrap_replicates']=20;return c


@pytest.fixture
def lab(tmp_path,monkeypatch):
    db=connect(tmp_path/'lab.db');fixture,s,forecasts=fixture_data(ROOT)
    payload=json.loads(fixture.read_text());rules=payload['rules']
    for rule in rules.values():rule['rules_reference']='https://unit.test/documented-rules'
    monkeypatch.setattr('nfl_predictor.odds_provider.utc_now',lambda:AT-pd.Timedelta(seconds=30))
    ingest(db,json.dumps([payload['data'][0]]),'json','verified_archive',rules)
    forecasts=[f for f in forecasts if f['game_id']=='synthetic_m8_1']
    for f in forecasts:f['classification']='genuine_saved_forecast';f['forecast_id']=key(f)
    s=s.iloc[:1].copy();s['completed']=False;s[['home_score','away_score']]=np.nan;s['status']='scheduled'
    monkeypatch.setattr('nfl_predictor.paper_betting.utc_now',lambda:AT)
    yield db,s,forecasts,payload,rules
    db.close()


@pytest.mark.parametrize('odds,decimal,probability',[(150,2.5,.4),(-150,5/3,.6),(100,2,.5),(-100,2,.5),(300,4,.25)])
def test_american_odds_conversion(odds,decimal,probability):
    assert float(decimal_odds(odds))==pytest.approx(decimal)
    assert implied(odds)==pytest.approx(probability)


@pytest.mark.parametrize('value',[0,99,-99,150.5,'nonsense',float('nan'),float('inf'),True,None])
def test_invalid_american_prices(value):
    with pytest.raises(ValueError):decimal_odds(value)


def test_decimal_vig_ev_and_probability_boundaries():
    assert decimal_odds('2.50','decimal')==decimal_odds(150)
    pair=market_pair(decimal_odds(-110),decimal_odds(-110));assert pair['overround']>1
    assert pair['no_vig_home']==pytest.approx(.5) and pair['no_vig_home']+pair['no_vig_away']==pytest.approx(1)
    ev=value_at_probability(.45,2.5,.03)
    assert ev['ev_per_unit']==pytest.approx(.125) and ev['expected_roi_percent']==pytest.approx(12.5)
    assert ev['minimum_probability_for_threshold']==pytest.approx(.412)
    assert value_at_probability(0,2.5)['ev_per_unit']==-1
    assert value_at_probability(1,2.5)['ev_per_unit']==1.5
    for p,d in [(-.1,2),(.5,1),(.5,'1e999'),(.5,'1e308'),(1.1,2)]:
        with pytest.raises(ValueError):value_at_probability(p,d)
    with pytest.raises(ValueError):decimal_odds(1,'decimal')


def test_import_idempotence_and_raw_immutability(lab):
    db,s,f,payload,rules=lab;before=rows(db,'quotes')[0]
    ingest(db,json.dumps([payload['data'][0]]),'json','verified_archive',rules)
    assert len(rows(db,'quotes'))==1 and rows(db,'quotes')[0]==before
    assert db.execute('SELECT count(*) FROM raw').fetchone()[0]==1
    for table in ['quotes','raw','receipts']:
        with pytest.raises(sqlite3.IntegrityError,match='append-only'):db.execute(f'DELETE FROM {table}')
        db.rollback()


def test_invalid_schema_and_missing_sides_leave_cache_intact(lab):
    db,s,f,payload,rules=lab;before=rows(db,'quotes')
    with pytest.raises(ValueError,match='Expected'):ingest(db,'{"unexpected": 1}')
    bad=deepcopy(payload['data'][0]);bad['bookmakers'][0]['markets'][0]['outcomes'].pop()
    result=ingest(db,json.dumps([bad]),'json','verified_archive',rules)
    assert result['issues'] and rows(db,'quotes')==before
    empty=deepcopy(bad);empty['bookmakers']=[]
    result=ingest(db,json.dumps([empty]),'json','verified_archive',rules);assert result['issues']


def test_csv_provenance_and_coherent_market_pairs(lab):
    from io import StringIO
    db,s,f,payload,rules=lab;q=rows(db,'quotes')[0]
    base={k:q[k] for k in ['provider','bookmaker','event_id','market','home_team','away_team','kickoff','season','snapshot_at','quote_at','source_reference']}
    data=pd.DataFrame([{**base,'selection':q['home_team'],'price':150,'odds_format':'american'},{**base,'selection':q['away_team'],'price':-170,'odds_format':'american'}])
    result=ingest(db,data.to_csv(index=False).encode(),'csv');assert len(result['quote_ids'])==1
    with pytest.raises(ValueError,match='exactly two'):ingest(db,data.iloc[:1].to_csv(index=False).encode(),'csv')
    data.loc[0,'quote_at']='2023-10-07T16:59:00'
    with pytest.raises(ValueError,match='exactly two|timezone'):ingest(db,data.to_csv(index=False).encode(),'csv')
    with pytest.raises(ValueError,match='missing columns'):ingest(db,b'price\n150\n','csv')


def test_game_matching_aliases_neutral_reschedule_and_ambiguity(lab,config):
    db,s,f,payload,rules=lab;q=rows(db,'quotes')[0]
    assert team('Oakland Raiders')==team('OAK')=='LV'
    assert match(q,s)['status']=='matched'
    neutral=s.copy();neutral['neutral']=True;assert match(q,neutral)['neutral']
    moved=s.copy();moved['kickoff']+=pd.Timedelta(hours=1);assert match(q,moved)['status']=='kickoff_changed_review'
    reverse=s.copy();reverse[['home_team','away_team']]=reverse[['away_team','home_team']].to_numpy()
    assert match(q,reverse)['status']=='home_away_reversed_review'
    duplicate=s.copy();duplicate['game_id']='other';assert match(q,pd.concat([s,duplicate]))['status']=='ambiguous'
    with pytest.raises(ValueError,match='Unknown'):team('Las Vegas Raders')


def test_future_quote_forecast_and_closing_injection_cannot_change_past_decision(lab,config,monkeypatch):
    db,s,forecasts,payload,rules=lab
    a,_=compare_at(db,s,forecasts,AT,config)
    later=deepcopy(payload['data'][0]);later['id']='later-duplicate-event';later['bookmakers'][0]['last_update']='2023-10-07T17:01:00Z';later['bookmakers'][0]['markets'][0]['outcomes'][0]['price']=1000
    monkeypatch.setattr('nfl_predictor.odds_provider.utc_now',lambda:AT+pd.Timedelta(minutes=2))
    ingest(db,json.dumps([later]),'json','verified_archive',rules)
    future=deepcopy(forecasts[0]);future.update(created_at='2023-10-07T17:01:00+00:00',data_cutoff='2023-10-07T17:01:00+00:00',home_probability=.99,forecast_id='future')
    b,_=compare_at(db,s,forecasts+[future],AT,config)
    assert a==b
    assert any(audit['status']=='duplicate_provider_events_review' for audit in audit_matches(db,s,config))
    strategy_before=json.loads((ROOT/'config/m8_protocol.json').read_text())
    assert config['thresholds']==strategy_before['thresholds']  # no outcome-driven selection exists


def test_stale_missing_late_information_and_rule_guards(lab,config):
    db,s,f,payload,rules=lab
    o,_=compare_at(db,s,f,AT+pd.Timedelta(hours=1),config);assert not o
    bad=deepcopy(f)
    for r in bad:r['data_cutoff']='2023-10-07T17:01:00+00:00'
    o,x=compare_at(db,s,bad,AT,config);assert not o and x
    q=rows(db,'quotes')[0];assert 'not_pregame' in quote_issues(q,pd.Timestamp(q['kickoff']),config)
    o,x=compare_at(db,s,[],AT,config);assert not o and any('no_valid_asof_forecast' in r['reasons'] for r in x)
    with pytest.raises(ValueError,match='backdated'):issue(db,s,f,config,cutoff=AT-pd.Timedelta(days=1))


def test_paper_dry_run_immutable_idempotent_and_no_completed_issue(lab,config):
    db,s,f,payload,rules=lab
    assert issue(db,s,f,config,dry_run=True)['would_issue']
    assert not rows(db,'wagers')
    first=issue(db,s,f,config);assert first['saved']==1
    original=rows(db,'wagers')[0];assert original['selection']=='LV' and original['stake_units']=='1'
    assert original['minimum_probability_for_threshold']==pytest.approx(.412)
    assert issue(db,s,f,config)['saved']==0 and rows(db,'wagers')[0]==original
    with pytest.raises(sqlite3.IntegrityError,match='append-only'):db.execute("UPDATE wagers SET payload='{}'")
    db.rollback()
    s['completed']=True;assert issue(db,s,f,config,threshold=.05)['saved']==0


@pytest.mark.parametrize('home_score,tie_rule,expected,profit',[(24,'push','win',1.5),(10,'push','loss',-1),(17,'push','push',0),(17,'void','void',0)])
def test_settlement_outcomes_idempotence_and_revision(lab,config,monkeypatch,home_score,tie_rule,expected,profit):
    db,s,f,payload,rules=lab
    if tie_rule=='void':
        rules['synthetic_book']['tie_rule']='void'
        db.execute('BEGIN');db.rollback()  # no mutation of existing immutable quote
        newer=deepcopy(payload['data'][0]);newer['bookmakers'][0]['last_update']='2023-10-07T16:59:10Z';ingest(db,json.dumps([newer]),'json','verified_archive',rules)
    issue(db,s,f,config);w=rows(db,'wagers')[0]
    s.loc[:,['completed','home_score','away_score','status']]=[True,home_score,17,'final']
    monkeypatch.setattr('nfl_predictor.paper_betting.utc_now',lambda:AT+pd.Timedelta(days=2))
    assert len(settle(db,s,config))==1
    view=ledger_view(db);assert view[0]['status']==expected and float(view[0]['profit_units'])==pytest.approx(profit)
    assert not settle(db,s,config)
    s['home_score']=30 if home_score!=30 else 10
    events=settle(db,s,config)
    assert events and events[0]['supersedes']
    assert rows(db,'wagers')[0]==w


def test_cancel_reschedule_unknown_and_manual_void(lab,config,monkeypatch):
    db,s,f,payload,rules=lab;issue(db,s,f,config);w=rows(db,'wagers')[0]
    s['kickoff']+=pd.Timedelta(days=1);events=settle(db,s,config);assert events[0]['status']=='void'
    correction=void_wager(db,w['wager_id'],'Corrected synthetic decision for audit')
    assert correction['kind']=='manual_void' and correction['supersedes']
    assert void_wager(db,w['wager_id'],'Corrected synthetic decision for audit')==correction
    assert ledger_view(db)[0]['status']=='void'
    with pytest.raises(ValueError,match='reason'):void_wager(db,w['wager_id'],'')


def test_roi_drawdown_and_unique_game_conventions():
    wagers=[]
    for i,profit in enumerate([1.,-1.,-1.,2.]):
        wagers.append({'game_id':str(i),'wager_id':str(i),'status':'win' if profit>0 else 'loss','stake_units':'1','profit_units':str(profit),'ev_per_unit':.03,'settlement':{'available_at':f'2023-10-{i+1:02d}T00:00:00Z'}})
    result=performance(wagers);assert result['net_simulated_profit_units']==1 and result['realized_roi']==.25
    assert result['maximum_drawdown_units']==2 and result['longest_losing_streak']==2
    assert performance([])['realized_roi'] is None
    duplicated=deepcopy(wagers);duplicated[1]['game_id']=duplicated[0]['game_id']
    assert performance(duplicated)['unique_games']==3


def test_closing_requires_verified_same_book_and_stays_out_of_entry(lab,config):
    db,s,f,payload,rules=lab;issue(db,s,f,config);w=rows(db,'wagers')[0];q=rows(db,'quotes')[0]
    close=deepcopy(q);close.update(quote_id='closing',snapshot_at='2023-10-08T16:55:00+00:00',quote_at='2023-10-08T16:55:00+00:00',home_decimal='2.2',closing_status='verified_final_pregame',closing_reference='https://unit.test/closing')
    result=closing_line(w,[close],{'closing':w['game_id']},config);assert result['price_improvement_ratio']>0
    close['bookmaker']='other';assert closing_line(w,[close],{'closing':w['game_id']},config)['status']=='unavailable_verified_closing'
    close['bookmaker']=w['bookmaker'];close['closing_status']='last_observed'
    assert closing_line(w,[close],{'closing':w['game_id']},config)['status']=='unavailable_verified_closing'


class Response:
    def __init__(self,status,content,headers=None):self.status_code=status;self.content=content;self.headers=headers or {}


class Session:
    def __init__(self,responses):self.responses=list(responses);self.calls=[]
    def get(self,url,**kwargs):self.calls.append((url,kwargs));return self.responses.pop(0)


def test_provider_quota_parameters_rate_limit_and_secret_redaction(tmp_path,config,monkeypatch):
    db=connect(tmp_path/'provider.db');credential='unit-secret-not-for-storage';monkeypatch.setenv('ODDS_API_KEY',credential)
    session=Session([Response(200,b'[]',{'x-requests-remaining':'499','x-requests-used':'1','x-requests-last':'1'})])
    result=OddsAPIv4(session,sleep=lambda s:None).fetch(db,config)
    assert result['quota']['x-requests-remaining']==499 and session.calls[0][0]==ENDPOINT
    assert session.calls[0][1]['params']['markets']=='h2h' and session.calls[0][1]['params']['oddsFormat']=='american'
    with pytest.raises(RuntimeError,match='cooldown'):OddsAPIv4(session).fetch(db,config)
    assert len(session.calls)==1 and credential not in '\n'.join(db.iterdump())
    db.close()


def test_provider_429_and_failure_preserve_cache_and_do_not_leak_keys(tmp_path,config,monkeypatch):
    db=connect(tmp_path/'provider.db');monkeypatch.setenv('ODDS_API_KEY','unit-secret-never-log')
    session=Session([Response(429,b'{"error":"apiKey=unit-secret-never-log"}',{'Retry-After':'60'})])
    with pytest.raises(RuntimeError,match='HTTP 429') as exc:OddsAPIv4(session,sleep=lambda s:pytest.fail('must not sleep 60 seconds')).fetch(db,config)
    assert 'unit-secret' not in str(exc.value) and 'unit-secret' not in '\n'.join(db.iterdump())
    assert not rows(db,'quotes');db.close()


def test_missing_key_and_bounded_retry(tmp_path,config,monkeypatch):
    db=connect(tmp_path/'provider.db');monkeypatch.delenv('ODDS_API_KEY',raising=False)
    session=Session([])
    with pytest.raises(RuntimeError,match='not configured'):OddsAPIv4(session).fetch(db,config)
    assert not session.calls
    monkeypatch.setenv('ODDS_API_KEY','unit-credential')
    session=Session([Response(503,b'{}'),Response(200,b'[]')]);waits=[]
    OddsAPIv4(session,sleep=waits.append).fetch(db,config)
    assert len(session.calls)==2 and waits==[1];db.close()


def test_misconfigured_fetch_cannot_remove_cost_bounds(tmp_path,config,monkeypatch):
    db=connect(tmp_path/'provider.db');session=Session([]);monkeypatch.setenv('ODDS_API_KEY','unit-credential')
    for field,value in [('max_http_attempts',100),('minimum_fetch_interval_seconds',0),('max_retry_delay_seconds',60)]:
        bad=deepcopy(config);bad[field]=value
        with pytest.raises(ValueError,match='fetch policy'):OddsAPIv4(session).fetch(db,bad)
    assert not session.calls and not rows(db,'receipts');db.close()


def test_nonempty_betting_dashboard_shows_margin_and_forecast_provenance(lab,config,tmp_path):
    from nfl_predictor.betting_report import build
    from streamlit.testing.v1 import AppTest
    db,s,f,payload,rules=lab;root=tmp_path/'project';data=root/'data'
    run=build(db,s,f,config,root/'reports/m8',AT)
    # SQLite backup is a reversible test copy; the UI receives no write connection.
    path=data/'m8/lab.db';path.parent.mkdir(parents=True);copy=sqlite3.connect(path);db.backup(copy);copy.close()
    before=digest(path)
    script=f"from pathlib import Path\nfrom nfl_predictor.betting_dashboard import render\nrender(Path({str(root)!r}),Path({str(data)!r}))"
    app=AppTest.from_string(script,default_timeout=60).run();assert not app.exception
    assert any('bookmaker_margin' in view.value.columns for view in app.dataframe)
    assert any('artifact_sha256' in view.value.columns for view in app.dataframe)
    assert digest(path)==before


def test_benchmark_alignment_cohorts_and_synthetic_exclusion(lab,config,monkeypatch,tmp_path):
    db,s,f,payload,rules=lab;s.loc[:,['completed','home_score','away_score','status']]=[True,24,17,'final']
    monkeypatch.setattr('nfl_predictor.market_benchmark.utc_now',lambda:AT+pd.Timedelta(days=2))
    frame,opportunities,excluded=benchmark(db,s,f,config)
    assert set(frame.model)=={'official_logistic','boosting','ensemble','market_no_vig'} and frame.game_id.nunique()==1
    assert set(frame.cohort)=={'24h'}
    write_benchmark(frame,tmp_path/'report',config);metrics=pd.read_csv(tmp_path/'report/benchmark.csv')
    assert metrics.games.eq(1).all() and metrics.difference_low.le(metrics.difference_high).all()
    bad=deepcopy(f);bad.pop();frame,_,_=benchmark(db,s,bad,config);assert frame.empty


def test_synthetic_demo_cli_and_read_only_dashboard(tmp_path,config,monkeypatch,capsys):
    result=run_demo(ROOT,tmp_path/'demo');assert result['artificial_games']==3 and result['unique_game_count']==3
    assert result['statuses']=={'win':9,'loss':9,'push':9} and result['real_market_results'] is None
    from nfl_predictor.betting_report import build
    from streamlit.testing.v1 import AppTest
    root=tmp_path/'ui';data=root/'data';db=connect(data/'m8/lab.db')
    _,s,f=fixture_data(ROOT);run=build(db,s,[],config,root/'reports/m8');db.close();before=digest(data/'m8/lab.db')
    script=f"from pathlib import Path\nfrom nfl_predictor.betting_dashboard import render\nrender(Path({str(root)!r}),Path({str(data)!r}))"
    app=AppTest.from_string(script,default_timeout=60).run();assert not app.exception
    assert digest(data/'m8/lab.db')==before
    from nfl_predictor.cli import main
    monkeypatch.setattr('sys.argv',['cli','--help'])
    with pytest.raises(SystemExit):main()
    output=capsys.readouterr().out
    assert all(name in output for name in ['fetch-odds','import-odds','audit-odds','issue-paper-bets','report-m8'])


def test_official_repository_is_read_only_and_requires_exact_artifact(tmp_path):
    from types import SimpleNamespace
    import joblib
    from nfl_predictor.database import connect as official_connect,insert
    from nfl_predictor.market_forecasts import ForecastRepository
    root=tmp_path/'project';(root/'models').mkdir(parents=True);data=root/'data'
    model={'version':'fixture-logistic','pipeline':SimpleNamespace(named_steps={'logisticregression':None}),'training_cutoff':'2023-09-01T00:00:00+00:00'}
    joblib.dump(model,root/'models/production.joblib');db=official_connect(data/'predictions.db')
    record={'game_id':'g','season':2023,'week':5,'home_team':'LV','away_team':'KC','kickoff':'2023-10-08T17:00:00+00:00','created_at':'2023-10-07T16:58:00+00:00','data_cutoff':'2023-10-07T16:57:00+00:00','model_version':'fixture-logistic','home_probability':.45}
    insert(db,record);db.close();sha=digest(data/'predictions.db');artifact=digest(root/'models/production.joblib')
    repository=ForecastRepository(root,data);f=repository.read()
    assert len(f)==1 and f[0]['artifact_sha256']==artifact and digest(data/'predictions.db')==sha
    with pytest.raises(ValueError,match='Unsafe'):repository.artifact('../../escape')
    (root/'models/production.joblib').unlink()
    fresh=ForecastRepository(root,data);assert not fresh.read() and fresh.issues


def test_postkickoff_odds_and_unknown_rules_never_issue(lab,config,monkeypatch):
    db,s,f,payload,rules=lab
    unknown=deepcopy(payload['data'][0]);unknown['bookmakers'][0]['last_update']='2023-10-07T16:59:15Z'
    ingest(db,json.dumps([unknown]),'json','verified_archive')
    o,_=compare_at(db,s,f,AT,config);assert o and all(not r['paper_eligible'] and r['rules_warning'] for r in o)
    assert issue(db,s,f,config)['saved']==0
    post=deepcopy(payload['data'][0]);post['bookmakers'][0]['last_update']='2023-10-08T17:01:00Z'
    monkeypatch.setattr('nfl_predictor.odds_provider.utc_now',lambda:AT+pd.Timedelta(days=2))
    ingest(db,json.dumps([post]),'json','verified_archive',rules)
    assert not rows(db,'quotes')[-1]['pregame_quote']


def test_historical_import_cannot_become_prospective_and_orientation_is_checked(lab,config,monkeypatch):
    db,s,f,payload,rules=lab
    wrong=deepcopy(f)
    for r in wrong:r['home_team'],r['away_team']=r['away_team'],r['home_team']
    o,x=compare_at(db,s,wrong,AT,config);assert not o and any('forecast_team_mismatch' in r['reasons'] for r in x)
    q=rows(db,'quotes')[0]
    assert 'not_observed_by_decision' in quote_issues(q,AT-pd.Timedelta(minutes=1),config)
    with pytest.raises(ValueError,match='mode'):compare_at(db,s,f,AT,config,'unrecognized')


def test_future_outcome_injection_does_not_choose_entry_or_threshold(lab,config):
    from nfl_predictor.paper_betting import select,strategy
    db,s,f,payload,rules=lab
    a,_=compare_at(db,s,f,AT,config);definition=strategy(config)
    altered=s.copy();altered['home_score']=10000;altered['away_score']=0
    b,_=compare_at(db,altered,f,AT,config)
    assert a==b and select(a,definition,config)==select(b,definition,config)
    assert definition==strategy(config)


def test_cancel_unknown_rule_requires_review_and_suspended_quote_is_excluded(lab,config,monkeypatch):
    db,s,f,payload,rules=lab;rules=deepcopy(rules);rules['synthetic_book']['cancel_rule']='manual_review'
    newer=deepcopy(payload['data'][0]);newer['bookmakers'][0]['last_update']='2023-10-07T16:59:10Z'
    ingest(db,json.dumps([newer]),'json','verified_archive',rules);issue(db,s,f,config)
    s['status']='canceled';events=settle(db,s,config);assert events[0]['status']=='review' and events[0]['profit_units'] is None
    assert performance(ledger_view(db))['realized_roi'] is None
    q=rows(db,'quotes')[0];q['availability']='suspended'
    assert 'market_suspended' in quote_issues(q,AT,config)


def test_csv_fixture_is_never_silently_promoted(tmp_path):
    db=connect(tmp_path/'quotes.db')
    result=ingest(db,(ROOT/'tests/fixtures/m8/historical_example.csv').read_bytes(),'csv','verified_archive')
    assert result['source_kind']=='synthetic' and rows(db,'quotes')[0]['source_kind']=='synthetic'
    db.close()


def test_m8_windows_script_keeps_frozen_model_selection():
    script=(ROOT/'scripts/windows_m8_acceptance.ps1').read_text()
    for command in ['build-adjusted-efficiency','forecast-ensemble','demo-m8','report-m8']:assert command in script
    assert "'compare-m7'" not in script and "'report-m7'" not in script
    assert '[switch]$LiveOdds' in script and "'-c'" not in script


def test_future_game_missing_scores_remain_missing_in_report(lab,config,tmp_path):
    from nfl_predictor.betting_report import build
    db,s,f,payload,rules=lab
    assert s.home_score.isna().all()
    run=build(db,s,f,config,tmp_path/'reports',AT)
    metadata=json.loads((run/'metadata.json').read_text())
    assert metadata['real_matched_probability_games']==0
    assert s.home_score.isna().all() and metadata['paper_summary']['realized_roi'] is None


def test_unobserved_live_quote_is_not_an_archival_observation(lab,config):
    db,s,f,payload,rules=lab;q=rows(db,'quotes')[0]
    q['source_kind']='live';q['received_at']='2023-10-07T17:01:00+00:00'
    assert 'live_quote_not_observed_by_decision' in quote_issues(q,AT,config,'reconstructed')
    q['source_kind']='verified_archive'
    assert not quote_issues(q,AT,config,'reconstructed')


def test_historical_inference_uses_earlier_cutoff_not_kickoff(tmp_path,config,monkeypatch):
    from nfl_predictor.market_forecasts import historical_inference
    root=tmp_path/'project';(root/'config').mkdir(parents=True)
    (root/'config/m8_protocol.json').write_text(json.dumps(config))
    (root/'config/m7_protocol.json').write_text('{}')
    run=root/'reports/m7/frozen';run.mkdir(parents=True);(run.parent/'latest.json').write_text('{"run":"frozen"}')
    version='m7-ensemble-2024-unit';(run/'registry_versions.json').write_text(json.dumps([version]))
    (run/'selection.json').write_text('{"method":"E1_equal__raw"}')
    (run/'outputs.json').write_text(json.dumps({p.name:digest(p) for p in run.iterdir()}))
    versions={'logistic':'base-logistic','boosting':'base-boosting'}
    for v in [version]+list(versions.values()):
        path=root/'models/registry/candidates'/v;path.mkdir(parents=True);(path/'model.joblib').write_bytes(b'unit-artifact')
    (root/'models/registry/candidates'/version/'metadata.json').write_text('{"parameters":{"method":"E1_equal","calibration_method":"raw"}}')
    model={'training_cutoff':'2024-02-01T00:00:00+00:00','base_refs':{k:{'version':v} for k,v in versions.items()}}
    bases={k:{'training_cutoff':'2024-02-01T00:00:00+00:00'} for k in versions}
    monkeypatch.setattr('nfl_predictor.market_forecasts.load_ensemble',lambda *args:(model,bases,{}))
    kickoff=pd.Timestamp('2024-10-10T17:00:00Z');decision=kickoff-pd.Timedelta(hours=24)
    s=pd.DataFrame([{'game_id':'g','season':2024,'home_team':'LV','away_team':'KC','kickoff':kickoff,'completed':True}])
    def inference(schedules,metrics,ensemble,loaded,protocol,cutoff,now,game_id):
        assert cutoff==now==decision and cutoff<kickoff
        assert not schedules.iloc[0].completed
        return pd.DataFrame([{'p_logistic':.4,'p_boosting':.5,'ensemble_probability':.45}]),{'asof':str(cutoff)}
    monkeypatch.setattr('nfl_predictor.market_forecasts.probabilities',inference)
    db=connect(tmp_path/'lab.db');records=historical_inference(root,s,pd.DataFrame(),'g',decision,db)
    assert all(r['classification']=='retrospective_oos_inference' and pd.Timestamp(r['data_cutoff'])==decision for r in records)
    assert s.iloc[0].completed  # source schedule never mutated
    historical_inference(root,s,pd.DataFrame(),'g',decision,db)
    assert len(rows(db,'forecasts'))==3
    db.close()
