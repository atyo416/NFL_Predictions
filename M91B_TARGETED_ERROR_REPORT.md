# M9.1B targeted historical error investigation

## Executive findings

Three-base common sample: 1865 games, 2019–2025. All three missed 499; closing picked correctly in 84 of those. These outcome-selected cases are descriptive, not a selection rule.

Boosting ≥20-point absolute probability disagreements: 87 games. Outcome-independent disagreement comparisons, confidence controls and season breakdowns are below/in the supporting CSVs. The threshold is inherited from M9.1A and was not optimized.

Verified historical playoff-clinching and starter-rest evidence is unavailable in the default caches. Chronological standings can be counted, but tiebreakers/clinch status are not inferred from final standings. Coaching names exist in cached schedules; transition labels are retrospective assignment proxies, not verified pregame appointment/interim records. No model, feature, forecast, ledger or policy is changed.

Measured findings:

- On 87 boosting ≥20pp disagreements, model accuracy is 41.38% versus closing 79.31%; confidence-adjusted excess error is 19.76% (week-bootstrap interval 8.86% to 29.58%). Brier-minus-market is 0.0992 (0.0534 to 0.1407). This is historical evidence for a prospective disagreement hypothesis, not an executable rule.
- All three bases favor the side opposite closing in 146 outcome-independent games. Closing picks correctly in 84/146, versus 62/146 for the unanimous models. The 84 market-correct shared failures are the outcome-selected successful-market portion of this comparison, not a deployable filter.
- Weeks 17–18 contain 191 matched games. Model accuracies range 63.35%–64.92%, versus closing 71.73%. All confidence-adjusted excess-error intervals include zero: True. No verified playoff/rest labels exist by default, so this does not identify an incentive or rest mechanism.
- The first-four observed coaching-change group contains 220 games; all three excess-error intervals contain zero: True. The data do not establish a coaching-transition prediction penalty; assignment timing, interim status and confounding remain unresolved.

## Data and coverage

| measure | value |
| --- | --- |
| source_classification | historical_closing_reference |
| schedule_games | 1871 |
| base_prediction_games | 1865 |
| unmatched_prediction_ids | 0 |
| incomplete_scores | 0 |
| ties_excluded | 6 |
| missing_closing_pair | 0 |
| invalid_closing_pair | 0 |
| usable_closing_pairs | 1865 |
| underround_pairs | 1 |
| missing_or_invalid_model_probabilities | 0 |
| metadata_conflicts | 0 |
| closing_games_without_base_predictions | 0 |
| base_matched_games | 1865 |
| ensemble_metadata_conflicts | 0 |
| ensemble_matched_games | 543 |
| base_games_without_eligible_ensemble | 1322 |
| missing_or_ambiguous_feature_seasons | [] |
| missing_feature_game_rows | 0 |

M9.1A classified CSV is validated against the checksum-verified M7/M8.1 inputs using exact sample/game/model identities, orientation, outcomes and probabilities (CSV-rounding tolerance 5e-10). Only the 1,865-game base sample is used here; repeated narrower-sample rows are excluded. Frozen ensemble results are not expanded beyond their original eligible sample.

## Track A: outcome-independent market comparisons

