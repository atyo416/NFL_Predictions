# M5 engineering report

## Scope, baseline and authorization

M5 adds 1999–2017 source ingestion, season audits, compact historical pregame caches, staged window selection and exponential sample weighting for the existing logistic and fixed shallow HGB estimators. Development proceeded at risk while native Windows M4 acceptance remains pending. The actual starting suite passed 74 tests on Linux/Python 3.12. The champion, existing registry, forecasts, Elo histories and reports are preserved; see docs/m5/BASELINE.json and verification evidence below. No M5 candidate was activated. M6 was not started.

## Source coverage and completeness

| season | schedule_games | expected_regular_games | completed_games | ties | pbp_rows | source_metric_coverage | clock_known_fraction | venue_known_fraction | completeness | retrieved_at | disk_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1999 | 248 | 248 | 248 | 0 | 46136 | 0.995968 | 0.000000 | 1.000000 | review_required | 2026-11-03T05:55:09.127636+00:00 | 13557726 |
| 2000 | 248 | 248 | 248 | 0 | 45491 | 0.991935 | 1.000000 | 1.000000 | review_required | 2026-11-03T05:59:08.924631+00:00 | 13587827 |
| 2001 | 248 | 248 | 248 | 0 | 44969 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:10.710778+00:00 | 14181092 |
| 2002 | 256 | 256 | 256 | 1 | 47355 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:12.786844+00:00 | 14918270 |
| 2003 | 256 | 256 | 256 | 0 | 46811 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:14.823193+00:00 | 14819483 |
| 2004 | 256 | 256 | 256 | 0 | 46705 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:16.813149+00:00 | 14744972 |
| 2005 | 256 | 256 | 256 | 0 | 46823 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:18.658222+00:00 | 14808125 |
| 2006 | 256 | 256 | 256 | 0 | 46299 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:20.610555+00:00 | 18713119 |
| 2007 | 256 | 256 | 256 | 0 | 46266 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:22.482436+00:00 | 18903614 |
| 2008 | 256 | 256 | 256 | 1 | 45917 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:55:10.321840+00:00 | 18719798 |
| 2009 | 256 | 256 | 256 | 0 | 46519 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:25.484309+00:00 | 19075323 |
| 2010 | 256 | 256 | 256 | 0 | 46892 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:27.449500+00:00 | 19256313 |
| 2011 | 256 | 256 | 256 | 0 | 47448 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:29.439462+00:00 | 19295257 |
| 2012 | 256 | 256 | 256 | 1 | 47834 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:31.479467+00:00 | 19496075 |
| 2013 | 256 | 256 | 256 | 1 | 48158 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:55:11.642632+00:00 | 19686127 |
| 2014 | 256 | 256 | 256 | 1 | 47629 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:34.342432+00:00 | 19519265 |
| 2015 | 256 | 256 | 256 | 0 | 48122 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:36.202262+00:00 | 19715669 |
| 2016 | 256 | 256 | 256 | 2 | 47651 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:59:38.277294+00:00 | 19528372 |
| 2017 | 256 | 256 | 256 | 0 | 47245 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T05:55:13.127404+00:00 | 19247638 |
| 2018 | 256 | 256 | 256 | 2 | 47109 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:34:57.304748+00:00 | 19218866 |
| 2019 | 256 | 256 | 256 | 1 | 47260 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:34:59.065779+00:00 | 19316369 |
| 2020 | 256 | 256 | 256 | 1 | 47705 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:35:00.721465+00:00 | 19458233 |
| 2021 | 272 | 272 | 272 | 1 | 49922 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:35:02.348737+00:00 | 20427590 |
| 2022 | 271 | 272 | 271 | 2 | 49434 | 1.000000 | 1.000000 | 1.000000 | known_canceled_game_exception | 2026-11-03T04:35:04.263541+00:00 | 20609308 |
| 2023 | 272 | 272 | 272 | 0 | 49665 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:35:05.990159+00:00 | 20710550 |
| 2024 | 272 | 272 | 272 | 0 | 49492 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:35:07.731837+00:00 | 20775834 |
| 2025 | 272 | 272 | 272 | 1 | 48771 | 1.000000 | 1.000000 | 1.000000 | complete_source_metrics | 2026-11-03T04:34:39.067514+00:00 | 20514308 |
| 2026 | 272 | 272 | 121 | 1 | 21018 | 0.991736 | 1.000000 | 1.000000 | review_required | 2026-11-03T04:35:08.725216+00:00 | 9115437 |

