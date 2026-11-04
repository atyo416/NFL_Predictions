"""Matched one-game cohorts and fixed-threshold reconstructed sensitivity."""
from datetime import timedelta
from pathlib import Path
import json
import uuid
import numpy as np
import pandas as pd
from .ensemble import timestamp
from .elo import eligible_at
from .analysis import paired_intervals,calibration_diagnostic
from .evaluation import evaluate,buckets
from .market_math import value_at_probability
from .market_comparison import compare_at,choose_books,audit_matches
from .market_forecasts import FAMILIES,historical_inference
from .paper_betting import strategy,select
from .odds_store import rows,append,key,encoded,utc_now
from .integrity import atomic_json,digest


def benchmark(db,schedules,forecasts,config,mode='prospective',infer=None):
    now=timestamp(utc_now());quotes=rows(db,'quotes');audits=audit_matches(db,schedules,config)
    from .odds_matching import match
    # Candidate collection must not let a later duplicate event erase earlier samples.
    potential=[match(q,schedules,config['kickoff_tolerance_seconds']) for q in quotes]
    matched={a['game_id'] for a in potential if a['status']=='matched'}
    completed=schedules[schedules.completed&schedules.game_id.isin(matched)]
    records=[];exclusions=[];opportunities=[]
    for g in completed.to_dict('records'):
        available=eligible_at(g)
        if pd.isna(available) or available>=now:continue
        if g['home_score']==g['away_score']:
            exclusions.append({'game_id':g['game_id'],'reason':'tie_excluded_from_binary_probability_scoring'});continue
        for cohort,spec in config['cohorts'].items():
            decision=timestamp(g['kickoff'])-timedelta(hours=spec['lead_hours'])
            relevant=[q for q in quotes if q['season']==g['season'] and q['home_team']==g['home_team'] and q['away_team']==g['away_team'] and timestamp(q['snapshot_at'])<=decision and timestamp(q['snapshot_at'])>=decision-timedelta(minutes=spec['tolerance_minutes'])]
            if not relevant:exclusions.append({'game_id':g['game_id'],'cohort':cohort,'reason':'no_quote_in_predeclared_window'});continue
            if mode=='reconstructed' and infer is not None and any(q['source_kind']=='verified_archive' for q in relevant):
                try:forecasts=forecasts+infer(g['game_id'],decision)
                except (ValueError,FileNotFoundError) as exc:exclusions.append({'game_id':g['game_id'],'cohort':cohort,'reason':str(exc)})
            o,x=compare_at(db,schedules,forecasts,decision,config,mode,cohort,[g['game_id']]);exclusions.extend(x)
            # Never let synthetic fixtures enter actual NFL market scoring.
            o=[r for r in o if r['source_kind']!='synthetic' and r['rules_warning'] is None]
            o=choose_books(o,config);home=[r for r in o if r['side']=='home']
            if set(r['model'] for r in home)!=set(FAMILIES):
                exclusions.append({'game_id':g['game_id'],'cohort':cohort,'reason':'incomplete_matched_model_set_or_unverified_market_rules'});continue
            y=int(g['home_score']>g['away_score']);first=home[0]
            for r in home:records.append({'game_id':g['game_id'],'season':g['season'],'week':g['week'],'cohort':cohort,'bookmaker':r['bookmaker'],'target':y,'model':r['model'],'probability':r['model_probability'],'classification':mode,'quote_id':r['quote_id'],'forecast_id':r['forecast_id']})
            records.append({'game_id':g['game_id'],'season':g['season'],'week':g['week'],'cohort':cohort,'bookmaker':first['bookmaker'],'target':y,'model':'market_no_vig','probability':first['no_vig_home'],'classification':mode,'quote_id':first['quote_id'],'forecast_id':None})
            opportunities.extend(o)
    frame=pd.DataFrame(records)
    if len(frame) and frame.duplicated(['game_id','cohort','model']).any():raise ValueError('Duplicate independent market benchmark observations')
    return frame,opportunities,exclusions


def reconstruct_paper(db,opportunities,schedules,config,classification='historical_reconstructed_paper_simulation'):
    """Explicit research records; never a genuinely issued past wager."""
    saved=[]
    for cohort in sorted({o['cohort'] for o in opportunities}):
        for model in FAMILIES:
            for threshold in config['thresholds']:
                definition=strategy(config,model,threshold,cohort)
                candidates=[o for o in opportunities if o['cohort']==cohort and o['rules_warning'] is None]
                for o in select(candidates,definition,config,False):
                    slot=key([classification,o['game_id'],definition['strategy_version'],cohort])
                    existing=db.execute('SELECT payload FROM wagers WHERE slot=?',(slot,)).fetchone()
                    if existing:continue
                    created=timestamp(utc_now()).isoformat()
                    w={**o,'minimum_probability_for_threshold':value_at_probability(o['model_probability'],o['decimal_odds'],threshold)['minimum_probability_for_threshold'],'wager_id':slot,'strategy_version':definition['strategy_version'],'threshold':threshold,'stake_units':'1','created_at':created,'status':'pending','classification':classification,'executable_price_claim':False}
                    with db:
                        append(db,'strategies',definition,definition['strategy_version'])
                        db.execute('INSERT INTO wagers VALUES(?,?,?,?)',(slot,slot,created,encoded(w)))
                    saved.append(w)
    return saved


def write_benchmark(frame,directory,config):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    scores=[];calibration=[];probabilities=[]
    if len(frame):
        for cohort,f in frame.groupby('cohort'):
            c=paired_intervals(f,config['bootstrap_replicates'],config['seed'],config['confidence_level'],'market_no_vig');c['cohort']=cohort;scores.append(c)
            for model,g in f.groupby('model'):
                calibration.append({'cohort':cohort,'model':model,**evaluate(g.target,g.probability),**calibration_diagnostic(g.target,g.probability)})
                b=buckets(g.target,g.probability);b['cohort']=cohort;b['model']=model;probabilities.append(b)
    pd.concat(scores).to_csv(directory/'benchmark.csv',index=False) if scores else pd.DataFrame(columns=['model','metric','estimate','difference','difference_low','difference_high','cohort','games']).to_csv(directory/'benchmark.csv',index=False)
    pd.DataFrame(calibration,columns=['cohort','model','games','accuracy','brier','log_loss','home_win_rate','intercept','slope']).to_csv(directory/'calibration.csv',index=False)
    (pd.concat(probabilities) if probabilities else pd.DataFrame(columns=['bucket','games','predicted','observed','cohort','model'])).to_csv(directory/'probability_buckets.csv',index=False)
    frame.to_parquet(directory/'benchmark_predictions.parquet',index=False)
    if len(frame):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots()
        # Never pool repeated game observations from different timing cohorts.
        for (cohort,model),g in frame.groupby(['cohort','model']):
            b=buckets(g.target,g.probability);ax.plot(b.predicted,b.observed,'o-',label=cohort+' '+model)
        ax.plot([0,1],[0,1],'k--');ax.set(xlabel='Predicted home probability',ylabel='Observed home win rate',title='Matched market probability diagnostics');ax.legend(fontsize=6);fig.tight_layout();fig.savefig(directory/'reliability.png');plt.close(fig)
