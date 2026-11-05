import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from nfl_predictor import targeted_errors as t
from test_m91a import diagnostic


def schedule():
    rows=[]
    for year in [2018,2019]:
        for week in range(1,7):
            at=pd.Timestamp(f'{year}-09-{week*4:02d}T17:00Z')
            rows.append(dict(game_id=f'{year}_{week}',season=year,week=week,game_type='REG',kickoff=at,completed=True,
                             home_team='LV',away_team='KC',home_score=24,away_score=17,home_coach='A' if year==2018 or week<=2 else 'B',away_coach='K',home_qb_id='qb',away_qb_id='other'))
    return pd.DataFrame(rows)


def test_market_outcome_independent_groups():
    f=diagnostic();g=t.market_groups(f)
    assert g.set_index('game_id').loc['a','market_group']=='unanimous_opposite_market'
    changed=f.copy();changed['target']=1-changed.target;changed['error']=~changed.error;changed['market_correct']=~changed.market_correct
    other=t.market_groups(changed)
    assert g[['game_id','market_group']].equals(other[['game_id','market_group']])
    assert not g.market_correct_shared_failure.equals(other.market_correct_shared_failure)
    with pytest.raises(ValueError,match='Three unique'):t.market_groups(f.iloc[1:])


def test_shared_failure_definition():
    f=diagnostic();f['error']=True;f['market_correct']=True
    g=t.market_groups(f);assert g.market_correct_shared_failure.all() and not g.all_predictors_wrong.any()
    f['market_correct']=False;g=t.market_groups(f)
    assert g.all_predictors_wrong.all() and not g.market_correct_shared_failure.any()


def test_chronological_standings_no_future_or_target_scores():
    s=schedule();game=s[s.game_id.eq('2019_3')]
    a=t.pregame_context(s,game).set_index('team')
    assert a.loc['LV','wins_before']==2 and a.loc['KC','losses_before']==2
    assert a.latest_prior_result.lt(game.iloc[0].kickoff).all()
    altered=s.copy();altered.loc[altered.season.eq(2019)&altered.week.ge(3),'home_score']=0
    pd.testing.assert_frame_equal(a,t.pregame_context(altered,game).set_index('team'))
    delayed=s.copy();delayed['result_available_at']=delayed.kickoff+pd.Timedelta(hours=8)
    delayed.loc[delayed.game_id.eq('2019_2'),'result_available_at']=game.iloc[0].kickoff
    assert t.pregame_context(delayed,game).set_index('team').loc['LV','wins_before']==1
    pending=s.copy();pending['completed']=False
    assert t.pregame_context(pending,game).completed_before.eq(0).all()


def test_unknown_vs_verified_playoff():
    game=schedule().iloc[-1].to_dict();at=game['kickoff']
    assert t.verified_playoff_status([],game,'LV')=='unknown'
    row=dict(game_id=game['game_id'],team='LV',status='berth_clinched',verification='verified_pregame',source_reference='fixture://reviewed',published_at=at-pd.Timedelta(days=2),captured_at=at-pd.Timedelta(days=1),preserved_at=at-pd.Timedelta(hours=12))
    assert t.verified_playoff_status([row],game,'LV')=='berth_clinched'
    row['preserved_at']=at;assert t.verified_playoff_status([row],game,'LV')=='unknown'
    row['preserved_at']=at-pd.Timedelta(hours=12);conflict={**row,'status':'eliminated'}
    assert t.verified_playoff_status([row,conflict],game,'LV')=='unknown'


def test_coach_effective_game_and_in_season_replacement():
    s=schedule();c=t.coaching_assignments(s);lv=c[c.team.eq('LV')].set_index('game_id')
    assert lv.loc['2019_2','coach']=='A' and lv.loc['2019_3','coach']=='B'
    assert lv.loc['2019_2','coach_group']=='established_observed'
    assert lv.loc['2019_3','games_since_observed_change']==1
    assert lv.loc['2019_6','games_since_observed_change']==4
    assert lv.loc['2019_3','in_season_replacement_proxy']
    assert c.effective_start.isna().all() and c.interim_status.eq('unknown').all()
    assert c[c.season.eq(2018)].coach_group.eq('unknown_left_censored').all()
    next_year=s.iloc[[-1]].copy();next_year['game_id']='2020_1';next_year['season']=2020;next_year['kickoff']=pd.Timestamp('2020-09-01T17:00Z')
    later=t.coaching_assignments(pd.concat([s,next_year],ignore_index=True))
    assert not later.loc[later.game_id.eq('2020_1'),'in_season_replacement_proxy'].any()


def test_missing_coaches_do_not_get_current_names():
    s=schedule().drop(columns=['home_coach','away_coach']);c=t.coaching_assignments(s)
    assert c.coach.isna().all() and c.coach_group.eq('unknown').all()


def test_postgame_share_never_becomes_rest_evidence():
    s=schedule();s.loc[s.game_id.eq('2019_5'),'week']=16;s.loc[s.game_id.eq('2019_6'),'week']=17
    game=s[s.game_id.eq('2019_6')];before=t.pregame_context(s,game)
    snaps=pd.DataFrame({'game_id':['2019_5','2019_6'],'team':['OAK','OAK'],'position':['QB','QB'],
                        'pfr_player_id':['p','p'],'offense_snaps':[60,10],'offense_pct':[1.,.15]})
    out=t.postgame_participation(s,snaps)
    assert out.iloc[0].participation_class=='observed_drop_50pp_plus'
    assert out.iloc[0].share_drop==pytest.approx(.85)
    assert before.starter_rest_evidence.eq('unknown').all()
    pd.testing.assert_frame_equal(before,t.pregame_context(s,game))
    assert t.postgame_participation(s,pd.DataFrame()).empty


def test_report_preserves_inputs_and_uses_no_training(tmp_path,monkeypatch):
    f=diagnostic();f['sample']='all_base_history';f['market_confidence']=np.maximum(f.market_probability,1-f.market_probability)
    from test_m81 import inputs
    s,_,_=inputs();s['home_coach']='A';s['away_coach']='K'
    monkeypatch.setattr(t,'load_data',lambda *a:(f,s,pd.DataFrame(),{},[]))
    paths=['models/production.joblib','data/predictions.db','data/m8/lab.db','M91A_CLASSIFIED_ERRORS.csv','M91A_PREDICTION_ERROR_REPORT.md']
    for name in paths:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'protected')
    output=t.generate(tmp_path,replicates=20)
    assert output.exists() and all((tmp_path/name).read_bytes()==b'protected' for name in paths)
    assert 'retrospective' in output.read_text() and 'No model' in output.read_text()
    assert (tmp_path/'reports/m91b/market_groups.csv').exists()


def test_required_source_unavailable(tmp_path):
    with pytest.raises(ValueError,match='classified errors unavailable'):t.load_data(tmp_path,tmp_path/'data')