Historical ingestion is season-by-season, resumable and manifest-atomic. Required columns, data types, null rates, game/PBP counts, retrieval time, source hashes, processing version, incomplete games and metric distributions are recorded in source_audit.json and each new season manifest. Earlier raw seasons are not retained together in process memory. Unchanged verified caches are reused; failed downloads cannot publish a half season. Each raw file is independently checked on reads.

1999 has no kickoff clock in schedules, start_time or time_of_day. It uses a clearly labeled local-day LOWER BOUND for feature cutoff, with result eligibility no earlier than next day 08:00 Eastern (latest possible local-day kickoff plus eight hours). This is conservative date-interval processing, not a reconstructed actual kickoff. Other inspected seasons supply scheduled clocks. Prior-game rest is not identifiable for date-only data, so **rest is excluded from every common-feature window**. Neutral status is missing if source venue is unknown. No missing football statistics are fabricated.

Source metric completeness is distinct from complete pregame inputs. Missing play-by-play games in 1999/2000 and initialization-season priors remain explicit; training-only imputation or native partial-missing handling is permitted and reported, not disguised as source coverage. Modern 2026 is incomplete/ongoing and is not scored as a prospective experiment.

| season | binary_games | full_m2_features_complete | common_features_complete | clock_known_fraction |
| --- | --- | --- | --- | --- |
| 1999 | 248 | 0.000000 | 0.927419 | 0.000000 |
| 2000 | 248 | 1.000000 | 1.000000 | 1.000000 |
| 2001 | 248 | 1.000000 | 1.000000 | 1.000000 |
| 2002 | 255 | 0.996078 | 1.000000 | 1.000000 |
| 2003 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2004 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2005 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2006 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2007 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2008 | 255 | 1.000000 | 1.000000 | 1.000000 |
| 2009 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2010 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2011 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2012 | 255 | 1.000000 | 1.000000 | 1.000000 |
| 2013 | 255 | 1.000000 | 1.000000 | 1.000000 |
| 2014 | 255 | 1.000000 | 1.000000 | 1.000000 |
| 2015 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2016 | 254 | 1.000000 | 1.000000 | 1.000000 |
| 2017 | 256 | 1.000000 | 1.000000 | 1.000000 |
| 2018 | 254 | 1.000000 | 1.000000 | 1.000000 |
| 2019 | 255 | 1.000000 | 1.000000 | 1.000000 |
| 2020 | 255 | 1.000000 | 1.000000 | 1.000000 |
| 2021 | 271 | 1.000000 | 1.000000 | 1.000000 |
| 2022 | 269 | 1.000000 | 1.000000 | 1.000000 |
| 2023 | 272 | 1.000000 | 1.000000 | 1.000000 |
| 2024 | 272 | 1.000000 | 1.000000 | 1.000000 |
| 2025 | 271 | 1.000000 | 1.000000 | 1.000000 |
| 2026 | 120 | 1.000000 | 1.000000 | 1.000000 |

## Statistical compatibility and era effects

The same eligible scrimmage policy is used across eras: run/pass including sacks, excluding kneels/spikes/administrative/special teams and missing EPA. Offensive/defensive EPA and success are from the possession/opposing-team perspective; game means receive equal weights. Success is EPA>0. Turnovers are interceptions plus lost fumbles on eligible plays. Passing production is net eligible pass-play yards (including sacks), not official gross passing yards; rushing production uses eligible run-play yards. Descriptive production fields are audited, not added to model feature sets.

Actual historical schemas include the required EPA, yardage, turnover and kneel/spike fields. Matching column definitions does not establish identical statistical distributions or source-model calibration. Per-season means, medians, standard deviations and null rates are exported. Modern historical EPA may itself use a retrospectively estimated expected-points model; rolling feature cutoffs do not reconstruct its original publication/model vintage.

Relevant era changes include passing/contact/protection enforcement, evolving offensive strategy, kickoff placement/touchback and dynamic-kickoff changes, overtime formats and the 17-game transition in 2021. Houston expansion and Seattle division realignment also change league structure. No rule-era or division indicators were automatically added. Distribution drift is descriptive, not a causal rule-change estimate. Abbreviations OAK→LV, SD→LAC, STL/LAR→LA and other existing aliases preserve franchise identity. Houston has no pre-2002 team prior and falls back to the prior-season league mean. The 2001 postponements are ordered by actual recorded dates, not nominal week alone.