| model | market_group | games | accuracy | expected_error_rate | error_rate | brier | market_brier | market_accuracy | excess_error | excess_error_low | excess_error_high | brier_minus_market | brier_delta_low | brier_delta_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | market_pickem | 2 | 0.000000 | 0.433887 | 1.000000 | 0.321995 | 0.250000 | 0.000000 | 0.566113 | 0.527243 | 0.604983 | 0.071995 | 0.027985 | 0.116005 |
| boosting_oos | models_split | 392 | 0.528061 | 0.449120 | 0.471939 | 0.247138 | 0.225978 | 0.617347 | 0.022819 | -0.021963 | 0.068960 | 0.021160 | 0.011976 | 0.029850 |
| boosting_oos | unanimous_opposite_market | 146 | 0.424658 | 0.410311 | 0.575342 | 0.273018 | 0.237228 | 0.575342 | 0.165032 | 0.075272 | 0.251873 | 0.035790 | 0.003462 | 0.065098 |
| boosting_oos | unanimous_same_as_market | 1325 | 0.688302 | 0.318389 | 0.311698 | 0.211691 | 0.202983 | 0.688302 | -0.006691 | -0.031090 | 0.015998 | 0.008709 | 0.005244 | 0.012026 |
| logistic_oos | market_pickem | 2 | 0.000000 | 0.438150 | 1.000000 | 0.315843 | 0.250000 | 0.000000 | 0.561850 | 0.548889 | 0.574810 | 0.065843 | 0.051280 | 0.080406 |
| logistic_oos | models_split | 392 | 0.448980 | 0.440370 | 0.551020 | 0.262177 | 0.225978 | 0.617347 | 0.110650 | 0.068463 | 0.154344 | 0.036199 | 0.023332 | 0.048801 |
| logistic_oos | unanimous_opposite_market | 146 | 0.424658 | 0.414274 | 0.575342 | 0.268514 | 0.237228 | 0.575342 | 0.161068 | 0.074206 | 0.243966 | 0.031286 | -0.001853 | 0.063717 |
| logistic_oos | unanimous_same_as_market | 1325 | 0.688302 | 0.351136 | 0.311698 | 0.214814 | 0.202983 | 0.688302 | -0.039438 | -0.064124 | -0.015977 | 0.011832 | 0.007613 | 0.015914 |
| margin_elo | market_pickem | 2 | 0.000000 | 0.468258 | 1.000000 | 0.282795 | 0.250000 | 0.000000 | 0.531742 | 0.525022 | 0.538462 | 0.032795 | 0.025648 | 0.039942 |
| margin_elo | models_split | 392 | 0.540816 | 0.430478 | 0.459184 | 0.243405 | 0.225978 | 0.617347 | 0.028705 | -0.021650 | 0.079695 | 0.017427 | 0.007834 | 0.026854 |
| margin_elo | unanimous_opposite_market | 146 | 0.424658 | 0.408781 | 0.575342 | 0.275063 | 0.237228 | 0.575342 | 0.166561 | 0.076600 | 0.254834 | 0.037835 | 0.005579 | 0.070685 |
| margin_elo | unanimous_same_as_market | 1325 | 0.688302 | 0.320916 | 0.311698 | 0.212401 | 0.202983 | 0.688302 | -0.009218 | -0.033163 | 0.013516 | 0.009419 | 0.005590 | 0.013174 |

| model | large_disagreement | games | accuracy | expected_error_rate | error_rate | brier | market_brier | market_accuracy | excess_error | excess_error_low | excess_error_high | brier_minus_market | brier_delta_low | brier_delta_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 20pp_plus | 87 | 0.413793 | 0.388631 | 0.586207 | 0.269884 | 0.170638 | 0.793103 | 0.197576 | 0.088619 | 0.295796 | 0.099245 | 0.053394 | 0.140722 |
| boosting_oos | under20pp | 1778 | 0.643982 | 0.351453 | 0.356018 | 0.221819 | 0.212500 | 0.657480 | 0.004565 | -0.016488 | 0.024688 | 0.009319 | 0.006085 | 0.012362 |
| logistic_oos | 20pp_plus | 167 | 0.485030 | 0.398037 | 0.514970 | 0.272183 | 0.170830 | 0.760479 | 0.116933 | 0.035600 | 0.198168 | 0.101353 | 0.058578 | 0.140400 |
| logistic_oos | under20pp | 1698 | 0.629564 | 0.372655 | 0.370436 | 0.224842 | 0.214453 | 0.654299 | -0.002220 | -0.023676 | 0.018736 | 0.010389 | 0.006456 | 0.014061 |
| margin_elo | 20pp_plus | 97 | 0.463918 | 0.364433 | 0.536082 | 0.292982 | 0.215684 | 0.628866 | 0.171650 | 0.062505 | 0.268354 | 0.077299 | 0.028332 | 0.120198 |
| margin_elo | under20pp | 1768 | 0.645362 | 0.350243 | 0.354638 | 0.220109 | 0.210265 | 0.665724 | 0.004395 | -0.015686 | 0.024679 | 0.009843 | 0.005876 | 0.013533 |

