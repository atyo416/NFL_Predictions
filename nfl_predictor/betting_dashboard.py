"""Read-only Betting Lab. Rendering never fetches odds, fits models or issues wagers."""
from pathlib import Path
import json
import sqlite3
import pandas as pd
import streamlit as st
from .integrity import digest
from .odds_store import rows
from .paper_betting import ledger_view,performance


def local_time(value):return pd.Timestamp(value).tz_convert('America/New_York').strftime('%Y-%m-%d %H:%M %Z')


def render(root,data):
    root=Path(root);data=Path(data)
    st.header('Betting Lab · research and paper simulation')
    st.caption('No real-money execution. Probability disagreement and model EV are conditional estimates, not verified advantages or executable prices.')
    path=data/'m8/lab.db';pointer=root/'reports/m8/latest.json';run=None;meta=None
    if pointer.exists():
        run=pointer.parent/json.loads(pointer.read_text())['run'];checks=json.loads((run/'outputs.json').read_text())
        if any(digest(run/name)!=sha for name,sha in checks.items()):st.error('M8 report integrity check failed.');return
        meta=json.loads((run/'metadata.json').read_text())
    if not path.exists():
        st.info('No market database yet. Import genuine timestamped quotes or explicitly fetch with your own API key. Synthetic examples run separately with demo-m8.')
        st.code('python -m nfl_predictor.cli import-odds --odds-file reviewed_quotes.csv\npython -m nfl_predictor.cli report-m8')
        return
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    try:
        quotes=rows(db,'quotes');ledger=ledger_view(db)
        current,detail,paper,analysis,integrity=st.tabs(['Current Market','Game Detail','Paper Ledger','Performance Analysis','Data Integrity'])
        with current:
            if meta:
                st.write('Saved comparison as of '+local_time(meta['decision_cutoff'])+' · '+meta['mode'])
                if pd.Timestamp.now(tz='UTC')-pd.Timestamp(meta['decision_cutoff'])>pd.Timedelta(minutes=15):st.warning('Saved market comparison is stale; run compare-market explicitly. It is not refreshed by opening this page.')
                o=pd.read_parquet(run/'current_opportunities.parquet')
                if len(o):
                    columns=['game_id','kickoff','bookmaker','model','selection','quoted_odds','odds_format','implied_home','implied_away','overround','bookmaker_margin','no_vig_home','no_vig_away','model_probability','probability_edge_pp','ev_per_unit','positive_ev_after_minus2pp','positive_ev_after_minus5pp','model_disagreement_range_pp','quote_at','forecast_cutoff','model_version','rules_warning']
                    st.dataframe(o[columns],hide_index=True)
                    st.caption('Boosting is the M5 architecture with M7 annual refits. Ensemble probabilities remain experimental. EV assumes a binary/no-tie scenario; undocumented market rules block paper issuance.')
                    for r in o.head(6).to_dict('records'):
                        with st.expander(r['game_id']+' · '+r['model']+' · '+r['selection']+' sensitivity'):
                            st.dataframe(pd.DataFrame(list(r['sensitivity'])),hide_index=True);st.caption('Scenario shifts, not confidence intervals.')
                else:st.info('No valid timestamp-aligned model/market pairs. Missing quotes and forecasts remain unavailable.')
            else:st.info('Run compare-market or report-m8 to save timestamped comparisons.')
        with detail:
            if quotes:
                event=st.selectbox('Provider event',sorted({q['event_id'] for q in quotes}),key='m8_event')
                history=pd.DataFrame([q for q in quotes if q['event_id']==event]).sort_values('snapshot_at')
                st.dataframe(history[['home_team','away_team','bookmaker','snapshot_at','quote_at','received_at','home_quoted','away_quoted','odds_format','source_kind','scope','tie_rule','source_reference']],hide_index=True)
                if run:
                    saved=pd.read_parquet(run/'current_opportunities.parquet')
                    side_by_side=saved[saved.quote_id.isin(history.quote_id)] if 'quote_id' in saved else pd.DataFrame()
                    if len(side_by_side):
                        st.dataframe(side_by_side.pivot_table(index=['bookmaker','selection','quote_at'],columns='model',values='model_probability',aggfunc='first'),hide_index=False)
                        st.dataframe(side_by_side[['model','model_version','forecast_created_at','forecast_cutoff','quote_id','artifact_sha256']],hide_index=True)
                    else:st.caption('No valid saved model probabilities for this event at the comparison cutoff.')
                st.caption('History preserves each coherent same-book pair; last observed is not automatically a verified closing price.')
            else:st.caption('No genuine odds history available. No prices are invented.')
        with paper:
            st.json(performance([w for w in ledger if w['classification']=='genuine_prospective_paper_simulation']))
            if ledger:
                st.dataframe(pd.DataFrame(ledger)[['wager_id','game_id','model','bookmaker','selection','decimal_odds','model_probability','break_even_probability','ev_per_unit','stake_units','threshold','strategy_version','classification','status','profit_units']],hide_index=True)
                chosen=st.selectbox('Paper wager audit',sorted(w['wager_id'] for w in ledger),key='m8_wager');st.json(next(w for w in ledger if w['wager_id']==chosen))
            else:st.caption('No paper wagers issued. Opening this page never issues them.')
            st.code('python -m nfl_predictor.cli issue-paper-bets --dry-run\npython -m nfl_predictor.cli settle-paper-bets')
        with analysis:
            if run:
                b=pd.read_csv(run/'benchmark.csv')
                if len(b):
                    st.dataframe(b,hide_index=True)
                    st.dataframe(pd.read_csv(run/'calibration.csv'),hide_index=True)
                    if (run/'reliability.png').exists():st.image(str(run/'reliability.png'))
                else:st.info('No genuine matched, graded market sample. Brier/log loss, ROI and profitability are unavailable.')
                st.dataframe(pd.read_csv(run/'paper_performance.csv'),hide_index=True)
                if ledger:st.dataframe(pd.DataFrame(ledger)[['game_id','model','cohort','threshold','ev_per_unit','status','profit_units']],hide_index=True)
                st.json(json.loads((run/'closing_lines.json').read_text()))
                st.caption('Cohorts/strategies are correlated; do not count repeated prices as independent games. CLV and sensitivity are diagnostics, not proof of profitability.')
        with integrity:
            if meta:
                st.json(meta['provider']);st.json(meta['match_status_counts']);st.json(meta['storage'])
                st.write('Actual quote pairs:',meta['actual_quote_pairs'],'· synthetic pairs:',meta['synthetic_quote_pairs'])
                st.json(json.loads((run/'match_audit.json').read_text()))
                st.json(json.loads((run/'comparison_exclusions.json').read_text()))
            stale=sum(pd.Timestamp.now(tz='UTC')-pd.Timestamp(q['quote_at'])>pd.Timedelta(minutes=15) for q in quotes)
            st.write('Currently stale price versions:',stale)
            st.caption('Provider credentials are never displayed. Live fetch is explicit; no polling runs here. M6/M7/M8 native Windows acceptance remains outstanding unless separately verified.')
    finally:db.close()