## Feature reconstruction and original references

All common-feature window policies use identical 1999-onward pregame state. W1 means earliest training label season, not resetting priors/Elo to 2018. Original full-feature M2/M4 references are separate and use only the original modern source history.

Each compact season cache uses the current and previous season (all needed statistical priors), strict earlier-result availability and four-game prior shrinkage. Source/code hashes invalidate only affected caches; longer Elo is replayed over the compact schedule sequence separately. The four-game prior and 50% offseason league regression remain fixed, not tuned against 2024–2025. season_phase.csv reports weeks 1–3 versus later results to review early-prior behavior without selecting a new prior on these outcomes; four games is not claimed optimal across eras. Initialization lacks 1998 data and is explicitly labeled; early-season missing values are not replaced by future source values.

Original M2 logistic and M4 shallow-HGB references are reconstructed from the unchanged 2018–2026 cache through their original endpoints, preserving mature-history differences as a separate reference. Main window comparisons use the same common features and 1999-onward prior/Elo history for ALL window policies. Therefore W1-common may differ from the exact original full-feature benchmark; within_algorithm.csv is the fair window-effect reference. Rest removal and richer initialization must not be misattributed to extra training labels.

## Staged window and recency selection

W1=2018, W2=2013, W3=2008, W4=1999 are earliest eligible label-season policies. Development folds validate 2019/2020/2021 after training endpoints 2018/2019/2020. Uniform windows are ranked per algorithm by equal-season mean Brier then log loss. The top two windows per algorithm receive predefined 3/5/8-year decay; one primary policy is selected using those same development years. Later-year comparisons never feed back into selection. Shallow HGB parameters stay fixed at the M4-selected values; there is no tree/feature/prior retuning.

| algorithm | window | brier | log_loss |
| --- | --- | --- | --- |
| hgb | W3 | 0.224189 | 0.639990 |
| hgb | W4 | 0.224899 | 0.640953 |
| hgb | W2 | 0.226324 | 0.645778 |
| hgb | W1 | 0.232017 | 0.658572 |
| logistic | W3 | 0.224593 | 0.640373 |
| logistic | W4 | 0.225116 | 0.641238 |
| logistic | W2 | 0.226167 | 0.644582 |
| logistic | W1 | 0.230397 | 0.655211 |

| algorithm | window | half_life | brier | log_loss |
| --- | --- | --- | --- | --- |
| hgb | W3 | 0 | 0.224189 | 0.639990 |
| hgb | W3 | 8 | 0.224689 | 0.641375 |
| hgb | W4 | 0 | 0.224899 | 0.640953 |
| hgb | W3 | 5 | 0.225488 | 0.642896 |
| hgb | W4 | 5 | 0.225711 | 0.643188 |
| hgb | W4 | 3 | 0.225724 | 0.643355 |
| hgb | W4 | 8 | 0.225971 | 0.643467 |
| hgb | W3 | 3 | 0.226382 | 0.645075 |
| logistic | W3 | 0 | 0.224593 | 0.640373 |
| logistic | W4 | 5 | 0.224643 | 0.640701 |
| logistic | W4 | 8 | 0.224665 | 0.640549 |
| logistic | W3 | 8 | 0.224689 | 0.640834 |
| logistic | W3 | 5 | 0.224762 | 0.641151 |
| logistic | W4 | 3 | 0.224827 | 0.641465 |
| logistic | W3 | 3 | 0.224936 | 0.641804 |
| logistic | W4 | 0 | 0.225116 | 0.641238 |

Selected experimental policies: `{"logistic": {"window": "W3", "half_life": 0.0}, "hgb": {"window": "W3", "half_life": 0.0}}`. Configuration counts: `{"development_fits": 60, "forward_uncalibrated_policies": 80, "registered_fold_models": 96}`.

Weights are 0.5**(age_years/half_life), age at each specific historical fit cutoff, never today. One year=365.25 days; weights normalize to mean one, preserving total likelihood scale relative to fixed L2. Effective sample size is (sum w)^2/sum(w^2). No records are duplicated. Logistic uses training-only unweighted mean imputation, weighted StandardScaler and weighted logistic loss; HGB receives sample_weight directly. All-empty training columns retain the M4 exclusions/fallback.