As in M9.1A, probabilities exactly 50% use a deterministic home pick for accuracy; pick’em is separated from favorite agreement. Groups above use only prediction/market probabilities, not results. Unanimous same-side losses and the 84 market-correct shared failures are separate outcome-defined retrospective case groups. Confidence-adjusted error subtracts each prediction’s expected favorite-loss rate. Each model-market difference uses exactly the same games; the ≥20pp category is model-specific and must not be used for cross-model ranking on unequal subsets. Closing quote timing/book identity is unknown and may postdate the model information cutoff. No wager simulation is performed.

Outcome-selected case profile (not a predictive/calibration test):

| outcome_selected_games | mean_base_confidence | mean_market_confidence | mean_abs_off_epa_advantage | mean_abs_def_epa_advantage | mean_recent_minus_season_off_epa |
| --- | --- | --- | --- | --- | --- |
| 84 | 0.585723 | 0.588594 | 0.052610 | 0.052956 | -0.011342 |

Outcome-selected 84-case season/week distribution and full confidence/efficiency details: market_correct_failures_by_week.csv and market_correct_failure_details.csv. Outcome-independent season/week counts: market_groups_by_week.csv. Mean confidence, market accuracy, team EPA and recent-minus-season EPA appear in the group CSVs. These are descriptions, not evidence that membership could have been selected from the outcome.

## Track B: late-season context

| model | late_phase | games | accuracy | expected_error_rate | error_rate | brier | market_brier | market_accuracy | excess_error | excess_error_low | excess_error_high | brier_minus_market | brier_delta_low | brier_delta_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | week16 | 112 | 0.616071 | 0.357432 | 0.383929 | 0.226836 | 0.213977 | 0.660714 | 0.026497 | -0.020064 | 0.075793 | 0.012859 | -0.000694 | 0.027632 |
| boosting_oos | weeks17_18 | 191 | 0.633508 | 0.332546 | 0.366492 | 0.224769 | 0.186992 | 0.717277 | 0.033947 | -0.033247 | 0.097891 | 0.037776 | 0.028003 | 0.048629 |
| boosting_oos | weeks1_15 | 1562 | 0.634443 | 0.355407 | 0.365557 | 0.223775 | 0.213182 | 0.657490 | 0.010150 | -0.013211 | 0.033926 | 0.010594 | 0.006592 | 0.014286 |
| logistic_oos | week16 | 112 | 0.642857 | 0.383936 | 0.357143 | 0.223410 | 0.213977 | 0.660714 | -0.026793 | -0.100291 | 0.057859 | 0.009433 | -0.001699 | 0.024152 |
| logistic_oos | weeks17_18 | 191 | 0.638743 | 0.356094 | 0.361257 | 0.230344 | 0.186992 | 0.717277 | 0.005163 | -0.087011 | 0.097543 | 0.043352 | 0.029327 | 0.057976 |
| logistic_oos | weeks1_15 | 1562 | 0.612036 | 0.376585 | 0.387964 | 0.229334 | 0.213182 | 0.657490 | 0.011379 | -0.008824 | 0.032479 | 0.016152 | 0.010618 | 0.021403 |
| margin_elo | week16 | 112 | 0.651786 | 0.344847 | 0.348214 | 0.226094 | 0.213977 | 0.660714 | 0.003367 | -0.041729 | 0.062917 | 0.012117 | 0.000788 | 0.025594 |
| margin_elo | weeks17_18 | 191 | 0.649215 | 0.316737 | 0.350785 | 0.226687 | 0.186992 | 0.717277 | 0.034048 | -0.034771 | 0.110290 | 0.039694 | 0.025876 | 0.056023 |
| margin_elo | weeks1_15 | 1562 | 0.633163 | 0.355608 | 0.366837 | 0.223401 | 0.213182 | 0.657490 | 0.011229 | -0.008967 | 0.032435 | 0.010219 | 0.006143 | 0.013959 |

