"""Fixed, forward-only margin research; no classifier or betting-ledger writes."""
from pathlib import Path
import hashlib
import json
import math
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from .boosting import check_features
from .elo import eligible_at, replay
from .history_features import COMMON, reconstruct
from .integrity import atomic_json, digest
from .market_math import decimal_odds
from .reporting import table

FEATURES=COMMON+['elo_difference']
CONFIG={'ridge_alpha':10.0,'boosting':{'loss':'squared_error','learning_rate':.05,
    'max_leaf_nodes':4,'max_depth':2,'max_iter':100,'min_samples_leaf':20,
    'l2_regularization':1.0,'early_stopping':False,'random_state':42}}
MODELS=['ridge','boosted']
THRESHOLDS=[0,3,5]


def load_compact(data):
    """Verify schedules/aggregated metrics only; never read or hash raw PBP."""
    data=Path(data);schedules=[];metrics=[];sources=[]
    for year in range(1999,2027):
        pointer=data/'manifests'/f'{year}.json'
        # 2026 is unnecessary for this historical experiment.
        if year==2026 and not pointer.exists():continue
        if not pointer.exists():raise ValueError(f'Missing cached season {year}; run update-history first')
        meta=json.loads(pointer.read_text());generation=data/'generations'/meta['generation']
        if generation.resolve().parent!=(data/'generations').resolve():raise ValueError('Invalid cache generation path')
        frames={}
        for name in ['schedules','metrics']:
            info=meta['files'][name];path=generation/info['file']
            if path.resolve().parent!=generation.resolve() or digest(path)!=info['sha256']:raise ValueError(f'Corrupt {year} {name} cache')
            frames[name]=pd.read_parquet(path)
        s=frames['schedules']
        if 'kickoff_precision' not in s:s['kickoff_precision']='scheduled_clock'
        if 'neutral_known' not in s:s['neutral_known']=s.location.notna()
        if 'result_available_at' not in s:s['result_available_at']=s.kickoff+pd.Timedelta(hours=8)
        schedules.append(s);metrics.append(frames['metrics'])
        sources.append({'season':year,'retrieved_at':meta.get('retrieved_at'),
                        'schedules_sha256':meta['files']['schedules']['sha256'],
                        'metrics_sha256':meta['files']['metrics']['sha256']})
    return pd.concat(schedules,ignore_index=True),pd.concat(metrics,ignore_index=True),sources


def prepare(schedules,features):
    """Scores/closing lines are authoritative schedule labels, never estimator inputs."""
    required={'game_id','season','week','game_type','kickoff','home_team','away_team','home_score','away_score','completed'}
    if required-set(schedules):raise ValueError(f'Missing schedule fields: {sorted(required-set(schedules))}')
    if schedules.game_id.isna().any() or schedules.game_id.duplicated().any():raise ValueError('Missing/duplicate schedule game IDs')
    if features.game_id.isna().any() or features.game_id.duplicated().any():raise ValueError('Missing/duplicate feature game IDs')
    if schedules.kickoff.dt.tz is None or features.data_cutoff.dt.tz is None:raise ValueError('Timezone-aware cutoffs required')
    s=schedules[schedules.game_type.eq('REG')].copy()
    scores=s[['home_score','away_score']].apply(pd.to_numeric,errors='coerce')
    valid=np.isfinite(scores).all(axis=1)&scores.ge(0).all(axis=1)&scores.eq(scores.round()).all(axis=1)
    s['available_at']=pd.to_datetime([eligible_at(g) if good else pd.NaT for g,good in zip(s.to_dict('records'),valid)],utc=True)
    s['actual_home_margin']=scores.home_score-scores.away_score
    s['market_home_margin']=pd.to_numeric(s.get('spread_line',pd.Series(np.nan,index=s.index)),errors='coerce')
    s.loc[~np.isfinite(s.market_home_margin),'market_home_margin']=np.nan
    coverage=[]
    for year,g in s.groupby('season'):
        final=g.available_at.notna()
        pairs=g.reindex(columns=['home_spread_odds','away_spread_odds'])
        present=pairs.notna().all(axis=1);valid_price=[]
        for h,a in pairs.itertuples(index=False,name=None):
            try:decimal_odds(h);decimal_odds(a);valid_price.append(True)
            except ValueError:valid_price.append(False)
        coverage.append({'season':int(year),'scheduled':len(g),'eligible_scores':int(final.sum()),
            'ties_included':int((final&g.actual_home_margin.eq(0)).sum()),
            'missing_invalid_spread':int((final&g.market_home_margin.isna()).sum()),
            'price_pairs_present':int(present.sum()),'price_pairs_valid':sum(valid_price)})
    s=s[s.available_at.notna()].copy()
    columns=['game_id','kickoff','home_team','away_team','data_cutoff']+FEATURES
    f=s.drop(columns=[c for c in FEATURES+['data_cutoff'] if c in s]).merge(features[columns],on='game_id',suffixes=('','_feature'),validate='one_to_one',how='left')
    if f.data_cutoff.isna().any():raise ValueError('Missing pregame feature rows/cutoffs; reconstruct historical features first')
    for column in ['kickoff','home_team','away_team']:
        if f[column].ne(f[column+'_feature']).any():raise ValueError(f'Feature/schedule {column} mismatch')
    if f.data_cutoff.gt(f.kickoff).any():raise ValueError('Feature cutoff after kickoff')
    check_features(f,FEATURES)
    return f.sort_values(['kickoff','game_id']).reset_index(drop=True),pd.DataFrame(coverage)


