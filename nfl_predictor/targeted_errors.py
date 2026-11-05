"""Read-only market, late-season and observed coaching diagnostics. No fitting."""
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import polars as pl
from threadpoolctl import threadpool_limits
from .prediction_errors import load_inputs, summarize, BASES
from .ensemble import timestamp
from .elo import regular_games, eligible_at
from .data_loader import ALIASES
from .integrity import digest
from .reporting import table

PLAYOFF_STATUSES={'eliminated','berth_clinched','division_clinched','seeding_competitive','unresolved'}


def market_groups(frame):
    """Outcome-independent labels are defined solely from saved probabilities."""
    rows=[]
    for gid,g in frame[frame.model.isin(BASES)].groupby('game_id',sort=False):
        if len(g)!=3 or set(g.model)!=set(BASES):raise ValueError('Three unique matched base models required')
        if g[['season','week','target','market_probability']].nunique().gt(1).any():raise ValueError('Conflicting game metadata')
        r=g.iloc[0];unanimous=g.predicted_home.nunique()==1;pickem=r.market_probability==.5
        side_agreement=bool(g.predicted_home.iloc[0]==r.market_pick_home)
        group='models_split' if not unanimous else 'market_pickem' if pickem else 'unanimous_same_as_market' if side_agreement else 'unanimous_opposite_market'
        wrong=bool(g.error.all());market_right=bool(r.market_correct)
        rows.append({'game_id':gid,'season':r.season,'week':r.week,'market_group':group,
            'all_models_wrong':wrong,'market_correct_shared_failure':wrong and market_right,
            'all_predictors_wrong':wrong and not market_right,'base_mean_confidence':g.confidence.mean(),
            'market_confidence':r.market_confidence,'market_correct':market_right,'base_mean_brier':g.brier.mean()})
    return pd.DataFrame(rows)


def coaching_assignments(schedules):
    """Names are observed game assignments, not verified pregame appointments."""
    s=regular_games(schedules);rows=[]
    for side in ['home','away']:
        for g in s.to_dict('records'):
            value=g.get(side+'_coach');coach=str(value).strip() if pd.notna(value) else None
            rows.append({'game_id':g['game_id'],'season':int(g['season']),'week':int(g['week']),'kickoff':g['kickoff'],
                         'team':g[side+'_team'],'coach':coach or None,'side':side})
    frame=pd.DataFrame(rows);output=[]
    for team,games in frame.groupby('team'):
        previous=None;seen_year=None;continuity_start_year=None;change_year=None;number=0;in_season=False;spell=0
        for r in games.sort_values(['kickoff','game_id']).to_dict('records'):
            coach=r['coach'];year=r['season']
            if coach is None:
                previous=None;seen_year=None;continuity_start_year=None;change_year=None;number=0;group='unknown'
            elif previous is not None and coach!=previous:
                change_year=year;number=1;in_season=seen_year==year;spell+=1;group='first_four_after_observed_change'
            elif coach==previous and change_year is not None:
                number+=1
                group='first_four_after_observed_change' if number<=4 else 'remaining_observed_first_season' if year==change_year else 'established_observed'
            else:
                group='established_observed' if previous==coach and continuity_start_year is not None and continuity_start_year<year else 'unknown_left_censored'
                number+=1
            output.append({**r,'coach_group':group,'spell_id':f'{team}-{spell}',
                'games_since_observed_change':number if change_year is not None else None,
                'in_season_replacement_proxy':bool(change_year==year and in_season),
                'interim_status':'unknown','effective_start':None,'effective_end':None,
                'source_publication_at':None,'source':'nflverse schedule coach fields','source_reference':'https://nflreadr.nflverse.com/reference/load_schedules.html','assignment_quality':'retrospective_schedule_assignment'})
            if coach is not None:
                if previous!=coach:continuity_start_year=year
                previous=coach;seen_year=year
    return pd.DataFrame(output)