Late-season team-context rows: 606; supplied verified playoff statuses: 0; default source records: 0. Chronological context uses only same-season finals with kickoff and conservative result availability strictly before target kickoff (ties count separately). No target result or final-season standing enters those counts.

Weeks 16 and 17–18 have within-confidence and season-specific controls in late_confidence.csv/late_seasons.csv; comparisons with weeks 1–15 describe timing, not playoff incentives. Unknown playoff status cannot be interpreted as eliminated, clinched or unresolved. No playoff simulation or tiebreaker engine is built. Optional reviewed evidence must carry a source reference plus publication, capture and local-preservation times strictly before kickoff; conflicting claims remain unknown. Operator claims require independent provenance review.

Cached historical snap-count seasons: [2019]. Covered late-season team comparisons: 63; missing target same-player rows remain missing, not zero. Any 50pp decrease compares the preceding eligible game’s leading QB snap share with that same player’s target-game share. It is retrospective participation evidence and cannot establish injury, intent or a pregame rest announcement. No historical verified starter-rest source is available.

## Track C: observed coaching transitions

| model | coach_group | games | accuracy | expected_error_rate | error_rate | brier | market_brier | market_accuracy | excess_error | excess_error_low | excess_error_high | brier_minus_market | brier_delta_low | brier_delta_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | established_both_observed | 1072 | 0.628731 | 0.358388 | 0.371269 | 0.226076 | 0.213489 | 0.653918 | 0.012881 | -0.016304 | 0.041670 | 0.012588 | 0.008205 | 0.016930 |
| boosting_oos | first_four_after_observed_change | 220 | 0.650000 | 0.352747 | 0.350000 | 0.223297 | 0.204633 | 0.668182 | -0.002747 | -0.060055 | 0.053236 | 0.018664 | 0.006669 | 0.030394 |
| boosting_oos | remaining_observed_first_season | 573 | 0.635253 | 0.343627 | 0.364747 | 0.220583 | 0.207315 | 0.680628 | 0.021120 | -0.010580 | 0.055628 | 0.013269 | 0.005866 | 0.020521 |
| logistic_oos | established_both_observed | 1072 | 0.617537 | 0.377151 | 0.382463 | 0.229992 | 0.213489 | 0.653918 | 0.005312 | -0.024913 | 0.034218 | 0.016503 | 0.010127 | 0.022737 |
| logistic_oos | first_four_after_observed_change | 220 | 0.636364 | 0.376721 | 0.363636 | 0.229962 | 0.204633 | 0.668182 | -0.013084 | -0.075615 | 0.048950 | 0.025329 | 0.011490 | 0.039566 |
| logistic_oos | remaining_observed_first_season | 573 | 0.607330 | 0.370081 | 0.392670 | 0.227041 | 0.207315 | 0.680628 | 0.022589 | -0.010892 | 0.056800 | 0.019726 | 0.010874 | 0.029213 |
| margin_elo | established_both_observed | 1072 | 0.634328 | 0.358650 | 0.365672 | 0.225270 | 0.213489 | 0.653918 | 0.007022 | -0.021376 | 0.036778 | 0.011781 | 0.006713 | 0.016903 |
| margin_elo | first_four_after_observed_change | 220 | 0.650000 | 0.348989 | 0.350000 | 0.214891 | 0.204633 | 0.668182 | 0.001011 | -0.050968 | 0.051293 | 0.010258 | -0.001198 | 0.022189 |
| margin_elo | remaining_observed_first_season | 573 | 0.633508 | 0.337399 | 0.366492 | 0.224792 | 0.207315 | 0.680628 | 0.029093 | -0.003830 | 0.063632 | 0.017477 | 0.009566 | 0.025171 |

