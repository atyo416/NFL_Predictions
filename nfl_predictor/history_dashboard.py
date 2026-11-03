"""Read-only historical training analysis; no fitting or source downloads on render."""
import json
import pandas as pd
import streamlit as st
from .integrity import digest

def render(root):
    st.subheader('Historical Training Analysis · M5')
    st.info('At-risk exploratory development. Original champion and issued forecasts remain unchanged; all M5 models are activation-blocked. Native combined Windows acceptance remains pending.')
    audit=root/'reports/history_audit/source_audit.csv'
    if audit.exists():
        a=pd.read_csv(audit);st.caption('Available cached seasons: '+', '.join(map(str,a.season.tolist())))
        st.dataframe(a,hide_index=True)
        if a.clock_known_fraction.lt(1).any():st.warning('Some historical clocks are unknown. Date-only games use conservative interval bounds; common-feature experiments exclude exact rest days.')
        if a.source_metric_coverage.lt(1).any():st.warning('Some seasons contain missing play-by-play coverage. See per-season audit; missing values are not source-confirmed zeros.')
    else:st.caption('Run python -m nfl_predictor.cli audit-history after downloading history.')
    pointer=root/'reports/m5/latest.json'
    if not pointer.exists():st.caption('Run python -m nfl_predictor.cli compare-history to build window/recency results.');return
    run=pointer.parent/json.loads(pointer.read_text())['run']
    checks=json.loads((run/'outputs.json').read_text())
    if any(digest(run/name)!=sha for name,sha in checks.items()):st.error('M5 report integrity check failed; preserve evidence and rebuild.');return
    meta=json.loads((run/'metadata.json').read_text());st.write('Development-selected experimental policies:',meta['selected_policies'])
    st.caption('Original full-feature references and common-feature W1 are separate. All common-feature windows share the same pregame history, and only training-label start dates change.')
    c=pd.read_csv(run/'comparison.csv');period=st.selectbox('M5 evaluation period',c.period.unique(),key='m5_period')
    st.subheader('Historical windows and recency weights')
    st.dataframe(c[c.period.eq(period)],hide_index=True)
    st.dataframe(pd.read_csv(run/'development_windows.csv'),hide_index=True)
    st.dataframe(pd.read_csv(run/'development_decay.csv'),hide_index=True)
    decay=pd.read_csv(run/'decay_effects.csv');st.caption('Decay effects below reference the SAME window with uniform weights.');st.dataframe(decay[decay.period.eq(period)],hide_index=True)
    for metric,label in [('brier','Brier score by year'),('accuracy','Accuracy by year')]:
        st.subheader(label)
        years=c[c.period.astype(str).str.fullmatch(r'\d{4}')&c.metric.eq(metric)]
        st.line_chart(years.pivot(index='period',columns='model',values='estimate'))
    st.subheader('Calibration and completeness')
    st.image(str(run/'reliability.png'))
    cal=pd.read_csv(run/'calibration.csv');st.dataframe(cal[cal.period.eq(period)],hide_index=True)
    if (run/'feature_completeness.csv').exists():st.dataframe(pd.read_csv(run/'feature_completeness.csv'),hide_index=True)
    st.download_button('Download M5 comparison report',(run/'MODEL_COMPARISON.md').read_bytes(),file_name='M5_MODEL_COMPARISON.md',mime='text/markdown')
    st.json(meta)
