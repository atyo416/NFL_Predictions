"""Isolated deterministic synthetic demonstration. Never real market performance."""
from pathlib import Path
import json
import tempfile
import pandas as pd
from .odds_store import connect,rows,key
from .odds_provider import ingest
from .odds_matching import team
from .market_comparison import compare_at
from .market_benchmark import reconstruct_paper
from .paper_betting import settle,ledger_view,performance
from .market_math import decimal_odds,market_pair,value_at_probability
from .integrity import atomic_json


def fixture_data(root):
    root=Path(root);fixture=root/'tests/fixtures/m8/provider_v4.json';payload=json.loads(fixture.read_text());games=[];forecasts=[]
    for i,event in enumerate(payload['data']):
        kickoff=pd.Timestamp(event['commence_time']);decision=kickoff-pd.Timedelta(hours=24);gid=f'synthetic_m8_{i+1}'
        home=team(event['home_team']);away=team(event['away_team'])
        games.append({'game_id':gid,'season':2023,'week':i+5,'game_type':'REG','home_team':home,'away_team':away,'kickoff':kickoff,'completed':True,'home_score':[24,10,17][i],'away_score':17,'result_available_at':kickoff+pd.Timedelta(hours=8),'neutral':False,'status':'final'})
        for family in ['official_logistic','boosting','ensemble']:
            f={'game_id':gid,'home_team':home,'away_team':away,'kickoff':kickoff.isoformat(),'created_at':(decision-pd.Timedelta(minutes=2)).isoformat(),'data_cutoff':(decision-pd.Timedelta(minutes=3)).isoformat(),'training_cutoff':'2023-09-01T00:00:00+00:00','model':family,'model_version':'synthetic-'+family,'home_probability':.45,'classification':'synthetic_oos','artifact_sha256':'0'*64,'source_fingerprint':'synthetic_fixture_only','source_designation':'artificial_not_actual_model_forecast'}
            f['forecast_id']=key(f);forecasts.append(f)
    return fixture,pd.DataFrame(games),forecasts


def run_demo(root,directory):
    root=Path(root);directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    config=json.loads((root/'config/m8_protocol.json').read_text());fixture,schedules,forecasts=fixture_data(root)
    with tempfile.TemporaryDirectory() as temporary:
        db=connect(Path(temporary)/'synthetic_only.db');first=ingest(db,fixture.read_bytes(),'json','synthetic');ingest(db,fixture.read_bytes(),'json','synthetic')
        assert len(rows(db,'quotes'))==3
        opportunities=[]
        for g in schedules.to_dict('records'):
            decision=g['kickoff']-pd.Timedelta(hours=24)
            o,_=compare_at(db,schedules,forecasts,decision,config,'reconstructed','24h',[g['game_id']]);opportunities.extend(o)
        saved=reconstruct_paper(db,opportunities,schedules,config,'synthetic_demonstration')
        settle(db,schedules,config);view=ledger_view(db);before=len(rows(db,'events'));settle(db,schedules,config);assert len(rows(db,'events'))==before
        result={'classification':'SYNTHETIC SOFTWARE VERIFICATION ONLY; not actual NFL odds, model performance or betting returns','artificial_games':3,'normalized_pairs':len(rows(db,'quotes')),'deduplicated_import':'passed','strategy_wagers':len(saved),'unique_game_count':len({w['game_id'] for w in view}),'statuses':{s:sum(w['status']==s for w in view) for s in ['win','loss','push']},'correlated_exposure_summary_not_inference':performance(view),'unit_math_example':{'american_150_decimal':str(decimal_odds(150)),'american_minus150_decimal':str(decimal_odds(-150)),'pair':market_pair(decimal_odds(150),decimal_odds(-170)),'model_45_percent_at_plus150':value_at_probability(.45,decimal_odds(150),.03)},'settlement_idempotence':'passed','real_market_results':None}
        atomic_json(result,directory/'SYNTHETIC_DEMO.json');db.close()
    return result
