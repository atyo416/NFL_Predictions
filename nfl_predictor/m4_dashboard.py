"""M4 analysis is read-only: model selection in a chart never changes forecasts."""
import json
import pandas as pd
import streamlit as st
from .integrity import digest

def render(directory):
    st.subheader('M4 nonlinear model experiments')
    st.info('Experimental historical analysis. The official champion and prospective prediction history are unchanged. Models are never trained or promoted by this page.')
    pointer=directory/'latest.json'
    if not pointer.exists():
        st.caption('Run python -m nfl_predictor.cli compare-m4 to generate nonlinear analysis.');return
    run=directory/json.loads(pointer.read_text())['run']
    checks=json.loads((run/'outputs.json').read_text())
    if any(digest(run/name)!=sha for name,sha in checks.items()):
        st.error('M4 report integrity check failed. Preserve the damaged run and regenerate in a new output directory.');return
    c=pd.read_csv(run/'comparison.csv');period=st.selectbox('M4 evaluation period',c.period.unique(),key='m4_period')
    st.dataframe(c[c.period.eq(period)],hide_index=True)
    st.caption('Model minus M2 logistic: positive accuracy or negative Brier/log-loss favors the candidate. Paired week-block intervals are exploratory and unadjusted.')
    st.subheader('Chronological development selection')
    st.dataframe(pd.read_csv(run/'development_ranking.csv'),hide_index=True)
    st.dataframe(pd.read_csv(run/'development_trials.csv'),hide_index=True)
    st.subheader('Training versus later-period diagnostics')
    gap=pd.read_csv(run/'overfitting.csv');name=st.selectbox('M4 diagnostic model',sorted(gap.model.unique()))
    st.dataframe(gap[gap.model.eq(name)],hide_index=True)
    st.caption('Training, calibration-diagnostic and forward evaluation rows are distinct periods. A training gain may disappear forward; calibration-diagnostic scores are not independent selection evidence.')
    st.subheader('Exploratory permutation importance')
    imp=pd.read_csv(run/'permutation_importance.csv');model=st.selectbox('M4 importance model',sorted(imp.model.unique()))
    means=imp[imp.model.eq(model)].groupby('group').brier_increase.mean().sort_values(ascending=False)
    st.bar_chart(means);st.caption('Brier increase after permutation. Correlated features can conceal redundant signals or create unrealistic combinations. Importance is not causal.')
    st.dataframe(pd.read_csv(run/'logistic_coefficients.csv'),hide_index=True)
    st.subheader('Calibration and confidence')
    st.image(str(run/'reliability.png'))
    cal=pd.read_csv(run/'calibration.csv');st.dataframe(cal[cal.period.eq(period)],hide_index=True)
    confidence=pd.read_csv(run/'confidence_buckets.csv');st.dataframe(confidence[confidence.period.eq(period)],hide_index=True)
    st.download_button('Download M4 comparison report',(run/'MODEL_COMPARISON.md').read_bytes(),file_name='M4_MODEL_COMPARISON.md',mime='text/markdown')
    st.subheader('Experimental model metadata')
    st.json(json.loads((run/'metadata.json').read_text()))
    st.json(json.loads((run/'registry_metadata.json').read_text()))