def verified_playoff_status(evidence,game,team):
    eligible=[]
    for r in evidence or []:
        if r.get('game_id')!=game['game_id'] or r.get('team')!=team:continue
        try:
            times=[timestamp(r[k]) for k in ['published_at','captured_at','preserved_at']]
            if not times[0]<=times[1]<=times[2]<timestamp(game['kickoff']):continue
            if r.get('verification')!='verified_pregame' or not r.get('source_reference') or r.get('status') not in PLAYOFF_STATUSES:continue
            eligible.append(r)
        except (KeyError,ValueError,TypeError):continue
    statuses={r['status'] for r in eligible}
    return next(iter(statuses)) if len(statuses)==1 else 'unknown'


def pregame_context(schedules,targets=None,evidence=None):
    s=regular_games(schedules);s['eligible_at']=pd.to_datetime([eligible_at(g) for g in s.to_dict('records')],utc=True);rows=[]
    targets=s[s.season.between(2019,2025)] if targets is None else targets
    for g in targets.to_dict('records'):
        at=timestamp(g['kickoff']);past=s[s.season.eq(g['season'])&s.kickoff.lt(at)&s.eligible_at.lt(at)]
        for side in ['home','away']:
            team=g[side+'_team'];history=past[past.home_team.eq(team)|past.away_team.eq(team)].sort_values(['kickoff','game_id'])
            wins=losses=ties=0;qbs=[]
            for prior in history.to_dict('records'):
                own='home' if prior['home_team']==team else 'away';other='away' if own=='home' else 'home'
                margin=prior[own+'_score']-prior[other+'_score'];wins+=margin>0;losses+=margin<0;ties+=margin==0
                qbs.append(prior.get(own+'_qb_id'))
            valid=len(qbs)>=2 and all(pd.notna(v) for v in qbs[-2:])
            rows.append({'game_id':g['game_id'],'team':team,'season':g['season'],'week':g['week'],'cutoff':at,
                'wins_before':int(wins),'losses_before':int(losses),'ties_before':int(ties),'completed_before':len(history),
                'latest_prior_result':history.eligible_at.max() if len(history) else pd.NaT,
                'playoff_status':verified_playoff_status(evidence,g,team),
                'prior_observed_qb_change':bool(qbs[-1]!=qbs[-2]) if valid else None,
                'starter_rest_evidence':'unknown'})
    return pd.DataFrame(rows)


def postgame_participation(schedules,snaps):
    """Target snap share is retrospective and never supplies pregame categories."""
    columns=['game_id','team','prior_snap_game','prior_player_id','prior_qb_share','target_same_player_share','share_drop','participation_class']
    required={'game_id','team','position','pfr_player_id','offense_snaps','offense_pct'}
    if snaps.empty or required-set(snaps):return pd.DataFrame(columns=columns)
    s=regular_games(schedules);s['eligible_at']=pd.to_datetime([eligible_at(g) for g in s.to_dict('records')],utc=True)
    q=snaps[snaps.position.eq('QB')].copy();q['team']=q.team.replace(ALIASES);rows=[]
    for g in s[s.week.ge(16)&s.season.between(2019,2025)&s.completed&s.eligible_at.notna()].to_dict('records'):
        for team in [g['home_team'],g['away_team']]:
            history=s[s.season.eq(g['season'])&s.kickoff.lt(g['kickoff'])&s.eligible_at.lt(g['kickoff'])&(s.home_team.eq(team)|s.away_team.eq(team))]
            if history.empty:continue
            previous=history.iloc[-1].game_id;prior=q[q.game_id.eq(previous)&q.team.eq(team)]
            target=q[q.game_id.eq(g['game_id'])&q.team.eq(team)]
            if prior.empty or target.empty:continue
            leaders=prior[prior.offense_snaps.eq(prior.offense_snaps.max())]
            if leaders.pfr_player_id.nunique()!=1:continue
            p=leaders.iloc[0];same=target[target.pfr_player_id.eq(p.pfr_player_id)]
            target_share=float(same.offense_pct.iloc[0]) if len(same)==1 else np.nan
            drop=float(p.offense_pct)-target_share
            rows.append({'game_id':g['game_id'],'team':team,'prior_snap_game':previous,'prior_player_id':p.pfr_player_id,
                'prior_qb_share':float(p.offense_pct),'target_same_player_share':target_share,'share_drop':drop,
                'participation_class':'target_record_missing' if pd.isna(drop) else 'observed_drop_50pp_plus' if drop>=.5 else 'no_50pp_drop'})
    return pd.DataFrame(rows,columns=columns)


