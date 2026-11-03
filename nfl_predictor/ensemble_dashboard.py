"""Read-only saved ensemble analysis and verified prospective records."""
from pathlib import Path
import json
import pandas as pd
import streamlit as st
from .integrity import digest


def render_analysis(root,data):
    root=Path(root);data=Path(data)
    st.subheader('Ensemble Analysis')
    st.info('Experimental only. Policy selection uses earlier development years. 2024–2025 was repeatedly examined. The production champion remains M2.')
    pointer=root/'reports/m7/latest.json'
    if not pointer.exists():st.caption('Run python -m nfl_predictor.cli compare-m7 to generate ensemble analysis.');return
    run=pointer.parent/json.loads(pointer.read_text())['run']
    checks=json.loads((run/'outputs.json').read_text())
    if any(digest(run/name)!=sha for name,sha in checks.items()):st.error('Ensemble report integrity check failed.');return
    meta=json.loads((run/'metadata.json').read_text());st.write('Development-selected policy: '+meta['selection']['method'])
    live=json.loads((run/'prospective_model.json').read_text())
    try:
        from .ensemble_registry import load_ensemble
        model,_,_=load_ensemble(root/'models/registry',live['version'])
        st.write('Current experimental parameters (2026)');st.json(model['parameters'])
    except (ValueError,FileNotFoundError):st.caption('Current experimental artifact unavailable; historical parameters remain below.')
    c=pd.read_csv(run/'comparison.csv');period=st.selectbox('Ensemble evaluation period',list(c.period.unique()),key='m7_period')
    reference=st.selectbox('Ensemble comparison reference',list(c.reference.unique()),key='m7_reference')
    view=c[c.period.eq(period)&c.reference.eq(reference)]
    st.dataframe(view,hide_index=True)
    st.bar_chart(view[view.metric.isin(['brier','log_loss'])].pivot(index='model',columns='metric',values='estimate'))
    st.image(str(run/'reliability.png'));st.dataframe(pd.read_csv(run/'complementarity.csv'),hide_index=True)
    st.dataframe(pd.read_csv(run/'disagreement.csv'),hide_index=True)
    st.dataframe(pd.read_csv(run/'parameters.csv'),hide_index=True)
    st.json(meta['folds']);st.json(meta['alignment'])
    st.caption('Weights/coefficients are fitted separately for each earlier-data calendar. Sigmoid/isotonic calibration is a separate stage; applying it does not establish calibration quality.')
    st.subheader('Genuinely issued experimental ensemble forecasts')
    from .ensemble_forecasts import records,prospective_summary
    directory=data/'m7/experimental_forecasts';forecasts=records(directory)
    if forecasts:
        st.dataframe(pd.DataFrame(forecasts).drop(columns=['source_fingerprints','selection'],errors='ignore'),hide_index=True)
    else:st.caption('No genuine experimental forecasts saved. Use forecast-ensemble; historical research rows are not issued forecasts.')
    st.json(prospective_summary(directory))
    st.download_button('Download ensemble comparison',(run/'MODEL_COMPARISON.md').read_bytes(),file_name='M7_MODEL_COMPARISON.md',mime='text/markdown')


def render_matchup(root,data,game_id):
    st.subheader('Experimental ensemble probabilities')
    if game_id is None:st.caption('Unavailable: choose a legitimate upcoming scheduled matchup.');return
    from .ensemble_forecasts import records
    from .ensemble_registry import load_ensemble
    forecasts=[r for r in records(Path(data)/'m7/experimental_forecasts') if r['game_id']==game_id]
    if not forecasts:st.caption('Unavailable: no versioned experimental forecast saved for this matchup.');return
    record=max(forecasts,key=lambda r:r['created_at'])
    try:load_ensemble(Path(root)/'models/registry',record['ensemble_version'])
    except (ValueError,FileNotFoundError) as exc:st.warning(f'Experimental artifacts unavailable or incompatible: {exc}');return
    st.dataframe(pd.DataFrame([{'Annual experimental logistic':record['base_probabilities']['logistic'],'Experimental shallow boosting':record['base_probabilities']['boosting'],'Experimental margin Elo':record['base_probabilities']['elo_margin'],'Experimental ensemble':record['home_probability']}]).map(lambda value:f'{value:.1%}'),hide_index=True)
    st.caption('Home-win probabilities. Issued '+record['created_at']+'; data cutoff '+record['data_cutoff']+'; version '+record['ensemble_version']+'. The official champion estimate above has its own cutoff and is unchanged. These saved values are not refreshed or issued by rendering this page.')