## Measured probability-quality comparison, examined 2024–2025

| model | accuracy | brier | log_loss |
| --- | --- | --- | --- |
| elo_extended | 0.639042 | 0.224453 | 0.639687 |
| elo_original | 0.639042 | 0.224492 | 0.639773 |
| hgb_W1_uniform | 0.648250 | 0.219158 | 0.628583 |
| hgb_W2_uniform | 0.651934 | 0.216486 | 0.622496 |
| hgb_W3_uniform | 0.664825 | 0.214954 | 0.618001 |
| hgb_W4_uniform | 0.662983 | 0.216392 | 0.620886 |
| logistic | 0.644567 | 0.220954 | 0.631279 |
| logistic_W1_uniform | 0.657459 | 0.218871 | 0.627051 |
| logistic_W2_uniform | 0.642726 | 0.218664 | 0.625938 |
| logistic_W3_uniform | 0.644567 | 0.219166 | 0.626949 |
| logistic_W4_uniform | 0.651934 | 0.219417 | 0.627308 |
| margin_elo_extended | 0.651934 | 0.219131 | 0.627868 |
| margin_elo_original | 0.651934 | 0.219134 | 0.627875 |
| original_hgb | 0.661142 | 0.217426 | 0.624715 |
| pregame_win_percentage | 0.657459 | 0.222769 | 0.637090 |

| model | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- |
| elo_extended | 0.224453 | 0.003499 | -0.004344 | 0.011930 | 543 |
| elo_original | 0.224492 | 0.003538 | -0.004322 | 0.011979 | 543 |
| hgb_W1_uniform | 0.219158 | -0.001796 | -0.008091 | 0.004740 | 543 |
| hgb_W2_uniform | 0.216486 | -0.004468 | -0.010973 | 0.002132 | 543 |
| hgb_W3_uniform | 0.214954 | -0.006000 | -0.011661 | -0.000335 | 543 |
| hgb_W4_uniform | 0.216392 | -0.004562 | -0.010243 | 0.001302 | 543 |
| logistic | 0.220954 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W1_uniform | 0.218871 | -0.002083 | -0.004483 | 0.000475 | 543 |
| logistic_W2_uniform | 0.218664 | -0.002289 | -0.006296 | 0.001915 | 543 |
| logistic_W3_uniform | 0.219166 | -0.001787 | -0.005189 | 0.001841 | 543 |
| logistic_W4_uniform | 0.219417 | -0.001537 | -0.005106 | 0.002357 | 543 |
| margin_elo_extended | 0.219131 | -0.001823 | -0.009639 | 0.006041 | 543 |
| margin_elo_original | 0.219134 | -0.001819 | -0.009637 | 0.006045 | 543 |
| original_hgb | 0.217426 | -0.003528 | -0.009152 | 0.002531 | 543 |
| pregame_win_percentage | 0.222769 | 0.001815 | -0.007872 | 0.010635 | 543 |

Differences above reference the exact original logistic. Complete accuracy, Brier, log loss and sample sizes appear in MODEL_COMPARISON.md and comparison.csv. within_algorithm.csv directly isolates each common-feature window against same-algorithm W1, while decay_effects.csv isolates each half-life against its same-window uniform model. Read all references carefully; feature-history/feature-set differences from the original benchmark are separate from training-window effects.

## Direct window effects and four experiment questions

Logistic: W1-common Brier 0.218871; best observed uniform window logistic_W2_uniform at 0.218664; maximum-history W4 0.219417. The observed-best window is descriptive, not a new choice using evaluation outcomes.

Shallow boosting: W1-common Brier 0.219158; best observed uniform window hgb_W3_uniform at 0.214954; maximum-history W4 0.216392. The observed-best window is descriptive, not a new choice using evaluation outcomes.

Development-selected policies: {"logistic": {"window": "W3", "half_life": 0.0}, "hgb": {"window": "W3", "half_life": 0.0}}. Uniform winners imply that decay was not selected on development data; later isolated decay gains do not reverse that decision. A universal optimal history length or half-life is not established.

