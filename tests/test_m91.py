import pandas as pd
import polars as pl
import pytest
from nfl_predictor import personnel_evidence as e

@pytest.fixture
def sample(monkeypatch):
    now=pd.Timestamp('2026-11-05T00:00Z');monkeypatch.setattr(e,'utc_now',lambda:now)
    f=pl.DataFrame({'season':[2026]*3,'week':[9]*3,'game_type':['REG']*3,'team':['OAK']*3,
                    'gsis_id':['p1','p2','p3'],'position':['QB']*3,'depth_team':[2,1,3],
                    'report_status':['Questionable','Out',None],'practice_status':['Limited','DNP',None]})
    game={'game_id':'g','season':2026,'week':9,'home_team':'LV','away_team':'KC','kickoff':now+pd.Timedelta(days=1)}
    return f,game,now


def test_identity_crosswalk():
    roster=pd.DataFrame({'gsis_id':['g1','g2','g3'],'espn_id':['1','2','2'],'pfr_id':['a','b','c']})
    f=pd.DataFrame({'espn_id':['1','2','unknown'],'pfr_player_id':['a',None,None]})
    ids=e.reconcile(f,roster);assert ids.iloc[0]=='g1' and ids.iloc[1:].isna().all()
    assert e.reconcile(pd.DataFrame({'gsis_id':['g9'],'espn_id':['1']}),roster).isna().all()


def test_ordering_status_and_missing(sample):
    raw,game,now=sample;f=e.normalize(raw,'load_depth_charts',2026)
    assert f.team.eq('LV').all()
    q=e.quarterback_list(f);assert q.player_id.tolist()==['p2','p1','p3']
    assert q.iloc[0].role=='listed_QB1' and not q.uncertain.any()
    assert f.game_designation.iloc[:2].tolist()==['Questionable','Out'] and pd.isna(f.game_designation.iloc[2])
    assert f.practice_participation.iloc[:2].tolist()==['Limited','DNP'] and pd.isna(f.practice_participation.iloc[2])
    dup=f.copy();dup.loc[0,'rank']=1;assert e.quarterback_list(dup).uncertain.all()
    f['rank']=2;assert e.quarterback_list(f).uncertain.all()


@pytest.mark.parametrize('value,missing',[('2026-11-04',True),('2026-11-04T12:00:00',True),('2026-11-04T12:00:00-05:00',False),(None,True)])
def test_source_clock(value,missing):assert pd.isna(e.source_time(value))==missing


def test_classification_and_future_time(sample):
    raw,game,now=sample;row=e.normalize(raw,'load_injuries',2026).iloc[0].to_dict()
    o={'source':'load_injuries','captured_at':now.isoformat(),'created_at':now.isoformat(),'provenance':'direct_nflreadpy_capture'}
    assert e.classify(row,o)=='retrospective'
    row['source_at']=now-pd.Timedelta(hours=1)
    assert e.classify(row,o)=='historical_source_timestamped'
    assert e.classify(row,o,now,game['kickoff'])=='verified_prospective'
    row['source_at']=now+pd.Timedelta(hours=1);assert e.classify(row,o,now,game['kickoff'])=='unknown'
    row['source_at']=pd.NaT;o['source']='load_snap_counts';assert e.classify(row,o,now,game['kickoff'])=='retrospective'


def test_duplicate_revision_asof_and_integrity(sample,tmp_path,monkeypatch):
    raw,game,now=sample;o=e.preserve(raw,'load_injuries',2026,tmp_path,now)
    assert e.preserve(raw,'load_injuries',2026,tmp_path,now)==o and len(e.observations(tmp_path))==1
    assert e.as_of(tmp_path,game,now-pd.Timedelta(seconds=1)).empty
    observed=e.as_of(tmp_path,game,now);assert len(observed)==3 and observed.evidence_class.eq('verified_prospective').all()
    monkeypatch.setattr(e,'utc_now',lambda:now+pd.Timedelta(hours=1))
    revised=raw.with_columns(pl.lit('Doubtful').alias('report_status'))
    e.preserve(revised,'load_injuries',2026,tmp_path,now+pd.Timedelta(hours=1))
    assert len(e.observations(tmp_path))==2
    assert e.as_of(tmp_path,game,now).game_designation.iloc[:2].tolist()==['Questionable','Out'] and pd.isna(e.as_of(tmp_path,game,now).game_designation.iloc[2])
    assert len(e.as_of(tmp_path,game,now+pd.Timedelta(hours=1)))==6
    path=tmp_path/'objects'/o['file'];path.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='integrity'):e.read_raw(tmp_path,o)


def test_late_receipt_not_backdated_and_future_rejection(sample,tmp_path):
    raw,game,now=sample;e.preserve(raw,'load_depth_charts',2026,tmp_path,now-pd.Timedelta(hours=1))
    assert e.as_of(tmp_path,game,now-pd.Timedelta(minutes=30)).empty
    with pytest.raises(ValueError,match='future'):e.preserve(raw,'load_injuries',2026,tmp_path,now+pd.Timedelta(seconds=1))
    with pytest.raises(ValueError,match='nonfuture'):e.as_of(tmp_path,game,now+pd.Timedelta(seconds=1))


def test_latest_whole_chart_and_unknown_identity(sample,tmp_path):
    raw,game,now=sample
    raw=pl.DataFrame({'dt':['2026-11-04T12:00Z','2026-11-04T14:00Z','2026-11-04T14:00Z'],
                      'team':['LV']*3,'gsis_id':['old','new',None],'pos_abb':['QB']*3,'pos_rank':[1,1,2]})
    e.preserve(raw,'load_depth_charts',2026,tmp_path,now)
    result=e.as_of(tmp_path,game,now)
    assert result.player_id.dropna().tolist()==['new'] and 'unknown' in result.evidence_class.tolist()


def test_collection_failures_preserve_ledgers(sample,tmp_path,monkeypatch):
    raw,game,now=sample
    import nflreadpy as nfl
    paths=['predictions.db','m8/lab.db','m7/experimental_forecasts/forecasts/original.json','m83/forecasts/original.json']
    for name in paths:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'original')
    monkeypatch.setattr(nfl,'load_injuries',lambda seasons:raw)
    def fail(seasons):raise RuntimeError('source unavailable')
    for source in e.SOURCES[1:]:monkeypatch.setattr(nfl,source,fail)
    events=e.collect(tmp_path,[2026]);assert len(events)==5 and len(e.observations(tmp_path/'m91'))==1
    assert len(list((tmp_path/'m91/failures').glob('*.json')))==4
    assert all((tmp_path/name).read_bytes()==b'original' for name in paths)
