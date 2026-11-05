"""Read-only diagnostics of frozen historical probabilities. No model inference."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from .historical_market import prepare
from .ensemble import timestamp
from .analysis import TEAM_DIVISION
from .integrity import digest
from .reporting import table

BASES=['logistic_oos','boosting_oos','margin_elo']
FEATURES=['off_epa','def_epa','recent_off_epa','recent_def_epa','scoring','turnover','neutral']
CONFIDENCE_LABELS=['50–55%','55–60%','60–70%','70–80%','80–90%','90–100%']


def classify(frame):
    f=frame.copy();p=f.probability.astype(float);y=f.target.astype(float);market=f.market_probability.astype(float)
    if not np.isfinite(market).all() or not market.between(0,1).all():raise ValueError('Finite closing-market probabilities required')
    if f.duplicated(['game_id','model']).any():raise ValueError('Duplicate game/model predictions')
    if not y.isin([0,1]).all() or not np.isfinite(p).all() or not p.between(0,1).all():raise ValueError('Finite probabilities and binary non-tie outcomes required')
    f['predicted_home']=p.ge(.5);f['correct']=f.predicted_home.eq(y.eq(1));f['error']=~f.correct
    f['predicted_winner']=np.where(f.predicted_home,f.home_team,f.away_team)
    f['actual_winner']=np.where(y.eq(1),f.home_team,f.away_team)
    f['confidence']=np.maximum(p,1-p);f['expected_error']=1-f.confidence
    f['confidence_bucket']=pd.cut(f.confidence,[.5,.55,.6,.7,.8,.9,1.00000001],right=False,labels=CONFIDENCE_LABELS).astype(str)
    f['brier']=(p-y)**2;f['log_loss']=-(y*np.log(np.clip(p,1e-6,1))+(1-y)*np.log(np.clip(1-p,1e-6,1)))
    f['signed_residual']=y-p;f['absolute_error']=np.abs(y-p)
    f['calibration_error']=f.error.astype(float)-f.expected_error
    f['week_phase']=np.where(f.week.le(4),'1–4',np.where(f.week.le(12),'5–12','13+'))
    f['model_side']=np.where(f.predicted_home,'home','away')
    f['market_pick_home']=f.market_probability.ge(.5);f['market_confidence']=np.maximum(f.market_probability,1-f.market_probability)
    f['market_correct']=f.market_pick_home.eq(y.eq(1));f['market_brier']=(f.market_probability-y)**2
    f['market_probability_difference']=p-f.market_probability;f['brier_minus_market']=f.brier-f.market_brier
    f['favorite_agreement']=np.where(f.market_probability.eq(.5),'market_pickem',np.where(f.predicted_home.eq(f.market_pick_home),'same_favorite','opposite_favorite'))
    f['picked_market_role']=np.where(f.market_probability.eq(.5),'pickem',np.where(f.predicted_home.eq(f.market_pick_home),'favorite','underdog'))
    f['higher_confidence']=np.where(f.confidence.gt(f.market_confidence),'model',np.where(f.confidence.lt(f.market_confidence),'market','equal'))
    f['disagreement_band']=pd.cut(f.market_probability_difference.abs().round(12),[0,.05,.1,.2,1.00000001],right=False,labels=['<5pp','5–10pp','10–20pp','20pp+']).astype(str)
    f['divisional']=f.home_team.map(TEAM_DIVISION).eq(f.away_team.map(TEAM_DIVISION))
    for c in ['recent_off_epa','recent_def_epa']:
        f[c+'_band']=pd.cut(f[c].abs(),[0,.1,.25,np.inf],right=False,labels=['<0.10','0.10–0.25','0.25+']).astype(str).replace('nan','missing')
    for label,a,b in [('elo_efficiency','elo_difference','off_epa'),('recent_vs_season','recent_off_epa','off_epa'),('offense_defense','off_epa','def_epa')]:
        f[label]=np.where(f[a].isna()|f[b].isna(),'missing',np.where(np.sign(f[a]).eq(np.sign(f[b])),'same_direction','opposite_or_zero'))
    return f


def summarize(frame,keys,replicates=2000):
    """Season-week cluster intervals for error rate and confidence-adjusted gap."""
    rows=[]
    for values,g in frame.groupby(keys,dropna=False,observed=True):
        values=values if isinstance(values,tuple) else (values,)
        cluster=pd.factorize(pd.MultiIndex.from_frame(g[['season','week']]))[0];k=int(cluster.max()+1)
        weights=np.random.default_rng(42).multinomial(k,np.full(k,1/k),size=replicates)
        counts=weights@np.bincount(cluster,minlength=k)
        def interval(column):
            if k<2:return np.array([np.nan,np.nan])
            draws=(weights@np.bincount(cluster,weights=g[column].to_numpy(float),minlength=k))/counts
            return np.quantile(draws,[.025,.975])
        low,high=interval('error');gap_low,gap_high=interval('calibration_error');delta_low,delta_high=interval('brier_minus_market')
        reference=frame[frame.model.eq(g.model.iloc[0])]
        ref_gap=float(reference.calibration_error.mean())
        rows.append({**dict(zip(keys,values)),'games':len(g),'accuracy':float(g.correct.mean()),'market_brier':float(g.market_brier.mean()),'error_rate':float(g.error.mean()),'expected_error_rate':float(g.expected_error.mean()),
            'expected_win_rate':float(g.confidence.mean()),'actual_win_rate':float(g.correct.mean()),
            'brier':float(g.brier.mean()),'log_loss':float(g.log_loss.mean()),'signed_residual':float(g.signed_residual.mean()),
            'calibration_gap_actual_minus_expected_win':float(g.correct.mean()-g.confidence.mean()),
            'error_low':float(low),'error_high':float(high),'excess_error':float(g.calibration_error.mean()),
            'excess_error_low':float(gap_low),'excess_error_high':float(gap_high),
            'reference_model_error_rate':float(reference.error.mean()),'reference_model_brier':float(reference.brier.mean()),
            'excess_error_minus_model_reference':float(g.calibration_error.mean()-ref_gap),
            'brier_minus_market':float(g.brier_minus_market.mean()),'brier_delta_low':float(delta_low),'brier_delta_high':float(delta_high),
            'small_sample':len(g)<50,'clusters':k})
    return pd.DataFrame(rows)


def shared_failures(frame):
    f=frame[frame.model.isin(BASES)]
    if f.duplicated(['game_id','model']).any():raise ValueError('Duplicate shared-failure prediction')
    count=f.groupby('game_id').model.nunique()
    if not count.eq(3).all():raise ValueError('Shared failures require three identical-game base predictions')
    rows=[]
    for gid,g in f.groupby('game_id',sort=False):
        if g[['season','week','target','market_probability']].nunique().gt(1).any():raise ValueError('Shared-failure metadata conflict')
        wrong=int(g.error.sum());r=g.iloc[0]
        rows.append({'game_id':gid,'season':r.season,'week':r.week,'incorrect_models':wrong,
            'category':['all_correct','one_incorrect','two_incorrect','all_incorrect'][wrong],
            'winner_disagreement':g.predicted_home.nunique()>1,'confidence':g.confidence.mean(),'brier':g.brier.mean(),
            'market_correct':bool(r.market_correct),'market_favorite_agreement_fraction':float(g.predicted_home.eq(g.market_pick_home).mean()) if r.market_probability!=.5 else np.nan})
    games=pd.DataFrame(rows)
    summary=games.groupby('category').agg(games=('game_id','size'),average_confidence=('confidence','mean'),average_brier=('brier','mean'),market_accuracy=('market_correct','mean'),market_favorite_agreement=('market_favorite_agreement_fraction','mean')).reset_index()
    summary['sample_fraction']=summary.games/len(games)
    return games,summary


def load_inputs(root,data):
    root=Path(root);data=Path(data);pointer=root/'reports/m7/latest.json'
    if not pointer.exists():raise ValueError('Saved M7 prediction matrix unavailable; no retraining or reconstruction is permitted')
    directory=pointer.parent;run=directory/json.loads(pointer.read_text())['run']
    if run.resolve().parent!=directory.resolve():raise ValueError('Invalid M7 run path')
    checks=json.loads((run/'outputs.json').read_text());required=['base_predictions.parquet','predictions.parquet','selection.json','metadata.json']
    for name in required:
        if digest(run/name)!=checks[name]:raise ValueError('M7 saved prediction integrity failure: '+name)
    base=pd.read_parquet(run/'base_predictions.parquet');pred=pd.read_parquet(run/'predictions.parquet');selection=json.loads((run/'selection.json').read_text());meta=json.loads((run/'metadata.json').read_text())
    cutoffs={int(f['evaluation']):max(timestamp(f['meta_outcome_cutoff']),timestamp(f['calibration_outcome_cutoff']),timestamp(selection['outcome_cutoff'])) for f in meta['folds']}
    ensemble=pred[pred.model.eq(selection['method'])&pred.season.isin([2024,2025])].copy();minimum=base.set_index('game_id').data_cutoff
    ensemble=ensemble[[g in minimum and int(y) in cutoffs and timestamp(minimum[g])>cutoffs[int(y)] for g,y in zip(ensemble.game_id,ensemble.season)]]
    schedules=[];source_hashes=[];features=[];feature_missing=[]
    for year in sorted(base.season.unique()):
        pointer=data/'manifests'/f'{int(year)}.json'
        if not pointer.exists():continue
        m=json.loads(pointer.read_text());generation=data/'generations'/m['generation'];info=m['files']['schedules'];path=generation/info['file']
        if generation.resolve().parent!=(data/'generations').resolve() or path.resolve().parent!=generation.resolve() or digest(path)!=info['sha256']:raise ValueError('Schedule integrity/path failure')
        schedules.append(pd.read_parquet(path));source_hashes.append({'input':f'schedules/{year}','sha256':info['sha256']})
        paths=list((data/'history_features').glob(f'{year}-*.parquet'))
        if len(paths)!=1:feature_missing.append(int(year));continue
        path=paths[0]
        if digest(path)!=json.loads(path.with_suffix('.json').read_text())['sha256']:raise ValueError('Pregame feature integrity failure')
        f=pd.read_parquet(path);features.append(f[['game_id','season','week','kickoff','home_team','away_team','data_cutoff']+FEATURES])
        source_hashes.append({'input':f'pregame_features/{year}','sha256':digest(path)})
    if not schedules:raise ValueError('No cached schedules available; report requires existing caches')
    s=pd.concat(schedules,ignore_index=True);groups,audit=prepare(s,base,ensemble,selection['outcome_cutoff'])
    feature=pd.concat(features,ignore_index=True) if features else pd.DataFrame(columns=['game_id']+FEATURES)
    if feature.game_id.duplicated().any():raise ValueError('Duplicate pregame feature IDs')
    if len(feature):
        overlap=base[['game_id','season','week','kickoff','home_team','away_team','data_cutoff']].merge(feature,on='game_id',suffixes=('','_feature'),validate='one_to_one')
        for c in ['season','week','kickoff','home_team','away_team','data_cutoff']:
            if overlap[c].ne(overlap[c+'_feature']).any():raise ValueError('Pregame feature provenance mismatch: '+c)
        if feature.data_cutoff.gt(feature.kickoff).any():raise ValueError('Future information in cached features')
    metadata=s[['game_id','home_team','away_team','home_score','away_score']].merge(base[['game_id','elo_difference','data_cutoff']],on='game_id',validate='one_to_one')
    metadata=metadata.merge(feature[['game_id']+FEATURES],on='game_id',how='left',validate='one_to_one')
    results={}
    for sample,f in groups.items():
        market=f[f.model.eq('closing_market')][['game_id','probability']].rename(columns={'probability':'market_probability'})
        f=f[f.model.ne('closing_market')].merge(market,on='game_id',validate='many_to_one').merge(metadata,on='game_id',validate='many_to_one')
        results[sample]=classify(f)
    audit.update(missing_or_ambiguous_feature_seasons=feature_missing,missing_feature_game_rows=int(metadata[FEATURES].isna().all(axis=1).sum()))
    return results,audit,source_hashes+[{'input':n,'sha256':checks[n]} for n in required]


def generate(root,data=None,replicates=2000):
    root=Path(root);data=Path(data or root/'data');groups,audit,inputs=load_inputs(root,data)
    output=root/'reports/m91a';output.mkdir(parents=True,exist_ok=True)
    lines=['# M9.1A historical prediction errors and shared failures','',
        'Frozen historical OOS probabilities only; no training, inference, data downloads, personnel collection, new model features or policy changes. 2024–2025 are historically explored evaluation years, not independent prospective confirmation.','',
        '## Coverage and exclusions','',table(pd.DataFrame([{'measure':k,'value':v} for k,v in audit.items()])),'',
        'M8.1 exact-ID/team/kickoff/outcome matching and American-moneyline proportional no-vig conversion are reused. Ties, unfinished games, unavailable/malformed paired odds, invalid probabilities and conflicting metadata are excluded. All models use identical games within each sample; the base and frozen-ensemble samples remain separate. Features come only from checksum-verified cached pregame rows with identical cutoffs; unavailable/ambiguous caches remain missing, never reconstructed.','']
    all_classified=[];top_candidates=[];headlines=[]
    tables={'confidence':['confidence_bucket'],'season':['season'],'week_phase':['week_phase'],
        'favorite':['model_side','picked_market_role'],'market_agreement':['favorite_agreement'],
        'divisional':['divisional'],'divisional_confidence':['divisional','confidence_bucket'],
        'phase_confidence':['week_phase','confidence_bucket'],
        'recent_offense':['recent_off_epa_band'],'recent_defense':['recent_def_epa_band'],
        'elo_efficiency':['elo_efficiency'],'recent_vs_season':['recent_vs_season'],
        'offense_defense':['offense_defense'],'venue':['neutral'],
        'market_disagreement':['disagreement_band'],'market_confidence':['higher_confidence']}
    with threadpool_limits(limits=2):
        for sample,f in groups.items():
            if f.empty:lines.extend(['## '+sample,'','No matched observations.','']);continue
            f['sample']=sample;all_classified.append(f)
            summary=summarize(f,['model'],replicates);summary.to_csv(output/f'{sample}_overall.csv',index=False)
            lines.extend(['## '+sample,'',table(summary[['model','games','accuracy','error_rate','expected_error_rate','brier','market_brier','log_loss','excess_error','excess_error_low','excess_error_high','brier_minus_market']]),''])
            for name,keys in tables.items():
                result=summarize(f,['model']+keys,replicates);result.to_csv(output/f'{sample}_{name}.csv',index=False)
                if name in ['confidence','week_phase','divisional','market_agreement','market_disagreement']:
                    columns=['model']+keys+['games','error_rate','expected_error_rate','brier','excess_error','excess_error_low','excess_error_high','brier_minus_market']
                    lines.extend(['### '+name,'',table(result[columns]),''])
            teams=pd.concat([f.assign(team=f.home_team,signed_residual=f.signed_residual),f.assign(team=f.away_team,signed_residual=-f.signed_residual)],ignore_index=True)
            team_summary=summarize(teams,['model','team'],replicates);team_summary.to_csv(output/f'{sample}_teams.csv',index=False)
            lines.extend(['### Team diagnostics','', 'Largest absolute observed team residuals (descriptive, not persistent bias):','',table(team_summary.assign(magnitude=team_summary.signed_residual.abs()).sort_values('magnitude',ascending=False).head(6)[['model','team','games','signed_residual','error_rate','expected_error_rate']]),''])
            if sample=='all_base_history':
                games,shared=shared_failures(f);games.to_csv(output/'shared_game_failures.csv',index=False);shared.to_csv(output/'shared_failure_summary.csv',index=False)
                games.groupby(['season','week','category']).size().rename('games').reset_index().to_csv(output/'shared_failures_by_week.csv',index=False)
                lines.extend(['### Shared base-model failures (each game counted once)','',table(shared),'',f"Winner-side disagreements: {int(games.winner_disagreement.sum())}/{len(games)} games. Market accuracy where all three bases missed: {games.loc[games.category.eq('all_incorrect'),'market_correct'].mean():.3%}.",''])
                top_candidates.append(f)
            else:top_candidates.append(f[f.model.eq('frozen_ensemble')])
            correlations=[]
            for model,g in f.groupby('model'):
                for feature in FEATURES+['elo_difference']:
                    h=g[[feature,'error','signed_residual','brier']].dropna()
                    correlations.append({'model':model,'feature':feature,'games':len(h),'error_correlation':h[feature].corr(h.error.astype(float)) if len(h)>1 and h[feature].nunique()>1 and h.error.nunique()>1 else np.nan,'residual_correlation':h[feature].corr(h.signed_residual) if len(h)>1 and h[feature].nunique()>1 and h.signed_residual.nunique()>1 else np.nan})
            pd.DataFrame(correlations).to_csv(output/f'{sample}_feature_correlations.csv',index=False)
            headlines.append(summary.assign(sample=sample))
    if not all_classified:raise ValueError('No eligible classified errors; no results invented')
    pd.concat(all_classified,ignore_index=True).to_csv(root/'M91A_CLASSIFIED_ERRORS.csv',index=False,float_format='%.10g')
    top=pd.concat(top_candidates).drop_duplicates(['game_id','model']);top=top[top.error].sort_values(['confidence','game_id','model'],ascending=[False,True,True]).head(20)
    top.to_csv(output/'top20_incorrect.csv',index=False)
    cols=['season','week','game_id','home_team','away_team','home_score','away_score','model','probability','confidence','actual_winner','market_probability','market_probability_difference','off_epa','def_epa','recent_off_epa','recent_def_epa','elo_difference']
    notes=[]
    shared_path=output/'shared_game_failures.csv'
    if shared_path.exists():
        shared=pd.read_csv(shared_path);wrong=shared[shared.category.eq('all_incorrect')]
        notes.append(f"All three base models missed {len(wrong)}/{len(shared)} games ({len(wrong)/len(shared):.2%}); the market picked correctly in {int(wrong.market_correct.sum())}/{len(wrong)} of those. This is a descriptive same-game comparison, not an explanation of losses or an executable market opportunity.")
    phase_path=output/'all_base_history_week_phase.csv'
    if phase_path.exists():
        early=pd.read_csv(phase_path).query("week_phase=='1–4'")
        notes.append(f"Weeks 1–4 observed base-model error rates range from {early.error_rate.min():.2%} to {early.error_rate.max():.2%}; confidence-adjusted excess error ranges from {early.excess_error.min():.2%} to {early.excess_error.max():.2%}. All early-season excess-error intervals contain zero: {bool(((early.excess_error_low<=0)&(early.excess_error_high>=0)).all())}. Raw early-season difficulty alone does not establish a special calibration failure.")
    confidence_path=output/'all_base_history_confidence.csv'
    if confidence_path.exists():
        high=pd.read_csv(confidence_path);high=high[high.model.eq('margin_elo')&high.confidence_bucket.eq('80–90%')]
        if len(high):
            r=high.iloc[0]
            notes.append(f"The predefined 80–90% margin-Elo band has {int(r.games)} games, observed losses {r.error_rate:.2%} versus expected {r.expected_error_rate:.2%}; excess-error interval {r.excess_error_low:.2%} to {r.excess_error_high:.2%}. This is an exploratory calibration candidate among many slices, not a validated general effect or an instruction to recalibrate.")
    notes.append(f"The twenty most confident misses contain {top.game_id.nunique()} distinct games; {int(top.favorite_agreement.eq('same_favorite').sum())}/{len(top)} agree with the closing favorite. {int(top.recent_off_epa.abs().ge(.25).sum())}/{len(top)} have absolute recent offensive EPA advantage ≥0.25. These outcome-selected examples have no control group and cannot establish why a game was lost.")
    overall=pd.concat(headlines,ignore_index=True);covers=(overall.excess_error_low<=0)&(overall.excess_error_high>=0)
    notes.append(f'On their corresponding samples, {int(overall.brier_minus_market.gt(0).sum())}/{len(overall)} model comparisons have higher mean Brier than closing; {int(covers.sum())}/{len(overall)} aggregate excess-error intervals contain zero. These descriptive results must not be used to select a model or a winning story.')
    lines.extend(['## Measured findings','']+['- '+note for note in notes]+[''])
    lines.extend(['## Twenty most confident incorrect observations','',table(top[cols]),'',
        'Rows are unique model/game forecasts; several can describe the same game and are not independent examples. They were selected by confidence after seeing outcomes, so shared characteristics here cannot establish an explanatory mechanism. EPA/Elo/scoring values are pregame cache values, not postgame recalculations.','',
        '## Interpretation, uncertainty and candidate research','',
        'Probabilities exactly 50% use a deterministic home pick; market pick’em is labeled separately, not a favorite. Shared-failure groups are defined by observed outcomes, so their average confidence is descriptive rather than a conditional calibration test. Winner error is distinct from probabilistic loss: a 51% favorite is expected to lose 49% of games, while a high-confidence miss contributes far more Brier/log loss. Confidence buckets show expected versus observed win rates; calibration gap is actual minus expected win frequency. Excess error is observed minus predicted favorite-loss rate. Positive excess error may suggest overconfidence; its interval and reference must be inspected before calling a pattern systematic.','',
        'Every detailed slice reports count, expected error, error rate, Brier/log loss, reference model-wide error/Brier, confidence-adjusted excess error, and descriptive 95% season-week cluster intervals (2,000 resamples, seed 42). Matched Brier-minus-market intervals use identical games inside each slice. Model-wide references include the slice. Difference from that reference is descriptive; its own interval is not estimated. Compare phase_confidence and divisional_confidence within the same confidence band before interpreting raw group errors. Absolute EPA bands (<0.10, 0.10–0.25, ≥0.25), confidence and market bands were predefined, not selected to maximize an outcome.','',
        'Team tables count a game once for each participating team; they must not be summed into independent observations. Signed residual is actual minus probability in the named team perspective. Categories overlap, teams recur across weeks, and seasons are few. Week bootstrap assumes independent week clusters, misses longer dependence, and does not adjust for the many exploratory comparisons. Small samples (<50) are flagged; intervals are withheld when fewer than two week clusters are available, and small-sample bootstrap intervals remain unreliable. Correlations, extreme examples and category differences are noncausal and are not significance-selected discoveries.','',
        'Detailed feature diagnostics compare Elo versus offensive efficiency direction, recent versus season EPA direction, offense/defense advantage directions, and neutral/home venue. Zero directions are grouped with disagreement; missing values remain explicit. These are analysis labels, never new model inputs. Existing M2 production coefficient/contribution reports are not applied to the M7 annual-refit forecasts: they describe different fitted artifacts and would not justify per-game attribution here.','',
        'Hypotheses for future prespecified research: check whether any early-season excess error persists within confidence bands across seasons; examine whether recent/season efficiency conflicts repeat prospectively; collect timestamp-aligned market observations to distinguish later market information from model disagreement. None establishes an injury, QB, weather or football-causal explanation. Negative/inconclusive strata and confidence intervals are retained in the CSVs; no model, feature, threshold or team adjustment is selected.','',
        'Closing prices can include later information than model cutoffs. Bookmaker, original quote time and executable prices are unknown. Historical data/model vintages and previously explored evaluation years limit inference. The analysis does not identify executable betting opportunities or profitability.','',
        'Recommended next research: preserve the existing models and M8.3 checkpoint policy, collect genuinely aligned prospective forecasts/markets, and preregister any proposed confidence/season-phase contrast before further evaluation. No M9.2 modeling is started.','',
        '## Reproduction and audit','', '`python -m nfl_predictor.cli report-m91a` reads only existing M7 outputs, schedule Parquets and compact pregame caches. Detailed tables: reports/m91a; game/model errors: M91A_CLASSIFIED_ERRORS.csv. Duplicate sample labels identify repeated base rows in the narrower comparison; do not pool samples.','',table(pd.DataFrame(inputs)),'',
        'Native Windows testing has not been executed. Focused/full test and preservation results are appended after actual verification.',''])
    report=root/'M91A_PREDICTION_ERROR_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8');return report