| model | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- |
| logistic_W1_uniform | 0.218871 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W2_uniform | 0.218664 | -0.000206 | -0.003444 | 0.003401 | 543 |
| logistic_W3_uniform | 0.219166 | 0.000296 | -0.002896 | 0.003773 | 543 |
| logistic_W4_uniform | 0.219417 | 0.000546 | -0.003684 | 0.005114 | 543 |
| hgb_W1_uniform | 0.219158 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W2_uniform | 0.216486 | -0.002672 | -0.008569 | 0.003014 | 543 |
| hgb_W3_uniform | 0.214954 | -0.004205 | -0.009798 | 0.001601 | 543 |
| hgb_W4_uniform | 0.216392 | -0.002766 | -0.008664 | 0.003150 | 543 |

1. **Logistic history expansion:** compare same-feature uniform policies above. More data is not automatically better; the development-selected window may differ from the best later point estimate, and no later-year choice replaces it.
2. **Boosting history expansion:** compare the same-feature W1 and expanded windows, then separately the original M4 full-feature reference below. These isolate different questions; one comparison cannot substitute for the other.
3. **Optimal window:** the selected 2008-or-other policy is a development choice recorded above, not a proven universal optimum. Maximum 1999 coverage need not win.
4. **Recency:** uniform and 3/5/8-year policies are compared within selected windows. A later exploratory gain is not selection authority; uniform may remain the development winner. No generally reliable superiority claim follows from a single interval.

| model | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- |
| hgb_W1_uniform | 0.219158 | 0.001732 | -0.002410 | 0.006324 | 543 |
| hgb_W2_uniform | 0.216486 | -0.000940 | -0.007162 | 0.005295 | 543 |
| hgb_W3_uniform | 0.214954 | -0.002473 | -0.007888 | 0.002927 | 543 |
| hgb_W4_uniform | 0.216392 | -0.001034 | -0.007790 | 0.005706 | 543 |

## Elo warm-up, calibration and uncertainty

Standard and margin Elo compare 1999 versus 2018 initialization separately, using the same evaluation games and fixed parameters. Main HGB windows share the extended Elo stream, so their window differences do not confound separate rating warm-up. No early initialized Elo is represented as mature historical evidence.

| model | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- |
| elo_extended | 0.224453 | -0.000039 | -0.000068 | -0.000013 | 543 |
| elo_original | 0.224492 | 0.000000 | 0.000000 | 0.000000 | 543 |
| margin_elo_extended | 0.219131 | -0.000003 | -0.000006 | -0.000001 | 543 |
| margin_elo_original | 0.219134 | 0.000000 | 0.000000 | 0.000000 | 543 |

Reliability diagrams, identifiable calibration intercept/slope, probability and confidence buckets are exported for every comparison. Only development-selected policies receive sigmoid/adequately supported isotonic variants, fit in separate intervening years. The first calibration year overlaps development (2021), which limits model-selection independence; evaluation remains strictly later. No calibrated variant is automatically selected for production.

Paired season-week percentile bootstrap intervals reuse M2–M4 methods on identical games. Few seasons, repeated teams, interweek dependence and many exploratory comparisons remain limitations. One interval excluding zero is not by itself a superiority claim. The repeatedly examined 2024–2025 seasons are not independent confirmation. Existing 2026 official forecasts are neither rewritten nor retroactively issued by M5.

## Storage and runtime

Development fits recorded: 60; total measured fit seconds 28.379. Forward uncalibrated fits: 80; total measured fit seconds 37.057. CPU threads capped at 2. These figures exclude initial downloads/features and vary by machine.

Training uses compact pregame matrices, never raw PBP per candidate. Raw ingestion disables nflreadpy memory accumulation and processes one season at a time; source hashes and immutable season generations provide local reuse. Audit loading is also season-bounded. Compact feature reconstruction prunes statistical context to current/prior season and caches each output. Native Windows peak-memory/runtime behavior remains unmeasured; Linux evidence is included below. Recorded process peak RSS: 766738432 bytes (includes feature/audit/model work in that process; not Windows RAM certification).

## Registry and preservation

The additive M4 registry records window start/end policy, weighting half-life/cutoff/normalization/effective size, feature schema, fixed algorithm parameters, calibration, dataset fingerprint, evaluation and experimental designation. M5 artifacts carry activation_blocked and registry activation explicitly refuses them even with an approval JSON. Existing M4 activation/rollback support remains intact; no destructive database changes occur.