def fit(train):
    x=check_features(train,FEATURES);y=train.actual_home_margin.to_numpy(float)
    if not len(x) or not np.isfinite(y).all():raise ValueError('Finite completed margins required for training')
    ridge=make_pipeline(SimpleImputer(strategy='mean',keep_empty_features=True),StandardScaler(),Ridge(alpha=CONFIG['ridge_alpha']))
    # sklearn's histogram binner cannot handle wholly empty columns in some releases.
    active=[c for c in FEATURES if x[c].notna().any()]
    boosted=HistGradientBoostingRegressor(**CONFIG['boosting'])
    bx=x[active] if active else pd.DataFrame({'intercept':np.zeros(len(x))},index=x.index)
    with threadpool_limits(limits=2):
        ridge.fit(x,y);boosted.fit(bx,y)
    return {'ridge':ridge,'boosted':boosted,'active':active}


def predict(models,frame):
    x=check_features(frame,FEATURES);active=models['active']
    bx=x[active] if active else pd.DataFrame({'intercept':np.zeros(len(x))},index=x.index)
    with threadpool_limits(limits=2):
        result={'ridge':models['ridge'].predict(x),'boosted':models['boosted'].predict(bx)}
    if not all(np.isfinite(v).all() for v in result.values()):raise ValueError('Nonfinite predicted margins')
    return result


def annual(frame,directory,years=range(2019,2026)):
    """Freeze each pair of estimators before the first target-season kickoff."""
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);predictions=[];folds=[]
    for year in years:
        ev=frame[frame.season.eq(year)].copy()
        if ev.empty:raise ValueError(f'Missing evaluation season {year}')
        cutoff=ev.kickoff.min()
        tr=frame[frame.season.between(2008,year-1)&frame.available_at.lt(cutoff)&frame.kickoff.lt(cutoff)].copy()
        if tr.empty or tr.season.nunique()!=year-2008:raise ValueError(f'Missing prior-season training history for {year}')
        if tr.data_cutoff.gt(tr.kickoff).any() or ev.data_cutoff.gt(ev.kickoff).any():raise ValueError('Feature cutoff after kickoff')
        h=hashlib.sha256(Path(__file__).read_bytes())
        identity_columns=['game_id','season','kickoff','data_cutoff','available_at','actual_home_margin']+FEATURES
        h.update(pd.util.hash_pandas_object(tr[identity_columns],index=False).values.tobytes())
        h.update(json.dumps(CONFIG,sort_keys=True).encode());key=h.hexdigest()
        path=directory/f'{year}-{key}.joblib';sidecar=path.with_suffix('.json')
        reused=path.exists()
        if reused:
            if not sidecar.exists() or json.loads(sidecar.read_text())['sha256']!=digest(path):raise ValueError('Margin model cache integrity failure')
            models=joblib.load(path)
        else:
            models=fit(tr);temporary=path.with_suffix('.tmp');joblib.dump(models,temporary);temporary.replace(path)
            atomic_json({'sha256':digest(path),'training_fingerprint':key,'config':CONFIG},sidecar)
        values=predict(models,ev)
        keep=['game_id','season','week','kickoff','home_team','away_team','data_cutoff','actual_home_margin','market_home_margin']
        out=ev[keep].copy()
        for name in MODELS:out[name]=values[name]
        out['training_cutoff']=cutoff;out['latest_training_result']=tr.available_at.max();out['model_version']=f'm82-{year}-{key[:16]}'
        out['role']='development' if year<=2021 else 'exploratory_evaluation'
        predictions.append(out)
        folds.append({'season':year,'training_start':2008,'training_end':year-1,'training_games':len(tr),
            'training_cutoff':cutoff.isoformat(),'latest_training_result':tr.available_at.max().isoformat(),
            'evaluation_games':len(ev),'model_version':out.model_version.iloc[0],'cache_reused':reused})
        print(f'{year}: {len(tr)} training / {len(ev)} margin predictions; models '+('reused' if reused else 'fitted'),flush=True)
    return pd.concat(predictions,ignore_index=True),pd.DataFrame(folds)