def load_data(root,data):
    from .prediction_errors import load_inputs
    root=Path(root);data=Path(data);source=root/'M91A_CLASSIFIED_ERRORS.csv'
    if not source.exists():raise ValueError('M9.1A classified errors unavailable; generate report-m91a from saved matrices first')
    frame=pd.read_csv(source);groups,audit,hashes=load_inputs(root,data)
    expected=pd.concat([f.assign(sample=name) for name,f in groups.items()],ignore_index=True)
    keys=['sample','game_id','model']
    if frame.duplicated(keys).any() or set(map(tuple,frame[keys].to_numpy()))!=set(map(tuple,expected[keys].to_numpy())):raise ValueError('M9.1A game/model/sample identity mismatch')
    a=frame.set_index(keys).sort_index();b=expected.set_index(keys).sort_index()
    for c in ['probability','market_probability','target']:
        if not np.allclose(a[c].astype(float),b[c].astype(float),rtol=0,atol=5e-10):raise ValueError('M9.1A probability/outcome mismatch')
    for c in ['season','week','home_team','away_team','error','predicted_home']:
        if a[c].ne(b[c]).any():raise ValueError('M9.1A metadata/classification mismatch: '+c)
    schedules=[]
    for year in range(2018,2026):
        pointer=data/'manifests'/f'{year}.json'
        if not pointer.exists():continue
        m=json.loads(pointer.read_text());gen=data/'generations'/m['generation'];info=m['files']['schedules'];path=gen/info['file']
        if gen.resolve().parent!=(data/'generations').resolve() or path.resolve().parent!=gen.resolve() or digest(path)!=info['sha256']:raise ValueError('Schedule cache integrity/path failure')
        schedules.append(pd.read_parquet(path));hashes.append({'input':f'coaching_context_schedules/{year}','sha256':info['sha256']})
    snaps=[]
    for p in (data/'m91/source_audit').glob('load_snap_counts_*.parquet'):
        meta=json.loads(p.with_suffix('.json').read_text())
        if 2019<=int(meta['season'])<=2025:
            if digest(p)!=meta['sha256']:raise ValueError('Snap cache integrity failure')
            snaps.append(pd.read_parquet(p));hashes.append({'input':str(p.relative_to(data)),'sha256':meta['sha256']})
    hashes.append({'input':'M91A_CLASSIFIED_ERRORS.csv','sha256':digest(source)})
    return frame,pd.concat(schedules,ignore_index=True),pd.concat(snaps,ignore_index=True) if snaps else pd.DataFrame(),audit,hashes