## Tests and combined Windows acceptance

```json
{
  "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
  "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
  "baseline_tests": 74,
  "final_tests": 86,
  "test_command": "python -m pytest -q",
  "warnings": {
    "dependency_deprecations": 5,
    "expected_low_coverage_synthetic_fixture": 1
  },
  "preserved_m4_artifacts_verified": 428,
  "champion_sqlite_registry_and_existing_elo_preserved": true,
  "available_source_seasons": [
    1999,
    2000,
    2001,
    2002,
    2003,
    2004,
    2005,
    2006,
    2007,
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
    2026
  ],
  "new_historical_seasons": [
    1999,
    2000,
    2001,
    2002,
    2003,
    2004,
    2005,
    2006,
    2007,
    2008,
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2016,
    2017
  ],
  "experimental_fold_models_verified": 96,
  "m5_activation_blocked": true,
  "actual_activations": 0,
  "dashboard_and_temporary_prediction_check": {
    "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
    "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
    "native_windows": false,
    "checked_at": "2026-11-03T06:21:59.847981+00:00",
    "checks": {
      "champion_load": "passed",
      "upcoming_predictions": "passed",
      "Upcoming Games": "passed",
      "Team Comparison": "passed",
      "Model Performance": "passed",
      "Model Analysis": "passed",
      "Team Power Rankings": "passed",
      "registry_load": "passed",
      "preservation": "passed"
    },
    "champion_version": "20261103T043653-6d77120a",
    "upcoming_count": 151,
    "registered_candidates_loaded": 480,
    "preserved_artifacts": 970,
    "status": "Review required; no automatic Windows certification. Native Windows, full data/model steps, manual UI startup and RAM behavior must all be verified."
  },
  "comparison_artifacts_verified": 20,
  "peak_rss_bytes": 766738432,
  "data_cache_bytes": 729905383,
  "native_windows_checks_executed": [],
  "combined_windows_acceptance": "NOT VERIFIED. Genuine Windows 10/11 Python 3.12 execution, RAM/runtime, full CLI/UI and local persistence checks remain pending; provided scripts are not certification.",
  "module_hashes": {
    "m3_dashboard.py": "5351a7f3c795b59a7205b25aeb959df19b4c5a025addaa3859caa7bf07812632",
    "history_analysis.py": "6cbb397ed884a20e6c0a4ca9047a1363825dad8f64366a31aef59e99138fbb3a",
    "schedule_features.py": "9729eeb3858191e1c89adf8e6c3f2a4e251268fa993fd4b9e93deb1f791001dd",
    "model.py": "1b8f73c4803e1fcb311bf13ee17f3c5a2a52b7c49cb0f70a62439ed205a10f2b",
    "m3.py": "42d8fd33f580e6eb182a5888192da4399f54edf1ae441f9cf873d76a257f68c0",
    "elo.py": "97bf2249618d43d21ab07d7c5437c4cb3371cc0bb5d6269504aa5db7754c5451",
    "reporting.py": "185fddd2facda141021a56a55dd0ad31707e61447f705a3edf6b90268975371b",
    "cli.py": "2092672d7f49f62076b9903366e2d4dcd86516e7fb35e97dd68297a645f21df0",
    "data_loader.py": "547ee2edd97693b6160446e62762db63a5566c2b9105a3a1101c038dcd4dbf80",
    "backtest.py": "8d177789ebefadee6faad10b98b88e6c60df9db3023b3d41e9ff7aaed76d80d9",
    "database.py": "0702742af2c55912ea929f86d94fc57274aa1a3375c86affc0693559aafb76ca",
    "m4.py": "f9d5295a8bc6d6def814240deac98de3bfcbc397d669fe50a87f59f701c84899",
    "predictions.py": "c71f5a2e87c06dc16fd10e74d7de2ba36a2c46d8aa31a2eec99906b73440a556",
    "history_dashboard.py": "ab2c79c13d5880984981d655c88b509b5112e812e6dff4cd7028cf382df03768",
    "__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "evaluation.py": "8a2dc24b652bc7e7e83fa8d26b973352403408cb7b1aa9ab0549e6b186daccd3",
    "history_models.py": "b4bd9b307bcde845e746ec1a9f4e2b4c35d7de1ead25959bffa7edd27d9f6cee",
    "m3_report.py": "19bd0681bbfe85de698834e53d61ffbd430918a112cc80f552f28ee0fae0274e",
    "feature_engineering.py": "ee4bcfc79052a2b726af4157e2041d02936c51956676b69884fa8eb0d65daa07",
    "m4_report.py": "1e1239612ace980b20dd217bb435f65bfee31e181140f08799a905554e83f558",
    "history_cli.py": "94966cb188c638f1ecedf9e3a80c23994289bfd88edfcad824ddfbc6606ca66a",
    "history_data.py": "db5ff7c811db1000293dea9508c6494fcfb968aeaf570575adb8e3b74763dba4",
    "quarterbacks.py": "bbf4cafb6c8e18e553a1c559f19a58958df636e0a198beac5e981b726c1ebc59",
    "history_report.py": "e3504b572ddbc6352713c84790c5e85a8a6e523cb7501ba96522379d65705699",
    "analysis.py": "6d9588137f1ca80f758c83aa53c1824604bccc054216a9a513dc5a1254b271a3",
    "integrity.py": "07d50bd7f6c96229e7f007c56a38cca396998765919a7ba622f1e3fa072fd6ad",
    "history_features.py": "28a679caf0e6a8d44873c68f23e220f6cfc11d65a41646120acbe187639dcb18",
    "dashboard.py": "957dd6e4a6409a82606b923c459d30b2c9344c9af4e1b1251b53efd96828bb38",
    "m4_dashboard.py": "2b0a7e4564dfed036ff255e34ab5f519b569193646f2ebc0b8edc2c5ea0e6fe2",
    "m4_features.py": "83c4207b219fc1bd3f3bb8a1e5f56b428726fcfbc9d808b19a28a5824640e1b4",
    "registry.py": "20269fa7bcbc07be18032f644febd09e1f2a008c10c890eb8e8c0f400ed79f3d",
    "boosting.py": "de08051c363f429945c1cb82d15daac37435cf0be4b7c050c6db029aff5034c6",
    "data_validation.py": "92049d2d37fcf1869457b3f7b91c4a136f877a7f6852eaece18509be09b584ac"
  },
  "test_hashes": {
    "test_m5.py": "ad58484d533b5fcc0a33ac9d2e1a227681d1642bdbc25cdd92f5d0806e235307",
    "test_m4.py": "c5f7d5d25ae155d620410f02630ccb70c242d503b92f8ebea32ce10af00aa2a5",
    "test_m2.py": "2fb65d03af4d252ded29a6ff1624a9b120511b281f38dc66845cdc7702ff56e4",
    "test_m3.py": "bcf4e819ef0343e0052a5172bdaa6443014020ea058b47975c44bf61e066cf9f",
    "test_engine.py": "d8288426b53285d33a94e22018733a9200970c1c6da8a77009ba99fefd56a6e4"
  }
}
```