def margin_metrics(frame,replicates=2000):
    """Reuse M3 season-week paired bootstrap mechanics for continuous MAE."""
    cluster=pd.factorize(pd.MultiIndex.from_frame(frame[['season','week']]))[0];k=int(cluster.max()+1)
    weights=np.random.default_rng(42).multinomial(k,np.full(k,1/k),size=replicates)
    counts=weights@np.bincount(cluster,minlength=k)
    y=frame.actual_home_margin.to_numpy(float);market=np.abs(frame.market_home_margin.to_numpy(float)-y);rows=[]
    for name,column in [('closing_market','market_home_margin')]+[(m,m) for m in MODELS]:
        error=frame[column].to_numpy(float)-y;loss=np.abs(error);delta=loss-market
        draws=(weights@np.bincount(cluster,weights=delta,minlength=k))/counts
        low,high=np.quantile(draws,[.025,.975])
        rows.append({'model':name,'games':len(y),'mae':float(loss.mean()),'rmse':float(np.sqrt(np.mean(error**2))),
            'bias_predicted_minus_actual':float(error.mean()),'mae_minus_market':float(delta.mean()),
            'difference_low':float(low),'difference_high':float(high)})
    return pd.DataFrame(rows)


def grade(frame,model,threshold):
    if model not in MODELS or threshold not in THRESHOLDS:raise ValueError('Only predefined models/thresholds are supported')
    edge=frame[model]-frame.market_home_margin
    selected=edge.ne(0)&(edge.abs()>=threshold)&np.isfinite(edge)&np.isfinite(frame.actual_home_margin)
    out=frame.loc[selected].copy();out['edge_points']=edge[selected]
    out['selected_side']=np.where(out.edge_points>0,'home','away')
    out['home_ats_residual']=out.actual_home_margin-out.market_home_margin
    result=np.sign(out.edge_points)*out.home_ats_residual
    out['ats_result']=np.where(result>0,'win',np.where(result<0,'loss','push'))
    return out


def wilson(wins,n):
    if not n:return np.nan,np.nan
    z=1.959963984540054;p=wins/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half


def ats_metrics(frame):
    rows=[]
    for model in MODELS:
        for threshold in THRESHOLDS:
            selected=grade(frame,model,threshold);w=int(selected.ats_result.eq('win').sum());loss=int(selected.ats_result.eq('loss').sum());push=int(selected.ats_result.eq('push').sum())
            low,high=wilson(w,w+loss)
            row={'model':model,'minimum_edge':threshold,'games_evaluated':len(frame),'selections':len(selected),
                'wins':w,'losses':loss,'pushes':push,'win_rate_ex_push':w/(w+loss) if w+loss else np.nan,
                'win_rate_low':low,'win_rate_high':high,'push_rate':push/len(selected) if len(selected) else np.nan}
            for side in ['home','away']:
                group=selected[selected.selected_side.eq(side)];decided=group[group.ats_result.ne('push')]
                row[side+'_selections']=len(group);row[side+'_win_rate']=float(decided.ats_result.eq('win').mean()) if len(decided) else np.nan
            row['home_minus_away_win_rate']=row['home_win_rate']-row['away_win_rate'];rows.append(row)
    return pd.DataFrame(rows)


