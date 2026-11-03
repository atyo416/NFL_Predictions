"""Read cached M6 results. Current team lookup uses compact summaries, never PBP."""
from pathlib import Path
import json
import pandas as pd
import streamlit as st
from .integrity import digest

@st.cache_data(show_spinner=False)
def _ratings(schedules,metrics,season,cutoff,parameters):
    from .adjusted_efficiency import observations,ratings_at,AdjustmentParameters
    return ratings_at(observations(schedules,metrics),season,pd.Timestamp(cutoff),AdjustmentParameters(**parameters))

@st.cache_data(show_spinner=False)
def _performance(directory,version_files):
    files=[Path(directory)/name for name,sha in version_files]
    return pd.concat([pd.read_parquet(path) for path in files],ignore_index=True) if files else pd.DataFrame(columns=['player_id','available_at','kickoff','season','dropbacks','epa_sum','successes'])

def render_context(schedules,metrics,data,root,a,b,game_id):
    st.subheader('Opponent-adjusted efficiency · experimental')
    config=json.loads((root/'config/m6_protocol.json').read_text()) if (root/'config/m6_protocol.json').exists() else {'adjustment':{}}
    # Conservative five-minute buckets reuse compact adjustment snapshots across rerenders.
    cutoff=pd.Timestamp.now(tz='UTC').floor('5min')
    state=_ratings(schedules,metrics,2026,cutoff.isoformat(),config['adjustment'])
    st.caption('As-of cutoff: '+cutoff.isoformat()+'. Defensive EPA/success are allowed values: lower is stronger. Schedule effects are additive estimates, not causal corrections.')
    st.dataframe(state[state.team.isin([a,b])][['team','raw_estimate_off_epa','adj_off_epa','raw_estimate_def_epa_allowed','adj_def_epa_allowed','adj_off_success','adj_def_success_allowed','off_schedule_epa','def_schedule_epa','epa_games']],hide_index=True)
    st.caption('Raw estimates here use the adjustment model’s prior; the original M5 raw ratings remain in the existing comparison table. Positive offense schedule effect means weaker opposing defenses; positive defense schedule effect means stronger opposing offenses.')
    st.subheader('QB and player context · evidence-qualified')
    from .personnel import load_evidence,team_context
    directory=data/'m6/qb_performance';pointer=directory/'active.json'
    active=json.loads(pointer.read_text())['files'] if pointer.exists() else []
    for entry in active:
        if digest(directory/entry['file'])!=entry['sha256']:raise ValueError('QB performance snapshot failed integrity verification')
    performance=_performance(str(directory),tuple((entry['file'],entry['sha256']) for entry in active));records=load_evidence(data/'m6/personnel')
    if game_id is None:
        st.caption('Choose an unstarted scheduled matchup to view verified context. Previous observed starters are not confirmed next starters.');return
    g=schedules[schedules.game_id.eq(game_id)].iloc[0];contexts=[team_context(schedules,performance,records,game_id,t,min(cutoff,g.kickoff)) for t in [a,b]]
    for c in contexts:
        st.write(c['team'])
        st.json(c)
    st.caption('Missing injury reports, rookie performance and incomplete report scope remain unknown. No personnel context changes official forecasts.')

def render_analysis(root):
    st.subheader('M6 opponent and personnel research')
    st.info('Experimental models only. Historical availability is coverage-gated; no eventual starter or current-game participation is treated as pregame evidence.')
    pointer=root/'reports/m6/latest.json'
    audit=root/'reports/personnel_audit/coverage.json'
    if audit.exists():st.json(json.loads(audit.read_text()))
    if not pointer.exists():st.caption('Run python -m nfl_predictor.cli compare-m6 to generate M6 analysis.');return
    run=pointer.parent/json.loads(pointer.read_text())['run'];checks=json.loads((run/'outputs.json').read_text())
    if any(digest(run/name)!=sha for name,sha in checks.items()):st.error('M6 report integrity check failed.');return
    c=pd.read_csv(run/'vs_m5.csv');period=st.selectbox('M6 evaluation period',c.period.unique(),key='m6_period')
    st.dataframe(c[c.period.eq(period)],hide_index=True);st.caption('Deltas are model minus fixed M5 A; negative Brier/log-loss is better. Paired intervals are exploratory and unadjusted.')
    imp=pd.read_csv(run/'permutation_importance.csv');model=st.selectbox('M6 importance model',sorted(imp.model.unique()))
    st.bar_chart(imp[imp.model.eq(model)].groupby('group').brier_increase.mean().sort_values(ascending=False))
    st.caption('Correlated raw/adjusted EPA and Elo can obscure importance. These diagnostics are noncausal.')
    st.image(str(run/'reliability.png'));st.dataframe(pd.read_csv(run/'personnel_coverage.csv'),hide_index=True)
    st.dataframe(pd.read_csv(run/'feature_coverage.csv'),hide_index=True)
    st.download_button('Download M6 comparison report',(run/'MODEL_COMPARISON.md').read_bytes(),file_name='M6_MODEL_COMPARISON.md',mime='text/markdown')
    st.json(json.loads((run/'metadata.json').read_text()))