Schedule home_coach/away_coach fields cover the sampled game assignments; no additional coaching download or dependency is required. Full assignment audit retains team/name, first-through-last observed game rows, null effective appointment dates, unknown interim status and unknown publication time. No current coach is assigned backward. 2018 provides warmup; left-censored/missing sequences remain unknown until observed continuity permits a label. First four games after a detected name change and the remainder of that observed first season are fixed groups. Returning coaches start a new spell. A game is categorized as first-four if either team qualifies, then remaining-first-season, then established-both, else unknown.

In-season replacement proxies apply only during the season of the observed replacement; later retained-coach seasons are not automatically labeled interim. Names are preserved without fuzzy spelling corrections; a source revision or naming inconsistency may mimic a transition. In-season replacements are separately labeled proxies; they are not called interim coaches without a source. Team-game assignment audit rows overlap within a game; all error comparisons deduplicate at game/model level. Confidence/season controls, prior two completed-game QB changes, and existing efficiency context are descriptive confounder checks. Target-game QB participation never defines a pregame coaching category. No coaching effect is causal or independently verified here.

## Reproducible illustrative cases

| case_group | season | week | game_id | home_team | away_team | home_score | away_score | model | probability | market_probability | confidence | coach_group | playoff_context |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| models_wrong_market_correct | 2020 | 17 | 2020_17_LAC_KC | KC | LAC | 21 | 38 | margin_elo | 0.896015 | 0.282528 | 0.896015 | established_both_observed | unknown |
| models_wrong_market_correct | 2023 | 18 | 2023_18_PIT_BAL | BAL | PIT | 10 | 17 | boosting_oos | 0.821261 | 0.417007 | 0.821261 | established_both_observed | unknown |
| all_predictors_wrong | 2020 | 15 | 2020_15_NYJ_LA | LA | NYJ | 20 | 23 | margin_elo | 0.910995 | 0.908664 | 0.910995 | established_both_observed | unknown |
| all_predictors_wrong | 2019 | 10 | 2019_10_ATL_NO | NO | ATL | 9 | 26 | boosting_oos | 0.902509 | 0.839356 | 0.902509 | established_both_observed | unknown |
| high_confidence_late_error | 2020 | 17 | 2020_17_LAC_KC | KC | LAC | 21 | 38 | margin_elo | 0.896015 | 0.282528 | 0.896015 | established_both_observed | unknown |
| high_confidence_late_error | 2024 | 18 | 2024_18_BUF_NE | NE | BUF | 23 | 16 | margin_elo | 0.108922 | 0.400361 | 0.891078 | remaining_observed_first_season | unknown |
| coaching_transition_error | 2019 | 4 | 2019_04_CLE_BAL | BAL | CLE | 25 | 40 | boosting_oos | 0.890521 | 0.743748 | 0.890521 | first_four_after_observed_change | unknown |
| coaching_transition_error | 2021 | 18 | 2021_18_IND_JAX | JAX | IND | 26 | 11 | margin_elo | 0.122434 | 0.127907 | 0.877566 | first_four_after_observed_change | unknown |

Each case group takes its two highest-confidence eligible errors (stable game/model tie-break; one row per game within that case group). Cases may overlap and are outcome-selected illustrations. No QB, injury, rest or coaching explanation is asserted without a supporting pregame source.

## Uncertainty and research suitability

All summaries reuse M9.1A’s season-week cluster bootstrap (2,000 replicates, seed 42), with confidence-adjusted excess error and same-game Brier-minus-market intervals. Expected error means 1 minus predicted-winner confidence. Small samples are flagged; fewer than two clusters have no interval. Correlated teams, interweek dependence, seven seasons, source revisions, overlapping groups and many comparisons limit inference. Group-average differences are descriptive and not randomized/matched causal effects.