def generate(root,data=None,replicates=2000):
    start=time.perf_counter();root=Path(root);data=Path(data or root/'data');frame,s,snaps,audit,hashes=load_data(root,data)
    frame=frame[frame['sample'].eq('all_base_history')].copy();games=market_groups(frame)
    coaches=coaching_assignments(s);evidence_file=data/'m91b/playoff_evidence.json'
    evidence=json.loads(evidence_file.read_text()) if evidence_file.exists() else []
    if evidence_file.exists():hashes.append({'input':'playoff_evidence.json','sha256':digest(evidence_file)})
    context=pregame_context(s,evidence=evidence);participation=postgame_participation(s,snaps)
    out=root/'reports/m91b';out.mkdir(parents=True,exist_ok=True)
    for name,f in [('market_game_groups',games),('coach_assignments',coaches),('pregame_context',context),('postgame_participation',participation)]:f.to_csv(out/(name+'.csv'),index=False)
    game_context=[]
    for gid,g in coaches.groupby('game_id'):
        values=set(g.coach_group)
        group='first_four_after_observed_change' if 'first_four_after_observed_change' in values else 'remaining_observed_first_season' if 'remaining_observed_first_season' in values else 'established_both_observed' if values=={'established_observed'} else 'unknown'
        c=context[context.game_id.eq(gid)]
        statuses=sorted(c.playoff_status.unique().tolist())
        game_context.append({'game_id':gid,'coach_group':group,'in_season_replacement_proxy':bool(g.in_season_replacement_proxy.any()),
            'playoff_context':'/'.join(statuses) if statuses else 'unknown',
            'prior_observed_qb_change':bool(c.prior_observed_qb_change.eq(True).any()) if len(c) else None})
    f=frame.merge(games,on=['game_id','season','week'],suffixes=('','_game'),validate='many_to_one').merge(pd.DataFrame(game_context),on='game_id',validate='many_to_one')
    f['late_phase']=np.where(f.week.ge(17),'weeks17_18',np.where(f.week.eq(16),'week16','weeks1_15'))
    f['large_disagreement']=np.where(f.market_probability_difference.abs().round(10).ge(.2),'20pp_plus','under20pp')
    summaries={}
    definitions={'market_groups':['market_group'],'market_large_disagreement':['large_disagreement'],
        'market_confidence_adjusted':['large_disagreement','confidence_bucket'],'market_seasons':['season','large_disagreement'],
        'late_phase':['late_phase'],'late_confidence':['late_phase','confidence_bucket'],
        'late_seasons':['season','late_phase'],'coach_groups':['coach_group'],
        'coach_confidence':['coach_group','confidence_bucket'],'coach_seasons':['season','coach_group'],
        'in_season_replacement':['in_season_replacement_proxy'],'prior_qb_change':['coach_group','prior_observed_qb_change']}
    with threadpool_limits(limits=2):
        for name,keys in definitions.items():
            result=summarize(f,['model']+keys,replicates)
            for key,g in f.groupby(['model']+keys,dropna=False,observed=True):
                key=key if isinstance(key,tuple) else (key,);mask=pd.Series(True,index=result.index)
                for col,value in zip(['model']+keys,key):mask&=result[col].isna() if pd.isna(value) else result[col].eq(value)
                result.loc[mask,'market_accuracy']=float(g.market_correct.mean());result.loc[mask,'mean_model_confidence']=float(g.confidence.mean());result.loc[mask,'mean_market_confidence']=float(g.market_confidence.mean())
                for column in ['off_epa','def_epa','recent_off_epa','recent_def_epa']:
                    result.loc[mask,'mean_'+column]=float(g[column].mean())
                result.loc[mask,'mean_recent_minus_season_off_epa']=float((g.recent_off_epa-g.off_epa).mean())
            result.to_csv(out/(name+'.csv'),index=False);summaries[name]=result
        late=f[f.week.ge(16)]
        if len(late):summarize(late,['model','playoff_context','late_phase'],replicates).to_csv(out/'late_playoff_context.csv',index=False)
        if len(participation):
            # Postgame explanatory strata, never used above to define pregame groups.
            post=participation.groupby('game_id').participation_class.agg(lambda v:'observed_drop_50pp_plus' if v.eq('observed_drop_50pp_plus').any() else 'unknown_target_record' if v.eq('target_record_missing').any() else 'no_50pp_drop')
            posterior=f.merge(post.rename('postgame_participation'),on='game_id',validate='many_to_one')
            summarize(posterior,['model','postgame_participation'],replicates).to_csv(out/'postgame_participation_errors.csv',index=False)
    selected=games[games.market_correct_shared_failure];selected.to_csv(out/'market_correct_shared_failures.csv',index=False)
    f[f.game_id.isin(selected.game_id)].to_csv(out/'market_correct_failure_details.csv',index=False)
    cases=[]
    for label,mask in [('models_wrong_market_correct',f.market_correct_shared_failure),('all_predictors_wrong',f.all_predictors_wrong),('high_confidence_late_error',f.week.ge(17)&f.error&f.confidence.ge(.8)),('coaching_transition_error',f.coach_group.eq('first_four_after_observed_change')&f.error)]:
        picked=f[mask].sort_values(['confidence','game_id','model'],ascending=[False,True,True]).drop_duplicates('game_id').head(2).copy();picked['case_group']=label;cases.append(picked)
    cases=pd.concat(cases,ignore_index=True);cases.to_csv(out/'case_studies.csv',index=False)
    # Distribution files distinguish game counts from three model observations.
    for label,subset in [('market_correct_failures',selected),('market_groups',games)]:
        subset.groupby(['season','week']+(['market_group'] if label=='market_groups' else [])).size().rename('games').reset_index().to_csv(out/(label+'_by_week.csv'),index=False)
    cohort_counts=coaches[coaches.game_id.isin(frame.game_id)].groupby(['season','coach_group'],dropna=False).size().rename('team_games').reset_index();cohort_counts.to_csv(out/'coaching_coverage.csv',index=False)
    cols=['model','games','accuracy','expected_error_rate','error_rate','brier','market_brier','market_accuracy','excess_error','excess_error_low','excess_error_high','brier_minus_market','brier_delta_low','brier_delta_high']
    boost=summaries['market_large_disagreement'];boost=boost[boost.model.eq('boosting_oos')&boost.large_disagreement.eq('20pp_plus')]
    findings=[]
    if len(boost):
        r=boost.iloc[0]
        findings.append(f"On {int(r.games)} boosting ≥20pp disagreements, model accuracy is {r.accuracy:.2%} versus closing {r.market_accuracy:.2%}; confidence-adjusted excess error is {r.excess_error:.2%} (week-bootstrap interval {r.excess_error_low:.2%} to {r.excess_error_high:.2%}). Brier-minus-market is {r.brier_minus_market:.4f} ({r.brier_delta_low:.4f} to {r.brier_delta_high:.4f}). This is historical evidence for a prospective disagreement hypothesis, not an executable rule.")
    opposite=games[games.market_group.eq('unanimous_opposite_market')]
    if len(opposite):findings.append(f"All three bases favor the side opposite closing in {len(opposite)} outcome-independent games. Closing picks correctly in {int(opposite.market_correct.sum())}/{len(opposite)}, versus {int((~opposite.market_correct).sum())}/{len(opposite)} for the unanimous models. The {len(selected)} market-correct shared failures are the outcome-selected successful-market portion of this comparison, not a deployable filter.")
    late_summary=summaries['late_phase'];tail=late_summary[late_summary.late_phase.eq('weeks17_18')]
    if len(tail):
        findings.append(f"Weeks 17–18 contain {int(tail.games.iloc[0])} matched games. Model accuracies range {tail.accuracy.min():.2%}–{tail.accuracy.max():.2%}, versus closing {tail.market_accuracy.iloc[0]:.2%}. All confidence-adjusted excess-error intervals include zero: {bool(((tail.excess_error_low<=0)&(tail.excess_error_high>=0)).all())}. No verified playoff/rest labels exist by default, so this does not identify an incentive or rest mechanism.")
    first=summaries['coach_groups'];first=first[first.coach_group.eq('first_four_after_observed_change')]
    if len(first):findings.append(f"The first-four observed coaching-change group contains {int(first.games.iloc[0])} games; all three excess-error intervals contain zero: {bool(((first.excess_error_low<=0)&(first.excess_error_high>=0)).all())}. The data do not establish a coaching-transition prediction penalty; assignment timing, interim status and confounding remain unresolved.")
    profile=frame.drop_duplicates('game_id');profile=profile[profile.game_id.isin(selected.game_id)]
    case_profile=pd.DataFrame([{'outcome_selected_games':len(selected),'mean_base_confidence':float(selected.base_mean_confidence.mean()),'mean_market_confidence':float(selected.market_confidence.mean()),'mean_abs_off_epa_advantage':float(profile.off_epa.abs().mean()),'mean_abs_def_epa_advantage':float(profile.def_epa.abs().mean()),'mean_recent_minus_season_off_epa':float((profile.recent_off_epa-profile.off_epa).mean())}])
    case_profile.to_csv(out/'market_correct_failure_profile.csv',index=False)
    lines=['# M9.1B targeted historical error investigation','',
        '## Executive findings','',
        f"Three-base common sample: {games.game_id.nunique()} games, 2019–2025. All three missed {int(games.all_models_wrong.sum())}; closing picked correctly in {len(selected)} of those. These outcome-selected cases are descriptive, not a selection rule.",'',
        f"Boosting ≥20-point absolute probability disagreements: {int(boost.games.sum())} games. Outcome-independent disagreement comparisons, confidence controls and season breakdowns are below/in the supporting CSVs. The threshold is inherited from M9.1A and was not optimized.",'',
        'Verified historical playoff-clinching and starter-rest evidence is unavailable in the default caches. Chronological standings can be counted, but tiebreakers/clinch status are not inferred from final standings. Coaching names exist in cached schedules; transition labels are retrospective assignment proxies, not verified pregame appointment/interim records. No model, feature, forecast, ledger or policy is changed.','',
        'Measured findings:','']+['- '+v for v in findings]+['',
        '## Data and coverage','',table(pd.DataFrame([{'measure':k,'value':v} for k,v in audit.items()])),'',
        'M9.1A classified CSV is validated against the checksum-verified M7/M8.1 inputs using exact sample/game/model identities, orientation, outcomes and probabilities (CSV-rounding tolerance 5e-10). Only the 1,865-game base sample is used here; repeated narrower-sample rows are excluded. Frozen ensemble results are not expanded beyond their original eligible sample.','',
        '## Track A: outcome-independent market comparisons','']
    for name,keys in [('market_groups',['market_group']),('market_large_disagreement',['large_disagreement'])]:
        lines.extend([table(summaries[name][['model']+keys+[c for c in cols if c!='model']]),''])
    lines.extend(['As in M9.1A, probabilities exactly 50% use a deterministic home pick for accuracy; pick’em is separated from favorite agreement. Groups above use only prediction/market probabilities, not results. Unanimous same-side losses and the 84 market-correct shared failures are separate outcome-defined retrospective case groups. Confidence-adjusted error subtracts each prediction’s expected favorite-loss rate. Each model-market difference uses exactly the same games; the ≥20pp category is model-specific and must not be used for cross-model ranking on unequal subsets. Closing quote timing/book identity is unknown and may postdate the model information cutoff. No wager simulation is performed.','',
        'Outcome-selected case profile (not a predictive/calibration test):','',table(case_profile),'',
        'Outcome-selected 84-case season/week distribution and full confidence/efficiency details: market_correct_failures_by_week.csv and market_correct_failure_details.csv. Outcome-independent season/week counts: market_groups_by_week.csv. Mean confidence, market accuracy, team EPA and recent-minus-season EPA appear in the group CSVs. These are descriptions, not evidence that membership could have been selected from the outcome.','',
        '## Track B: late-season context','',table(summaries['late_phase'][['model','late_phase']+[c for c in cols if c!='model']]),'',
        f"Late-season team-context rows: {len(context[context.week.ge(16)])}; supplied verified playoff statuses: {int(context[context.week.ge(16)].playoff_status.ne('unknown').sum())}; default source records: {len(evidence)}. Chronological context uses only same-season finals with kickoff and conservative result availability strictly before target kickoff (ties count separately). No target result or final-season standing enters those counts.",'',
        'Weeks 16 and 17–18 have within-confidence and season-specific controls in late_confidence.csv/late_seasons.csv; comparisons with weeks 1–15 describe timing, not playoff incentives. Unknown playoff status cannot be interpreted as eliminated, clinched or unresolved. No playoff simulation or tiebreaker engine is built. Optional reviewed evidence must carry a source reference plus publication, capture and local-preservation times strictly before kickoff; conflicting claims remain unknown. Operator claims require independent provenance review.','',
        f"Cached historical snap-count seasons: {sorted(snaps.season.unique().tolist()) if len(snaps) and 'season' in snaps else []}. Covered late-season team comparisons: {len(participation)}; missing target same-player rows remain missing, not zero. Any 50pp decrease compares the preceding eligible game’s leading QB snap share with that same player’s target-game share. It is retrospective participation evidence and cannot establish injury, intent or a pregame rest announcement. No historical verified starter-rest source is available.",'',
        '## Track C: observed coaching transitions','',table(summaries['coach_groups'][['model','coach_group']+[c for c in cols if c!='model']]),'',
        'Schedule home_coach/away_coach fields cover the sampled game assignments; no additional coaching download or dependency is required. Full assignment audit retains team/name, first-through-last observed game rows, null effective appointment dates, unknown interim status and unknown publication time. No current coach is assigned backward. 2018 provides warmup; left-censored/missing sequences remain unknown until observed continuity permits a label. First four games after a detected name change and the remainder of that observed first season are fixed groups. Returning coaches start a new spell. A game is categorized as first-four if either team qualifies, then remaining-first-season, then established-both, else unknown.','',
        'In-season replacement proxies apply only during the season of the observed replacement; later retained-coach seasons are not automatically labeled interim. Names are preserved without fuzzy spelling corrections; a source revision or naming inconsistency may mimic a transition. In-season replacements are separately labeled proxies; they are not called interim coaches without a source. Team-game assignment audit rows overlap within a game; all error comparisons deduplicate at game/model level. Confidence/season controls, prior two completed-game QB changes, and existing efficiency context are descriptive confounder checks. Target-game QB participation never defines a pregame coaching category. No coaching effect is causal or independently verified here.','',
        '## Reproducible illustrative cases','',table(cases[['case_group','season','week','game_id','home_team','away_team','home_score','away_score','model','probability','market_probability','confidence','coach_group','playoff_context']]),'',
        'Each case group takes its two highest-confidence eligible errors (stable game/model tie-break; one row per game within that case group). Cases may overlap and are outcome-selected illustrations. No QB, injury, rest or coaching explanation is asserted without a supporting pregame source.','',
        '## Uncertainty and research suitability','',
        'All summaries reuse M9.1A’s season-week cluster bootstrap (2,000 replicates, seed 42), with confidence-adjusted excess error and same-game Brier-minus-market intervals. Expected error means 1 minus predicted-winner confidence. Small samples are flagged; fewer than two clusters have no interval. Correlated teams, interweek dependence, seven seasons, source revisions, overlapping groups and many comparisons limit inference. Group-average differences are descriptive and not randomized/matched causal effects.','',
        'Market disagreement is a measurable, outcome-independent candidate for prespecified prospective timestamp-aligned testing; closing-line results alone cannot support an executable rule. Late-season raw error rates do not establish starter-rest or playoff-incentive effects because verified context is missing. Coaching proxy contrasts can guide source validation, but appointment/interim publication evidence and confounding controls are insufficient for an adjustment. Negative and inconclusive confidence intervals remain in all CSVs. No correction factor, model tuning, betting strategy or M9.2 work is introduced.','',
        'Recommended next step: retain existing forecasts and collect source-timestamped prospective context alongside M8.3 checkpoints; preregister the market-disagreement contrast before evaluating new outcomes. Do not deploy a historical subgroup rule.','',
        '## Reproduction, runtime and integrity','',
        '`python -m nfl_predictor.cli report-m91b` is offline, reads cached inputs and writes only this report and reports/m91b CSVs. No model inference/training, downloads, personnel collection, odds fetching or ledger writes occur. Missing historical snap/playoff/coach fields are kept unavailable; absent required classified forecasts cause an actionable error. Native Windows testing has not been executed.','',
        f'Measured runtime: {time.perf_counter()-start:.2f} seconds. Input SHA-256:','',table(pd.DataFrame(hashes)),'',
        'Actual automated test and protected-artifact verification results are appended after execution.',''])
    report=root/'M91B_TARGETED_ERROR_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8');return report
