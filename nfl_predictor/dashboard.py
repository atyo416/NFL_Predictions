"""Read-only presentation of immutable M2 experiments."""
import json
import pandas as pd
import streamlit as st

def render(directory, database):
    st.info('Exploratory historical experiments. 2024–2025 was previously examined. The M1 champion remains unchanged; prospective saved forecasts are a separate evidence stream.')
    latest=directory/'latest.json'
    if not latest.exists():
        st.warning('Run python -m nfl_predictor.cli analyze to generate M2 experiments.')
        return
    run=directory/json.loads(latest.read_text())['run']
    comparison=pd.read_csv(run/'comparison.csv')
    period=st.selectbox('Evaluation period',comparison.period.unique())
    st.subheader('Aligned model comparisons and paired uncertainty')
    st.caption('Deltas are model minus M1 logistic. Positive accuracy and negative Brier/log-loss favor the candidate. Week-block percentile intervals are exploratory and unadjusted for multiple comparisons.')
    st.dataframe(comparison[comparison.period.eq(period)],hide_index=True)
    st.subheader('Feature contributions')
    ranking=pd.read_csv(run/'feature_ranking.csv')
    st.bar_chart(ranking.set_index('group')[['mean_brier_contribution']])
    st.caption('Positive contribution: removing this group worsened Brier score. Correlated features make these conditional, noncausal comparisons.')
    st.dataframe(ranking,hide_index=True)
    st.image(str(run/'reliability.png'))
    st.subheader('Season accuracy')
    seasons=comparison[comparison.metric.eq('accuracy') & comparison.period.astype(str).str.fullmatch(r'\d{4}')]
    st.line_chart(seasons.pivot(index='period',columns='model',values='estimate'))
    st.subheader('Probability buckets')
    bands=pd.read_csv(run/'probability_buckets.csv')
    st.dataframe(bands[bands.period.eq(period)],hide_index=True)
    st.subheader('Historical error analysis')
    st.dataframe(pd.read_csv(run/'error_slices.csv'),hide_index=True)
    st.download_button('Download incorrect predictions and feature contributions', (run/'incorrect_predictions.csv').read_bytes(),file_name='m2_incorrect_predictions.csv',mime='text/csv')
    st.subheader('Experiment metadata')
    st.json(json.loads((run/'metadata.json').read_text()))
    st.subheader('Prospective official champion forecasts')
    if database.exists():
        import sqlite3
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as db:
            f=pd.read_sql_query('SELECT game_id,model_version,created_at,kickoff,home_probability,result FROM predictions WHERE official=1',db)
        st.caption(f'{len(f)} official saved forecasts; {f.result.notna().sum()} attached outcomes. Ties are excluded from binary metrics. No outcomes are inferred or modified by analysis.')
        valid=f[f.result.isin([0,1]) & pd.to_datetime(f.created_at,utc=True).lt(pd.to_datetime(f.kickoff,utc=True))]
        if len(valid):
            from .evaluation import evaluate
            st.json(evaluate(valid.result,valid.home_probability))
        else: st.write('No resolved eligible prospective forecasts yet.')