Market disagreement is a measurable, outcome-independent candidate for prespecified prospective timestamp-aligned testing; closing-line results alone cannot support an executable rule. Late-season raw error rates do not establish starter-rest or playoff-incentive effects because verified context is missing. Coaching proxy contrasts can guide source validation, but appointment/interim publication evidence and confounding controls are insufficient for an adjustment. Negative and inconclusive confidence intervals remain in all CSVs. No correction factor, model tuning, betting strategy or M9.2 work is introduced.

Recommended next step: retain existing forecasts and collect source-timestamped prospective context alongside M8.3 checkpoints; preregister the market-disagreement contrast before evaluating new outcomes. Do not deploy a historical subgroup rule.

## Reproduction, runtime and integrity

`python -m nfl_predictor.cli report-m91b` is offline, reads cached inputs and writes only this report and reports/m91b CSVs. No model inference/training, downloads, personnel collection, odds fetching or ledger writes occur. Missing historical snap/playoff/coach fields are kept unavailable; absent required classified forecasts cause an actionable error. Native Windows testing has not been executed.

Measured runtime: 28.44 seconds. Input SHA-256:

| input | sha256 |
| --- | --- |
| schedules/2019 | 490ae0ba90099fc099ab6177b573d177f45c4c26c4a38c78e747184f89c70ab2 |
| pregame_features/2019 | fa77d3fb45fe420c2f5d29ca2e8409f23ea84ccc3f206c035b94b639ae738216 |
| schedules/2020 | a585db1c876ba699c9e02f07ed22a2dda37526b25b6924e1b6ae94a6e02b3400 |
| pregame_features/2020 | de8ef8bfe1fb76eed3aa33ba8003edb6eb2b54da1dc85d44dc1f085aaa5ff8da |
| schedules/2021 | 8273e3b50d26a010b83927dc1273f6eb2f8e13031065428770d92bfcfc41149f |
| pregame_features/2021 | 7803cb8abe685f8470642ca75eafc4948fa0245665e09ad4c561da84fb8a6626 |
| schedules/2022 | 1e80b33dae054fb5e35e958d58ce62084e0232efd40a1e2082fed618a62a1404 |
| pregame_features/2022 | 64e2954b50f71270c936f00902b513e998e6dd9025826f16dabc5d1f039e78ec |
| schedules/2023 | 16432451e901643d9521d703c377c93202e3ba3bb369bc4265bb6fbeed38812f |
| pregame_features/2023 | 36dff27597c0bd9e59cef9d61f089605bbf253ab2c0a428b23106096957a84b8 |
| schedules/2024 | 3c9b4ac76f93e7b62673ddf220df9e3574fdf02694d18ab7f7f121f15a202a5a |
| pregame_features/2024 | e785bc448e69f27fc6fe4567e1beecc716d118c84b3f091fb5efbd0c5a7e8e89 |
| schedules/2025 | da34c7753becfa89be45efa321a1e27c5ba5065eb332680b01f224e9ca5ad83f |
| pregame_features/2025 | cdf643769d1c67a1b68861772e81ba7b6468da159de88f5440b299794f7d19a9 |
| base_predictions.parquet | a3ca327bda1879b35e71d45993602884e7ce05f3fedb0ab47ae1f20cefe4f0ae |
| predictions.parquet | c8c8cd8e4fda45df1832052dd97cac2f8551d0d5cc026074d27c920ff680e743 |
| selection.json | b37d2128803cc9f1aaf75545290c4c456ae1dad4ec883811c411b7fc4b8310ac |
| metadata.json | 9c1f7c48b6daa451244219177ceb0780a044cf402d1d87088bf2caeedce6fac3 |
| coaching_context_schedules/2018 | bcafaca2735238133cadb2613da0649dab1079635ef95a11033ab47aace28c4d |
| coaching_context_schedules/2019 | 490ae0ba90099fc099ab6177b573d177f45c4c26c4a38c78e747184f89c70ab2 |
| coaching_context_schedules/2020 | a585db1c876ba699c9e02f07ed22a2dda37526b25b6924e1b6ae94a6e02b3400 |
| coaching_context_schedules/2021 | 8273e3b50d26a010b83927dc1273f6eb2f8e13031065428770d92bfcfc41149f |
| coaching_context_schedules/2022 | 1e80b33dae054fb5e35e958d58ce62084e0232efd40a1e2082fed618a62a1404 |
| coaching_context_schedules/2023 | 16432451e901643d9521d703c377c93202e3ba3bb369bc4265bb6fbeed38812f |
| coaching_context_schedules/2024 | 3c9b4ac76f93e7b62673ddf220df9e3574fdf02694d18ab7f7f121f15a202a5a |
| coaching_context_schedules/2025 | da34c7753becfa89be45efa321a1e27c5ba5065eb332680b01f224e9ca5ad83f |
| m91/source_audit/load_snap_counts_2019.parquet | f7b2b073625d50d5f97d7a639a15d4577168967696940c3df757d03ffd479fbd |
| M91A_CLASSIFIED_ERRORS.csv | 40074ad6e0065b838256114c33db327fbaef742cd28a3bb5a3fa5cbbcd11af22 |