No genuine Windows environment is available in this task. Combined M4/M5 Windows-native acceptance is **not passed**. A PowerShell checklist/script covers installation, imports, CLI, source/audit/cache reuse, both algorithms, weighted experiments, calibration, registry, dashboard, upcoming games and preservation. Linux checks cannot certify Windows RAM/runtime behavior or native dependencies.

## Launch and outstanding limits

With the virtual environment active: `python -m nfl_predictor.cli update-history --start 1999 --end 2017`; `python -m nfl_predictor.cli audit-history`; `python -m nfl_predictor.cli compare-history`; `python -m nfl_predictor.cli report-m5`; `python -m streamlit run app.py`. Historical Training Analysis appears within Model Analysis. Training never runs during page rendering. Default M1–M4 commands retain the original modern history unless expansion is explicitly requested.

Measured run: `reports/m5/6478a947c6ea519f`. Source audits and all generated windows/weights/model diagnostics remain separate from the official forecast database. Downloaded raw datasets, SQLite and model binaries are ignored by Git; local environment caches contain the downloaded seasons. Missing dates, corrected/vintage EPA, incomplete early PBP and exact historical publication timing remain material limits.

## Promotion recommendation and M6 priorities

Keep the official M2 champion. Historical findings are exploratory and cannot supersede at-risk Windows acceptance or future explicit approval. Complete combined native Windows acceptance, collect independent prospective outcomes, improve early PBP/time evidence and verify era stability before considering promotion. M6 was not started.
