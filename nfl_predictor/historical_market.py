"""Lean closing-reference benchmark. Read cached predictions; never fit or issue."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .market_math import decimal_odds,market_pair
from .ensemble import validate_matrix,timestamp,PROBABILITIES
from .analysis import paired_intervals
from .evaluation import evaluate
from .integrity import digest
from .reporting import table

SOURCE='historical_closing_reference'
BASE_MODELS=dict(zip(PROBABILITIES,['logistic_oos','boosting_oos','margin_elo']))


def prepare(schedules,base,ensemble=None,selection_cutoff=None):
    """Return identical-game base and optional ensemble groups plus exclusion audit."""
    for name,f in [('schedules',schedules),('base predictions',base)]:
        if f.game_id.isna().any() or f.game_id.duplicated().any():raise ValueError(f'Duplicate/missing game IDs in {name}')
    s=schedules[schedules.game_type.eq('REG')].copy()
    audit={'source_classification':SOURCE,'schedule_games':len(s),'base_prediction_games':len(base),'unmatched_prediction_ids':int((~base.game_id.isin(s.game_id)).sum())}
    final=s.completed&s.home_score.notna()&s.away_score.notna()
    ties=final&s.home_score.eq(s.away_score)
    audit.update(incomplete_scores=int((~final).sum()),ties_excluded=int(ties.sum()))
    missing=pd.Series(False,index=s.index);invalid=missing.copy();market=[]
    for i,g in s.iterrows():
        if not final.loc[i] or ties.loc[i]:continue
        if any(c not in s or pd.isna(g[c]) for c in ['home_moneyline','away_moneyline']):missing.loc[i]=True;continue
        try:pair=market_pair(decimal_odds(g.home_moneyline),decimal_odds(g.away_moneyline))
        except ValueError:invalid.loc[i]=True;continue
        market.append({'game_id':g.game_id,'season':g.season,'week':g.week,'home_team':g.home_team,'away_team':g.away_team,'kickoff':g.kickoff,'target':int(g.home_score>g.away_score),**pair})
    audit.update(missing_closing_pair=int(missing.sum()),invalid_closing_pair=int(invalid.sum()),usable_closing_pairs=len(market),underround_pairs=sum(r['underround'] for r in market))
    valid_prob=base[PROBABILITIES].apply(pd.to_numeric,errors='coerce')
    ok=np.isfinite(valid_prob).all(axis=1)&valid_prob.ge(0).all(axis=1)&valid_prob.le(1).all(axis=1)
    audit['missing_or_invalid_model_probabilities']=int((~ok).sum())
    b=base.loc[ok].copy();validate_matrix(b,True)
    market=pd.DataFrame(market,columns=['game_id','season','week','home_team','away_team','kickoff','target','no_vig_home']) if not market else pd.DataFrame(market)
    joined=market.merge(b,on='game_id',suffixes=('','_model'),validate='one_to_one')
    conflict=pd.Series(False,index=joined.index)
    for column in ['season','week','home_team','away_team','target','kickoff']:conflict|=joined[column].ne(joined[column+'_model'])
    audit['metadata_conflicts']=int(conflict.sum());joined=joined[~conflict].copy()
    audit['closing_games_without_base_predictions']=int((~market.game_id.isin(base.game_id)).sum())
    audit['base_matched_games']=len(joined)
    def long(f,include_ensemble=False):
        frames=[]
        for column,name in [('no_vig_home','closing_market')]+list(BASE_MODELS.items())+([('p_ensemble','frozen_ensemble')] if include_ensemble else []):
            result=f[['game_id','season','week','target']].copy();result['model']=name;result['probability']=f[column].astype(float);frames.append(result)
        return pd.concat(frames,ignore_index=True)
    groups={'all_base_history':long(joined)}
    if ensemble is not None and len(ensemble):
        if ensemble.game_id.duplicated().any():raise ValueError('Duplicate selected ensemble/game predictions')
        e=ensemble.rename(columns={'probability':'p_ensemble'})
        common=joined.merge(e[['game_id','season','week','target','p_ensemble']],on='game_id',suffixes=('','_ensemble'),validate='one_to_one')
        metadata_ok=common.target.eq(common.target_ensemble)&common.season.eq(common.season_ensemble)&common.week.eq(common.week_ensemble)
        audit['ensemble_metadata_conflicts']=int((~metadata_ok).sum())
        probability=pd.to_numeric(common.p_ensemble,errors='coerce')
        eligible=metadata_ok&np.isfinite(probability)&probability.between(0,1)
        # Development-selected policy is not considered available during selection years.
        if selection_cutoff is not None:eligible&=common.data_cutoff.gt(timestamp(selection_cutoff))
        common=common[eligible].copy();groups['with_frozen_ensemble']=long(common,True)
        audit['ensemble_matched_games']=len(common)
    else:audit['ensemble_matched_games']=0
    audit['base_games_without_eligible_ensemble']=len(joined)-audit['ensemble_matched_games']
    return groups,audit


def generate(root,data=None,replicates=2000):
    root=Path(root);data=Path(data or root/'data');output=root/'M81_HISTORICAL_MARKET_REPORT.md'
    pointer=root/'reports/m7/latest.json'
    if not pointer.exists():
        output.write_text('# M8.1 historical market benchmark\n\nUnavailable: no cached M7 historical prediction matrix. No models were trained.\n');return output
    run=pointer.parent/json.loads(pointer.read_text())['run'];checks=json.loads((run/'outputs.json').read_text())
    required=['base_predictions.parquet','predictions.parquet','selection.json','metadata.json']
    for name in required:
        if name not in checks or digest(run/name)!=checks[name]:raise ValueError(f'M7 cached input integrity failure: {name}')
    base=pd.read_parquet(run/'base_predictions.parquet');predictions=pd.read_parquet(run/'predictions.parquet')
    selection=json.loads((run/'selection.json').read_text());metadata=json.loads((run/'metadata.json').read_text())
    ensemble=predictions[predictions.model.eq(selection['method'])].copy()
    # Enforce the existing meta/calibration bounds as well as the policy-selection bound.
    cutoffs={f['evaluation']:max(timestamp(f['meta_outcome_cutoff']),timestamp(f['calibration_outcome_cutoff']),timestamp(selection['outcome_cutoff'])) for f in metadata['folds']}
    minimum=base.set_index('game_id').data_cutoff
    ensemble=ensemble[[g in minimum and int(y) in cutoffs and timestamp(minimum[g])>cutoffs[int(y)] for g,y in zip(ensemble.game_id,ensemble.season)]]
    schedules=[];coverage=[];sources=[]
    for year in sorted(base.season.unique()):
        manifest=data/'manifests'/f'{int(year)}.json'
        if not manifest.exists():coverage.append({'season':int(year),'schedule_games':0,'paired_moneylines':0,'note':'schedule cache unavailable'});continue
        m=json.loads(manifest.read_text());info=m['files']['schedules'];path=data/'generations'/m['generation']/info['file']
        if (data/'generations'/m['generation']).resolve().parent!=(data/'generations').resolve():raise ValueError('Invalid schedule generation path')
        if path.resolve().parent!=(data/'generations'/m['generation']).resolve() or digest(path)!=info['sha256']:raise ValueError('Schedule cache integrity failure')
        columns=['game_id','season','week','game_type','kickoff','home_team','away_team','home_score','away_score','completed']
        available=info['columns'];odds=[c for c in ['home_moneyline','away_moneyline'] if c in available]
        s=pd.read_parquet(path,columns=columns+odds);schedules.append(s)
        paired=int(s[odds].notna().all(axis=1).sum()) if len(odds)==2 else 0
        coverage.append({'season':int(year),'schedule_games':len(s),'paired_moneylines':paired,'note':'paired fields present' if len(odds)==2 else 'missing paired moneyline columns'})
        sources.append({'season':int(year),'sha256':info['sha256'],'retrieved_at':m.get('retrieved_at','unknown')})
    if not schedules:
        output.write_text('# M8.1 historical market benchmark\n\nUnavailable: schedule caches are missing. No prices were invented or models trained.\n');return output
    groups,audit=prepare(pd.concat(schedules,ignore_index=True),base,ensemble,selection['outcome_cutoff'])
    lines=['# M8.1 historical market benchmark','',f"Source: cached nflverse/nflreadpy schedules, `home_moneyline` and `away_moneyline`; classification `{SOURCE}`. Predictions: unchanged M7 run `{run.name}`; selected ensemble `{selection['method']}`.",'', 'No model fitting, calibration, policy selection, API fetch, wager simulation or ledger writes were performed.','', '## Coverage and exclusions','',table(pd.DataFrame(coverage)),'',table(pd.DataFrame([{'reason_or_count':k,'value':v} for k,v in audit.items()])), '', 'Exclusion counts describe successive eligibility checks, not independent samples. Missing schedule caches also appear as unmatched prediction IDs. Ties and incomplete scores are excluded before moneyline checks. Invalid/missing probabilities are removed for every model in a comparison. Metadata conflicts include team orientation, kickoff, season/week or outcome disagreement.','']
    summaries={}
    for label,frame in groups.items():
        if frame.empty:lines.extend(['## '+label,'','Unavailable: no common eligible sample.','']);continue
        result=paired_intervals(frame,replicates=replicates,seed=42,reference='closing_market')
        values=result.pivot(index='model',columns='metric',values='estimate').reset_index()
        delta=result[result.metric.eq('brier')][['model','games','difference','difference_low','difference_high']]
        summary=values.merge(delta,on='model');summaries[label]=summary
        title='Five-way frozen-policy sample' if label=='with_frozen_ensemble' else 'Four-way full base-prediction history'
        lines.extend(['## '+title,'',table(summary[['model','games','accuracy','brier','log_loss','difference','difference_low','difference_high']]),'',f"Brier deltas are model minus closing market; lower is better. Intervals: paired season-week percentile bootstrap, {replicates} replicates, seed 42, nominal 95%. The market self-difference is zero by construction.",'', 'Season-by-season results:',''])
        seasonal=[{'season':int(y),'model':name,**evaluate(g.target,g.probability)} for (y,name),g in frame.groupby(['season','model'])]
        lines.extend([table(pd.DataFrame(seasonal)[['season','model','games','accuracy','brier','log_loss']]),''])
    lines.extend(['## Interpretation and limitations','', 'All rows within each table use identical games and home-win orientation. The four-way table uses all available base history; the five-way table narrows to availability of the frozen ensemble and its prior meta/calibration/selection cutoffs. Do not compare scores across these different samples as an ensemble effect. No alternative ensemble was selected from these results.','', 'These are source-level closing-line pairs, not verified same-book snapshots. Bookmaker identity, precise quote/publication timestamps, executable prices and settlement rules are unknown and have not been fabricated. M8 decimal conversion and proportional no-vig functions are reused; their margin is only a source-pair overround proxy here. This source is never imported into the M8 sportsbook/wager ledger.','', 'Closing lines may contain later information than the model predictions; exact relative timing cannot be verified. Cached/model/data vintages are retrospective, not genuinely issued market forecasts. Historical model probabilities retain the M7 chronological contracts, including annual base refits; they are not the currently deployed production artifact applied backward. The M2 and M5 labels identify architectures, with the existing M7 annual training policy.','', 'Previously examined 2024–2025 is exploratory, and ensemble choice used earlier development years. Paired intervals are unadjusted descriptive evidence: repeated teams, interweek dependence, few seasons and prior model comparisons limit certainty. Binary scoring excludes ties and does not establish applicable market rules. No profitability, EV strategy, CLV certification or genuine prospective advantage is inferred.',''])
    primary=summaries.get('with_frozen_ensemble',summaries.get('all_base_history'))
    if primary is None:recommendation='No meaningful paired comparison is available. Stop at the data limitation; do not invent prices or expand the scope.'
    elif primary.loc[primary.model.ne('closing_market'),'difference'].ge(0).all():recommendation='The closing reference has the lowest measured Brier score on the primary common sample. Further research is worthwhile as a timing/calibration diagnostic, but these results do not support model outperformance. Prioritize genuinely timestamp-aligned prospective comparisons; retain all models and policies unchanged.'
    else:recommendation='Some model estimates have lower measured Brier than the closing reference on this exploratory sample. Further timestamp-aligned prospective validation is worthwhile; these retrospective differences do not justify selecting a new model, policy or probability adjustment.'
    lines.extend(['## Recommendation','',recommendation,'','## Reproducibility','', '`python -m nfl_predictor.cli report-m81` reads only schedule Parquets and saved M7 prediction/report files. No full PBP processing is needed.','',table(pd.DataFrame(sources)),'', 'M7 input SHA-256:','',table(pd.DataFrame([{'input':name,'sha256':checks[name]} for name in required])),''])
    output.write_text('\n'.join(lines),encoding='utf-8');return output