def generate(root,data=None):
    started=time.perf_counter();root=Path(root);data=Path(data or root/'data')
    s,m,sources=load_compact(data)
    f,_=reconstruct(s,m,data/'history_features')
    # Standard Elo only; replay uses the existing event-driven availability rules.
    pre,_,_=replay(s[s.season.le(2025)])
    f=f[f.season.le(2025)].merge(pre[['game_id','elo_difference']],on='game_id',validate='one_to_one')
    frame,coverage=prepare(s[s.season.le(2025)],f)
    predictions,folds=annual(frame,root/'models/m82')
    matched=predictions[predictions.market_home_margin.notna()].copy()
    if matched.empty:raise ValueError('No valid closing spreads available; no ATS benchmark can be produced')
    identity=hashlib.sha256(pd.util.hash_pandas_object(predictions,index=False).values.tobytes()).hexdigest()[:16]
    out=root/'reports/m82'/identity;out.mkdir(parents=True,exist_ok=True)
    audit=predictions.copy()
    for model in MODELS:
        audit[model+'_edge_points']=audit[model]-audit.market_home_margin
        for threshold in THRESHOLDS:
            g=grade(audit,model,threshold);audit[f'{model}_ats_{threshold}']=audit.game_id.map(g.set_index('game_id').ats_result).astype('string').fillna('not_selected')
    audit.to_csv(out/'predictions.csv',index=False)
    folds.to_csv(out/'folds.csv',index=False)
    atomic_json({'source_classification':'historical_closing_reference','features':FEATURES,'config':CONFIG,'sources':sources},out/'metadata.json')
    lines=['# M8.2 NFL margin and historical ATS benchmark','',
        'Two fixed independent regression families; historical closing-line research only. Existing win-probability models, activation, official forecasts, M8 odds/wagers and M8.1 results are unchanged. No paper wagers or market API calls are generated.','',
        '## Coverage and sign verification','',table(coverage[coverage.season.ge(2008)]),'',
        'Training starts in 2008; 1999–2007 supplies existing Elo warmup/context. All eligible ties are retained with margin zero. Missing/invalid scores and unfinished/blocked results are excluded; missing/invalid spreads are excluded from the common evaluation sample, but not independent training. Missing feature values remain missing until training-only preprocessing.','',
        f'{len(predictions)} eligible predicted games; {len(matched)} matched closing spreads; {len(predictions)-len(matched)} spread exclusions across 2019–2025. Expected regular-season counts are 256 through 2020 and 272 thereafter; 2022 has 271 following the canceled Buffalo–Cincinnati game.','',
        '`actual_home_margin = home_score - away_score`; `market_home_margin = spread_line` (home-favorite-positive); home ATS residual = actual minus market. A positive model-minus-market edge selects home; negative selects away. Exact zero has no preference. Pushes are zero actual-minus-market residual, irrespective of chosen side.','',
        'Cached sign examples (negative home moneyline denotes the home favorite where paired prices are present):','',
        table(s[s.game_id.isin(['2024_01_BAL_KC','2024_01_TEN_CHI','2024_01_ARI_BUF','2024_02_SF_MIN'])].reindex(columns=['game_id','home_team','away_team','home_score','away_score','spread_line','home_moneyline','away_moneyline'])),'',
        'For KC–BAL: home margin +7, closing margin +3, home ATS residual +4. Away-favorite spreads are negative; unit tests also explicitly verify home +7 and away-favorite −3 orientation. These are source schedule closing fields; no book/quote timestamp is verified. Paired spread-price counts above are descriptive American-odds syntax checks only; invalid/missing prices never get fabricated or enter the regressors.','',
        '## Frozen training protocol and models','',
        'Each annual pair fits on completed 2008–previous-season games with result availability strictly before the first target-season kickoff. Estimators and preprocessing remain frozen throughout that season. Existing pregame team ratings and Elo continue updating only from earlier eligible games; conservative result availability is kickoff +8h, or the existing date-unknown upper bound. Historical features are retrospective data vintages, not timestamped original publications.','',
        'Development: 2019–2021. Final exploratory evaluation: 2022–2025. No configurations or thresholds were selected from either set of results. Previously examined 2024–2025 is not independent confirmation. Two families, three predefined thresholds (nonzero, ≥3, ≥5), seven annual fits each; no search, calibration or promotion.','',
        'Features: '+', '.join('`'+c+'`' for c in FEATURES)+'. Existing M5 common pregame home-minus-away features are reused; defensive signs are advantage-oriented. Four-game previous-season priors regress halfway toward prior league means. No rest feature, retrospective personnel/QB, scores, closing line or prices enter either estimator. Intercepts represent usual home advantage; neutral is explicit.','',
        'Ridge: mean imputation (empty training columns kept as zero), StandardScaler, fixed alpha=10. Boosted regressor: '+json.dumps(CONFIG['boosting'],sort_keys=True)+'. Native missing-value handling; wholly empty training columns are excluded using training rows only. CPU threads=2. Models live only in models/m82, with training-only content fingerprints and verified joblib checksums; they never enter the classifier registry.','',table(folds),'']
    for role,group in matched.groupby('role',sort=False):
        lines.extend(['## '+role,'',table(margin_metrics(group)),'',
            'Bias = predicted minus actual home points. MAE deltas = model minus market (negative favors model). Nominal 95% paired season-week percentile bootstrap, 2,000 replicates, seed 42, reusing existing resampling mechanics.','',
            'Historical ATS selections (not real bets); win rates exclude pushes:','',table(ats_metrics(group)),''])
    yearly=[];year_ats=[]
    for year,group in matched.groupby('season'):
        yearly.append(margin_metrics(group).assign(season=year));year_ats.append(ats_metrics(group).assign(season=year))
    lines.extend(['## Season-by-season margin results','',table(pd.concat(yearly,ignore_index=True)),'',
        '## Season-by-season ATS results','',table(pd.concat(year_ats,ignore_index=True)),'',
        '## Interpretation and limitations','',
        'The closing reference uses identical games for all three margin estimates. It may include information released after the model feature cutoff. Source-level spread prices are not verified same-book executable quotes; bookmaker, publication time and settlement rules are unknown. No realized ROI, EV, CLV or profitability is estimated. At hypothetical flat −110 only, conditional break-even excluding pushes is 110/210 = 52.38%; this does not establish those historical prices or a betting advantage.','',
        'Wilson 95% binomial intervals are descriptive and assume independent selected decisions. Repeated teams, correlated weeks, few seasons and six model/threshold comparisons weaken that assumption; no multiplicity adjustment or validated best threshold is claimed. The paired week bootstrap also assumes independent weeks and misses longer dependence. Margin accuracy improvements do not directly give cover probabilities. Point disagreements are not calibrated betting value.',''])
    primary=margin_metrics(matched[matched.role.eq('exploratory_evaluation')])
    deltas=primary[primary.model.ne('closing_market')].mae_minus_market
    recommendation=('Both independent models have larger measured exploratory MAE than the closing reference. A cover-probability model is not justified as a betting deployment from this evidence; keep it a deferred research question and first obtain genuine timestamp-aligned prospective data.' if deltas.ge(0).all() else 'Some independent margin estimates improve exploratory MAE relative to closing. This alone cannot justify a cover-probability deployment; any later research needs prespecified prospective evaluation and verified decision-time market data. No model or threshold is promoted here.')
    lines.extend(['## Recommendation','',recommendation,'','## Reproduction, verification and preservation','',
        '`python -m nfl_predictor.cli report-m82` reads cached schedule/metric Parquets and reuses compact historical features. It fits or loads two fixed regression families with annual training prefixes; no raw PBP is read or hashed. First-time data/feature setup follows the existing README historical-data workflow. No network is needed with complete caches.','',
        f'Game-level audit: `{out.relative_to(root)}/predictions.csv` (margins, cutoffs, versions, edge and grading for each threshold). Fold and source fingerprints accompany it. Generated caches/models/CSV stay gitignored. Measured command runtime: {time.perf_counter()-started:.2f} seconds; all outputs are historical, not issued pregame forecasts.','',
        'Verification results and preservation hashes are recorded below after execution. Native Windows certification was not performed; this execution uses Linux/Python 3.12.',''])
    report=root/'M82_SPREAD_BENCHMARK_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8')
    atomic_json({'run':identity},root/'reports/m82/latest.json')
    return report
