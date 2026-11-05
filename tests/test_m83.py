import json
import pandas as pd
import pytest
from nfl_predictor import prospective as p
from nfl_predictor.ensemble_forecasts import records,grade,_append

@pytest.fixture
def sample(monkeypatch):
    now=pd.Timestamp('2026-11-04T17:30Z');monkeypatch.setattr(p,'utc_now',lambda:now)
    s=pd.DataFrame([dict(game_id='g',season=2026,week=9,game_type='REG',kickoff=now+pd.Timedelta(hours=24,minutes=30),home_team='KC',away_team='BUF',home_score=None,away_score=None,completed=False,neutral=0)])
    def infer(*args):return {n:dict(probability=.6,version='v1',artifact_path='fixture',artifact_sha256='fixture') for n in ['official_logistic','boosting','ensemble']},[]
    return s,infer,now

@pytest.mark.parametrize('hours,state',[(26,'upcoming'),(25,'on_time'),(24,'on_time'),(23,'missed'),(0,'started')])
def test_utc_checkpoints(hours,state):
    now=pd.Timestamp('2026-11-04T12:00-05:00');target,actual=p.checkpoint(now+pd.Timedelta(hours=hours),now)
    assert actual==state and target.tzinfo is not None
    with pytest.raises(ValueError):p.checkpoint(now,now,-1)


def test_immutable_dedup_and_reschedule(sample,tmp_path):
    s,infer,now=sample;p.issue('.', '.',s,pd.DataFrame(),tmp_path,inference=infer)
    original=records(tmp_path);assert len(original)==1
    p.issue('.', '.',s,pd.DataFrame(),tmp_path,inference=lambda *a:pytest.fail('Duplicate inference'))
    assert records(tmp_path)==original
    s['kickoff']+=pd.Timedelta(hours=1)
    assert p.plan(s,tmp_path)[0]['schedule_changed']
    assert p.comparison(tmp_path,s)['schedule_change_exclusions']==1


def test_missed_and_late(sample,tmp_path):
    s,infer,now=sample;s['kickoff']-=pd.Timedelta(hours=2)
    p.issue('.', '.',s,pd.DataFrame(),tmp_path,inference=infer);assert not records(tmp_path)
    assert list((tmp_path/'checkpoints').glob('*.json'))
    p.issue('.', '.',s,pd.DataFrame(),tmp_path,late=True,inference=infer)
    assert records(tmp_path)[0]['cohort']=='late'


def test_missing_artifacts_and_no_substitution(sample,tmp_path):
    s,infer,now=sample
    values,issues=p.infer(tmp_path,tmp_path,s,pd.DataFrame(),s.iloc[0].to_dict(),now)
    assert not values and len(issues)==2
    p.issue('.', '.',s,pd.DataFrame(),tmp_path,inference=lambda *a:({},['missing artifact']))
    assert not records(tmp_path)


def test_grading_corrections_and_matching(sample,tmp_path,monkeypatch):
    s,infer,now=sample;p.issue('.', '.',s,pd.DataFrame(),tmp_path,inference=infer)
    import nfl_predictor.ensemble_forecasts as ef
    monkeypatch.setattr(ef,'utc_now',lambda:now+pd.Timedelta(days=4))
    s['completed']=True;s['home_score']=24;s['away_score']=17
    grade(s,tmp_path);result=p.comparison(tmp_path,s)
    assert result['graded']==1 and len(result['metrics'])==6 and result['paired']
    original=records(tmp_path);s['home_score']=10
    monkeypatch.setattr(ef,'utc_now',lambda:now+pd.Timedelta(days=4,seconds=1))
    grade(s,tmp_path)
    assert len(list((tmp_path/'results').glob('*.json')))==2 and records(tmp_path)==original
    assert p.comparison(tmp_path,s)['metrics'][0]['accuracy']==0
    bad=original[0].copy();bad['classification']='retrospective'
    # Existing append helper refuses mutations at a stable forecast identity.
    with pytest.raises(ValueError):_append(tmp_path/'forecasts',bad['forecast_id'],bad)


def test_market_observation_cutoff(sample):
    from nfl_predictor.odds_provider import normalized_pair
    s,infer,now=sample;g=s.iloc[0];f=dict(game_id='g',forecast_id='f',home_team='KC',away_team='BUF',kickoff=g.kickoff.isoformat(),created_at=now.isoformat(),data_cutoff=now.isoformat())
    q=normalized_pair(dict(provider='fixture',bookmaker='book',event_id='e',market='h2h',home_team='KC',away_team='BUF',kickoff=g.kickoff.isoformat(),snapshot_at=now.isoformat(),quote_at=now.isoformat(),season=2026,source_reference='fixture',home_price=-110,away_price=110,odds_format='american'),now,'raw','live')
    assert p.market_matches([f],[q],{'max_quote_age_minutes':60})
    q['received_at']=(now+pd.Timedelta(minutes=1)).isoformat()
    assert not p.market_matches([f],[q],{'max_quote_age_minutes':60})


def test_dry_run_report_preservation(sample,tmp_path,monkeypatch):
    s,infer,now=sample
    import nfl_predictor.spread_benchmark as sb
    monkeypatch.setattr(sb,'load_compact',lambda data:(s,pd.DataFrame(),[{'retrieved_at':now.isoformat()}]))
    (tmp_path/'config').mkdir();(tmp_path/'config/m8_protocol.json').write_text('{}')
    before=list(tmp_path.rglob('*'));result=p.weekly(tmp_path,tmp_path,dry_run=True,include_odds=True)
    assert result['writes']==0 and list(tmp_path.rglob('*'))==before
    result=p.weekly(tmp_path,tmp_path,report_only=True)
    assert result['forecasts']==0 and not (tmp_path/'m83').exists()


def test_missing_api_key_does_not_block(sample,tmp_path,monkeypatch):
    s,infer,now=sample
    import nfl_predictor.spread_benchmark as sb
    monkeypatch.setattr(sb,'load_compact',lambda data:(s,pd.DataFrame(),[{'retrieved_at':now.isoformat()}]))
    monkeypatch.setattr(p,'infer',infer);monkeypatch.delenv('ODDS_API_KEY',raising=False)
    (tmp_path/'config').mkdir();(tmp_path/'config/m8_protocol.json').write_text(json.dumps({'max_attempts':1,'minimum_fetch_interval_seconds':60}))
    # Use the actual default fetch policy, which validates before checking the key.
    from pathlib import Path
    (tmp_path/'config/m8_protocol.json').write_text((Path(__file__).parents[1]/'config/m8_protocol.json').read_text())
    result=p.weekly(tmp_path,tmp_path,include_odds=True)
    assert result['forecasts']==1 and result['issues']
