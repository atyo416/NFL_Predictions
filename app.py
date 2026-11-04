"""Local interface. All network operations are explicit button actions."""
import json
import pandas as pd
import streamlit as st
from nfl_predictor.data_loader import cached,update,DATA,ROOT
from nfl_predictor.feature_engineering import team_games,rating
from nfl_predictor.model import load
from nfl_predictor.predictions import predict
from nfl_predictor.database import connect,attach_results
st.set_page_config(page_title='NFL Prediction Engine',layout='wide')
st.title('NFL Game Prediction Engine · M8')
st.caption('Experimental statistical baseline. Probabilities are not claimed to be calibrated.')
page=st.sidebar.radio('Page',['Upcoming Games','Team Comparison','Model Performance','Model Analysis','Team Power Rankings','Betting Lab'])
try:
    schedules,metrics=cached()
except Exception as exc:
    st.warning(str(exc)); st.code('python -m nfl_predictor.cli update'); st.stop()
metadata=sorted((DATA/'manifests').glob('*.json')) or sorted((DATA/'processed').glob('metadata_*.json'))
current_metadata=[p for p in metadata if '2026' in p.name]
if current_metadata: metadata=current_metadata
if metadata:
    stamp=max(json.loads(p.read_text())['retrieved_at'] for p in metadata)
    st.caption('Last source retrieval: '+stamp)
    if pd.Timestamp.now(tz='UTC')-pd.Timestamp(stamp)>pd.Timedelta(days=2): st.warning('Cached data is more than two days old.')
model_path=ROOT/'models/production.joblib'
model=load(model_path) if model_path.exists() else None
st.caption('Model: '+(model['version'] if model else 'not trained'))
if page=='Upcoming Games':
    season=st.selectbox('Season',sorted(schedules.season.unique()),index=len(schedules.season.unique())-1)
    week=st.selectbox('Week',sorted(schedules.loc[schedules.season.eq(season),'week'].unique()))
    if st.button('Refresh Data'):
        try:
            with st.spinner('Refreshing current season…'): update([2026],refresh=True)
            st.rerun()
        except Exception as exc: st.error(str(exc))
    upcoming=schedules[schedules.season.eq(season)&schedules.week.eq(week)&~schedules.completed&schedules.kickoff.gt(pd.Timestamp.now(tz='UTC'))]
    st.dataframe(upcoming[['kickoff','away_team','home_team']],hide_index=True)
    if st.button('Generate Predictions',disabled=model is None):
        try:
            db=connect(DATA/'predictions.db'); attach_results(db,schedules)
            result=predict(schedules,metrics,model,db); db.close()
            if result.empty: st.info('No legitimate upcoming 2026 games available.')
            else: st.dataframe(result[result.week.eq(week)],hide_index=True)
        except Exception as exc: st.error(str(exc))
    db=connect(DATA/'predictions.db')
    saved=pd.read_sql_query('SELECT payload,result FROM predictions ORDER BY id DESC',db); db.close()
    if len(saved):
        st.subheader('Saved forecasts')
        st.dataframe(pd.DataFrame([dict(json.loads(r.payload),result=r.result) for r in saved.itertuples()]),hide_index=True)
elif page=='Team Comparison':
    teams=sorted(set(schedules.home_team)|set(schedules.away_team))
    a=st.selectbox('Team A',teams); b=st.selectbox('Team B',teams,index=1)
    cutoff=pd.Timestamp.now(tz='UTC'); history=team_games(schedules,metrics)
    st.dataframe(pd.DataFrame({a:rating(history,a,2026,cutoff),b:rating(history,b,2026,cutoff)}))
    matches=schedules[((schedules.home_team.eq(a)&schedules.away_team.eq(b))|(schedules.home_team.eq(b)&schedules.away_team.eq(a)))&schedules.season.eq(2026)&schedules.kickoff.gt(cutoff)]
    st.caption('Only actual scheduled matchups are supported. Hypothetical forecasts would require an explicit venue and cutoff and cannot be official.')
    selected=None
    if len(matches):
        selected=st.selectbox('Scheduled game',matches.game_id)
        if model:
            from nfl_predictor.feature_engineering import build,FEATURES
            if model.get('feature_schema')=='m4-v1':
                from nfl_predictor.m4_features import prepare
                f=prepare(schedules,metrics,model['feature_config'],cutoff=cutoff,game_ids=[selected])
            else:
                f=build(schedules,metrics,cutoff,game_ids=[selected])
            p=model['pipeline'].predict_proba(f[model.get('features',FEATURES)])[0,1]
            st.write(f'Official champion model estimate (not a saved forecast): home {p:.1%}; away {1-p:.1%}')
    from nfl_predictor.m3_dashboard import render_matchup
    render_matchup(schedules,DATA,a,b,selected)
    from nfl_predictor.m6_dashboard import render_context
    render_context(schedules,metrics,DATA,ROOT,a,b,selected)
    from nfl_predictor.ensemble_dashboard import render_matchup as render_ensemble_matchup
    render_ensemble_matchup(ROOT,DATA,selected)
elif page=='Betting Lab':
    from nfl_predictor.betting_dashboard import render
    render(ROOT,DATA)
elif page=='Team Power Rankings':
    from nfl_predictor.m3_dashboard import render_rankings
    render_rankings(DATA,ROOT/'reports')
elif page=='Model Analysis':
    from nfl_predictor.dashboard import render
    render(ROOT/'reports/m2', DATA/'predictions.db')
    from nfl_predictor.m4_dashboard import render as render_m4
    render_m4(ROOT/'reports/m4')
    from nfl_predictor.history_dashboard import render as render_history
    render_history(ROOT)
    from nfl_predictor.m6_dashboard import render_analysis
    render_analysis(ROOT)
    from nfl_predictor.ensemble_dashboard import render_analysis as render_ensemble_analysis
    render_ensemble_analysis(ROOT,DATA)
else:
    st.info('Historical backtests are retrospective simulations, distinct from forecasts saved before kickoff.')
    path=ROOT/'reports/backtest.json'
    if not path.exists(): st.warning('Run python -m nfl_predictor.cli backtest'); st.stop()
    report=json.loads(path.read_text()); st.json(report)
    st.image(str(ROOT/'reports/reliability.png'))
    st.dataframe(pd.read_parquet(ROOT/'reports/historical_predictions.parquet'),hide_index=True)
