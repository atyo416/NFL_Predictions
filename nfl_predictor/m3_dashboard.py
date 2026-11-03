"""Experimental ratings are displayed separately from official champion forecasts."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from .elo import probability
from .quarterbacks import cached_context,context
from .schedule_features import schedule_features


def saved_ratings(data):
    pointer=data/'ratings/latest.json'
    if not pointer.exists():return None,None,None
    directory=pointer.parent/json.loads(pointer.read_text())['run']
    from .integrity import digest
    checks=json.loads((directory/'outputs.json').read_text())
    if any(digest(directory/name)!=sha for name,sha in checks.items()):raise ValueError('Saved ratings failed integrity verification; regenerate ratings')
    return pd.read_parquet(directory/'rankings.parquet'),pd.read_parquet(directory/'history.parquet'),json.loads((directory/'metadata.json').read_text())

def render_rankings(data,reports):
    st.info('Experimental standard Elo power rankings. The official M2 champion is unchanged.')
    ranking,history,metadata=saved_ratings(data)
    if ranking is None:
        st.warning('Run python -m nfl_predictor.cli ratings to build the ranking snapshots.');return
    st.caption('Rating cutoff: '+metadata['cutoff']+' · previous-week rank means seven days earlier.')
    stamps=[m['retrieved_at'] for m in metadata['source_manifests'].values() if isinstance(m,dict) and m.get('retrieved_at')]
    if stamps:
        stamp=min(stamps);st.caption('Oldest contributing source retrieval: '+stamp)
        if pd.Timestamp.now(tz='UTC')-pd.Timestamp(stamp)>pd.Timedelta(days=2):st.warning('Contributing source data is more than two days old; refresh source and rebuild ratings.')
    st.dataframe(ranking[['rank','team','elo','previous_week_rank','weekly_change','record','last_opponent','last_result']],hide_index=True)
    st.download_button('Download current power rankings',ranking.to_csv(index=False),file_name='power_rankings.csv',mime='text/csv')
    team=st.selectbox('Rating history team',sorted(ranking.team))
    if len(history):
        years=sorted(history.season.unique());season=st.selectbox('Rating history season',years,index=len(years)-1)
        h=history[history.team.eq(team)&history.season.eq(season)].sort_values('available_at')
        st.caption('Postgame ratings plotted at result eligibility time, never at pregame kickoff.')
        if len(h):st.line_chart(h.set_index('available_at')[['postgame_elo']]);st.dataframe(h,hide_index=True)
    pointer=reports/'m3/latest.json'
    if pointer.exists():
        run=pointer.parent/json.loads(pointer.read_text())['run']
        st.subheader('M3 exploratory model comparisons')
        c=pd.read_csv(run/'comparison.csv');period=st.selectbox('M3 evaluation period',c.period.unique())
        st.dataframe(c[c.period.eq(period)],hide_index=True)
        st.caption('Model minus M2 champion. Positive accuracy and negative Brier/log-loss favor a candidate. Week-block intervals are exploratory and unadjusted.')
        st.image(str(run/'reliability.png'))
        st.subheader('Rest, bye and QB coverage')
        st.dataframe(pd.read_csv(run/'feature_missingness.csv'),hide_index=True)
        st.dataframe(pd.read_csv(run/'post_bye_diagnostic.csv'),hide_index=True)
        st.json(json.loads((run/'metadata.json').read_text()))

def render_matchup(schedules,data,a,b,game_id=None):
    ranking,_,metadata=saved_ratings(data)
    st.subheader('Experimental Elo and schedule context')
    if ranking is None:st.caption('Build ratings with python -m nfl_predictor.cli ratings.')
    else:
        st.caption('Saved rating cutoff: '+metadata['cutoff'])
        st.dataframe(ranking[ranking.team.isin([a,b])][['team','elo','rank','record']],hide_index=True)
    records=cached_context(data/'qb_context');cutoff=pd.Timestamp.now(tz='UTC')
    if game_id is not None:
        game=schedules[schedules.game_id.eq(game_id)].iloc[0]
        if ranking is not None:
            values=ranking.set_index('team').elo
            p=probability(values[game.home_team],values[game.away_team],bool(game.neutral))
            st.write(f'Experimental Elo difference (home minus away): {values[game.home_team]-values[game.away_team]:.1f}; Elo-only home win probability: {p:.1%}')
        rest=schedule_features(schedules,cutoff=cutoff,game_ids=[game_id])
        st.dataframe(rest,hide_index=True)
        qb=[context(schedules,records,t,game_id,min(cutoff,game.kickoff)) for t in [a,b]]
        st.dataframe(pd.DataFrame(qb),hide_index=True)
    else:st.caption('Choose an eligible scheduled matchup to view venue-specific Elo probabilities, rest and verified QB context.')
    if len(records):
        candidates=records[records.team.isin([a,b]) & ~records.classification.eq('verified_pregame')].copy()
        if len(candidates):
            candidates=candidates.sort_values('source_at',na_position='first').groupby('team',as_index=False).tail(1)
            st.warning('Depth-chart candidates below are unverified source observations, not confirmed starters or confirmation of health. Source dates may be stale.')
            st.dataframe(candidates[['team','player_id','name','source_at','observed_at','classification','quality','availability_status']],hide_index=True)