Actual automated test and protected-artifact verification results are appended after execution.

## Execution verification and preservation

Baseline: `57836202f2cb3ec1df385ec427ab455e06cb6937`, clean M9.1A tree. Actual starting collection confirmed **216 tests**. Relevant M9.1A/M8.3 baseline: **18 passed in 2.95s**. New focused tests: **9 passed in 2.07s**, no warnings. They cover outcome-independent grouping, shared failures, orientation, strict chronological result availability, missing/verified/conflicting playoff claims, observed coaching changes, missing coach fields, in-season flags and subsequent retained-coach seasons, retrospective snaps, unavailable sources and old-artifact preservation.

Real offline execution succeeded in **28.44 seconds**, including source validation, chronological context and all diagnostic tables. Coach names are present on **4254/4254** observed team/game assignment rows across 2018–2025; all effective appointment/interim publication evidence remains unavailable. The evaluated binary sample uses 3,730 team/game assignment rows on 1,865 distinct games.

Cached 2019 participation supplied **63** late-season team comparisons: **3** observed ≥50pp same-QB decreases, **55** smaller/no decreases, and **5** missing target same-player records. These counts describe postgame participation only; none establishes pregame knowledge or intentional rest. Source context tables retain tie games where relevant to standings; binary model comparisons exclude ties.

Pre/post SHA-256 checks currently confirm **2767 protected existing files unchanged**, including models, M7 predictions and forecasts, M8 odds/wagers, historical benchmarks, M8.3 records, M9.1 personnel snapshots and every M9.1A report/CSV. Manifest SHA-256: `d79393e6a74ce8c2b112632678087a4b9793ae6c691af6894b14710d9a683247`. No network data requests were made for this diagnostic; existing schedule coaches and cached snap counts were sufficient for the explicitly limited audits.

Native Windows execution remains unverified. With existing caches, local Windows/Python 3.12 checks are `python -m pytest -q tests/test_m91b.py` and `python -m nfl_predictor.cli report-m91b`. Source publication/appointment gaps and missing playoff/rest evidence remain unresolved, rather than being replaced with final standings or inferred coaching intent.


Full regression suite ran once after focused verification: **225 passed, 8 warnings in 169.75s (0:02:49)**. The eight existing warnings concern Streamlit/pandas deprecations and the synthetic play-count coverage fixture. Final SHA-256 verification again found **zero changes across all 2,767 protected files**. `git diff --check` passed.

M9.1B delivered: all 84 outcome-selected market-correct failures investigated; independent probability-defined groups evaluated; late-season/confidence/season controls reported; historical playoff/rest status kept unknown where unsupported; schedule coach assignments and transition proxies audited with source/timing limitations; retrospective QB participation isolated; reproducible cases and 25 supporting CSVs produced; focused and full suites passed. No new model, correction factor, forecast, ledger entry, wager or M9.2 development occurred.
