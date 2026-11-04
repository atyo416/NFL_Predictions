# M8.2 NFL margin and historical ATS benchmark

Two fixed independent regression families; historical closing-line research only. Existing win-probability models, activation, official forecasts, M8 odds/wagers and M8.1 results are unchanged. No paper wagers or market API calls are generated.

## Coverage and sign verification

| season | scheduled | eligible_scores | ties_included | missing_invalid_spread | price_pairs_present | price_pairs_valid |
| --- | --- | --- | --- | --- | --- | --- |
| 2008 | 256 | 256 | 1 | 0 | 185 | 185 |
| 2009 | 256 | 256 | 0 | 0 | 242 | 242 |
| 2010 | 256 | 256 | 0 | 0 | 256 | 256 |
| 2011 | 256 | 256 | 0 | 0 | 256 | 256 |
| 2012 | 256 | 256 | 1 | 0 | 256 | 256 |
| 2013 | 256 | 256 | 1 | 0 | 256 | 256 |
| 2014 | 256 | 256 | 1 | 0 | 256 | 256 |
| 2015 | 256 | 256 | 0 | 0 | 256 | 256 |
| 2016 | 256 | 256 | 2 | 0 | 256 | 256 |
| 2017 | 256 | 256 | 0 | 0 | 255 | 255 |
| 2018 | 256 | 256 | 2 | 0 | 256 | 256 |
| 2019 | 256 | 256 | 1 | 0 | 256 | 256 |
| 2020 | 256 | 256 | 1 | 0 | 256 | 256 |
| 2021 | 272 | 272 | 1 | 0 | 272 | 272 |
| 2022 | 271 | 271 | 2 | 0 | 271 | 271 |
| 2023 | 272 | 272 | 0 | 0 | 272 | 272 |
| 2024 | 272 | 272 | 0 | 0 | 272 | 272 |
| 2025 | 272 | 272 | 1 | 0 | 272 | 272 |

Training starts in 2008; 1999–2007 supplies existing Elo warmup/context. All eligible ties are retained with margin zero. Missing/invalid scores and unfinished/blocked results are excluded; missing/invalid spreads are excluded from the common evaluation sample, but not independent training. Missing feature values remain missing until training-only preprocessing.

1871 eligible predicted games; 1871 matched closing spreads; 0 spread exclusions across 2019–2025. Expected regular-season counts are 256 through 2020 and 272 thereafter; 2022 has 271 following the canceled Buffalo–Cincinnati game.

`actual_home_margin = home_score - away_score`; `market_home_margin = spread_line` (home-favorite-positive); home ATS residual = actual minus market. A positive model-minus-market edge selects home; negative selects away. Exact zero has no preference. Pushes are zero actual-minus-market residual, irrespective of chosen side.

Cached sign examples (negative home moneyline denotes the home favorite where paired prices are present):

| game_id | home_team | away_team | home_score | away_score | spread_line | home_moneyline | away_moneyline |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024_01_BAL_KC | KC | BAL | 27.000000 | 20.000000 | 3.000000 | -148.000000 | 124.000000 |
| 2024_01_ARI_BUF | BUF | ARI | 34.000000 | 28.000000 | 6.500000 | -310.000000 | 250.000000 |
| 2024_01_TEN_CHI | CHI | TEN | 24.000000 | 17.000000 | 4.000000 | -198.000000 | 164.000000 |
| 2024_02_SF_MIN | MIN | SF | 23.000000 | 17.000000 | -4.500000 | 180.000000 | -218.000000 |

For KC–BAL: home margin +7, closing margin +3, home ATS residual +4. Away-favorite spreads are negative; unit tests also explicitly verify home +7 and away-favorite −3 orientation. These are source schedule closing fields; no book/quote timestamp is verified. Paired spread-price counts above are descriptive American-odds syntax checks only; invalid/missing prices never get fabricated or enter the regressors.

## Frozen training protocol and models

Each annual pair fits on completed 2008–previous-season games with result availability strictly before the first target-season kickoff. Estimators and preprocessing remain frozen throughout that season. Existing pregame team ratings and Elo continue updating only from earlier eligible games; conservative result availability is kickoff +8h, or the existing date-unknown upper bound. Historical features are retrospective data vintages, not timestamped original publications.

Development: 2019–2021. Final exploratory evaluation: 2022–2025. No configurations or thresholds were selected from either set of results. Previously examined 2024–2025 is not independent confirmation. Two families, three predefined thresholds (nonzero, ≥3, ≥5), seven annual fits each; no search, calibration or promotion.

Features: `off_epa`, `def_epa`, `scoring`, `turnover`, `off_success`, `def_success`, `win`, `off_yards`, `def_yards`, `recent_off_epa`, `recent_def_epa`, `neutral`, `elo_difference`. Existing M5 common pregame home-minus-away features are reused; defensive signs are advantage-oriented. Four-game previous-season priors regress halfway toward prior league means. No rest feature, retrospective personnel/QB, scores, closing line or prices enter either estimator. Intercepts represent usual home advantage; neutral is explicit.

Ridge: mean imputation (empty training columns kept as zero), StandardScaler, fixed alpha=10. Boosted regressor: {"early_stopping": false, "l2_regularization": 1.0, "learning_rate": 0.05, "loss": "squared_error", "max_depth": 2, "max_iter": 100, "max_leaf_nodes": 4, "min_samples_leaf": 20, "random_state": 42}. Native missing-value handling; wholly empty training columns are excluded using training rows only. CPU threads=2. Models live only in models/m82, with training-only content fingerprints and verified joblib checksums; they never enter the classifier registry.

| season | training_start | training_end | training_games | training_cutoff | latest_training_result | evaluation_games | model_version | cache_reused |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2019 | 2008 | 2018 | 2816 | 2019-09-06T00:20:00+00:00 | 2018-12-31T09:20:00+00:00 | 256 | m82-2019-42a96e6605d9ed1a | False |
| 2020 | 2008 | 2019 | 3072 | 2020-09-11T00:20:00+00:00 | 2019-12-30T09:20:00+00:00 | 256 | m82-2020-4d76f43739a5fa06 | False |
| 2021 | 2008 | 2020 | 3328 | 2021-09-10T00:20:00+00:00 | 2021-01-04T09:20:00+00:00 | 272 | m82-2021-f9bb8c66fbacc311 | False |
| 2022 | 2008 | 2021 | 3600 | 2022-09-09T00:20:00+00:00 | 2022-01-10T09:20:00+00:00 | 271 | m82-2022-f2ed52888935454c | False |
| 2023 | 2008 | 2022 | 3871 | 2023-09-08T00:20:00+00:00 | 2023-01-09T09:20:00+00:00 | 272 | m82-2023-86aa2fad0de5d9bf | False |
| 2024 | 2008 | 2023 | 4143 | 2024-09-06T00:20:00+00:00 | 2024-01-08T09:20:00+00:00 | 272 | m82-2024-bdfde19252e9e395 | False |
| 2025 | 2008 | 2024 | 4415 | 2025-09-05T00:20:00+00:00 | 2025-01-06T09:20:00+00:00 | 272 | m82-2025-83e9ebb92268674a | False |

## development

| model | games | mae | rmse | bias_predicted_minus_actual | mae_minus_market | difference_low | difference_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| closing_market | 784 | 10.284439 | 13.204171 | 0.932398 | 0.000000 | 0.000000 | 0.000000 |
| ridge | 784 | 10.590717 | 13.530917 | 1.762915 | 0.306279 | 0.090709 | 0.515230 |
| boosted | 784 | 10.690765 | 13.664640 | 1.813593 | 0.406326 | 0.170739 | 0.629986 |

Bias = predicted minus actual home points. MAE deltas = model minus market (negative favors model). Nominal 95% paired season-week percentile bootstrap, 2,000 replicates, seed 42, reusing existing resampling mechanics.

Historical ATS selections (not real bets); win rates exclude pushes:

| model | minimum_edge | games_evaluated | selections | wins | losses | pushes | win_rate_ex_push | win_rate_low | win_rate_high | push_rate | home_selections | home_win_rate | away_selections | away_win_rate | home_minus_away_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0 | 784 | 784 | 405 | 365 | 14 | 0.525974 | 0.490664 | 0.561026 | 0.017857 | 474 | 0.496788 | 310 | 0.570957 | -0.074169 |
| ridge | 3 | 784 | 240 | 119 | 115 | 6 | 0.508547 | 0.444874 | 0.571944 | 0.025000 | 165 | 0.496933 | 75 | 0.535211 | -0.038279 |
| ridge | 5 | 784 | 86 | 47 | 38 | 1 | 0.552941 | 0.447241 | 0.654063 | 0.011628 | 63 | 0.539683 | 23 | 0.590909 | -0.051227 |
| boosted | 0 | 784 | 784 | 393 | 377 | 14 | 0.510390 | 0.475117 | 0.545559 | 0.017857 | 473 | 0.483940 | 311 | 0.551155 | -0.067215 |
| boosted | 3 | 784 | 263 | 131 | 127 | 5 | 0.507752 | 0.447084 | 0.568193 | 0.019011 | 183 | 0.513812 | 80 | 0.493506 | 0.020306 |
| boosted | 5 | 784 | 103 | 52 | 50 | 1 | 0.509804 | 0.414210 | 0.604686 | 0.009709 | 76 | 0.500000 | 27 | 0.538462 | -0.038462 |

## exploratory_evaluation

| model | games | mae | rmse | bias_predicted_minus_actual | mae_minus_market | difference_low | difference_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| closing_market | 1087 | 9.494480 | 12.360286 | -0.573597 | 0.000000 | 0.000000 | 0.000000 |
| ridge | 1087 | 9.907505 | 12.766824 | -0.081986 | 0.413025 | 0.252336 | 0.588542 |
| boosted | 1087 | 9.954163 | 12.847445 | -0.033359 | 0.459683 | 0.294377 | 0.634984 |

Bias = predicted minus actual home points. MAE deltas = model minus market (negative favors model). Nominal 95% paired season-week percentile bootstrap, 2,000 replicates, seed 42, reusing existing resampling mechanics.

Historical ATS selections (not real bets); win rates exclude pushes:

| model | minimum_edge | games_evaluated | selections | wins | losses | pushes | win_rate_ex_push | win_rate_low | win_rate_high | push_rate | home_selections | home_win_rate | away_selections | away_win_rate | home_minus_away_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0 | 1087 | 1087 | 532 | 526 | 29 | 0.502836 | 0.472752 | 0.532899 | 0.026679 | 624 | 0.502463 | 463 | 0.503341 | -0.000878 |
| ridge | 3 | 1087 | 319 | 151 | 162 | 6 | 0.482428 | 0.427620 | 0.537663 | 0.018809 | 198 | 0.489691 | 121 | 0.470588 | 0.019102 |
| ridge | 5 | 1087 | 120 | 55 | 63 | 2 | 0.466102 | 0.378587 | 0.555754 | 0.016667 | 75 | 0.486486 | 45 | 0.431818 | 0.054668 |
| boosted | 0 | 1087 | 1087 | 511 | 547 | 29 | 0.482987 | 0.452992 | 0.513105 | 0.026679 | 616 | 0.485050 | 471 | 0.480263 | 0.004787 |
| boosted | 3 | 1087 | 350 | 164 | 179 | 7 | 0.478134 | 0.425806 | 0.530947 | 0.020000 | 216 | 0.481132 | 134 | 0.473282 | 0.007850 |
| boosted | 5 | 1087 | 127 | 59 | 66 | 2 | 0.472000 | 0.386631 | 0.559039 | 0.015748 | 83 | 0.512195 | 44 | 0.395349 | 0.116846 |

## Season-by-season margin results

| model | games | mae | rmse | bias_predicted_minus_actual | mae_minus_market | difference_low | difference_high | season |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| closing_market | 256 | 10.210938 | 13.127455 | 1.882812 | 0.000000 | 0.000000 | 0.000000 | 2019 |
| ridge | 256 | 10.499274 | 13.450709 | 2.708659 | 0.288336 | -0.134471 | 0.687868 | 2019 |
| boosted | 256 | 10.638370 | 13.705066 | 2.803202 | 0.427432 | 0.006076 | 0.834405 | 2019 |
| closing_market | 256 | 9.830078 | 12.770778 | 0.998047 | 0.000000 | 0.000000 | 0.000000 | 2020 |
| ridge | 256 | 10.031210 | 13.009736 | 2.258593 | 0.201131 | -0.086251 | 0.476020 | 2020 |
| boosted | 256 | 10.157768 | 13.078376 | 2.308950 | 0.327690 | 0.042979 | 0.593271 | 2020 |
| closing_market | 272 | 10.781250 | 13.669181 | -0.023897 | 0.000000 | 0.000000 | 0.000000 | 2021 |
| ridge | 272 | 11.203378 | 14.076270 | 0.406282 | 0.422128 | 0.049613 | 0.766893 | 2021 |
| boosted | 272 | 11.241722 | 14.157584 | 0.415979 | 0.460472 | 0.029507 | 0.846406 | 2021 |
| closing_market | 271 | 8.741697 | 11.432862 | -0.321033 | 0.000000 | 0.000000 | 0.000000 | 2022 |
| ridge | 271 | 9.006525 | 11.659968 | 0.072731 | 0.264828 | 0.005100 | 0.535690 | 2022 |
| boosted | 271 | 9.120515 | 11.779254 | 0.046660 | 0.378818 | 0.115131 | 0.641972 | 2022 |
| closing_market | 272 | 9.900735 | 13.070721 | -1.025735 | 0.000000 | 0.000000 | 0.000000 | 2023 |
| ridge | 272 | 10.427667 | 13.461973 | -0.566805 | 0.526931 | 0.186901 | 0.848133 | 2023 |
| boosted | 272 | 10.567879 | 13.676603 | -0.462380 | 0.667144 | 0.366218 | 0.993172 | 2023 |
| closing_market | 272 | 9.610294 | 12.605146 | -0.375000 | 0.000000 | 0.000000 | 0.000000 | 2024 |
| ridge | 272 | 9.925090 | 12.927000 | 0.307616 | 0.314796 | -0.052667 | 0.722822 | 2024 |
| boosted | 272 | 9.890586 | 12.914883 | 0.352006 | 0.280292 | -0.090987 | 0.691549 | 2024 |
| closing_market | 272 | 9.722426 | 12.271178 | -0.571691 | 0.000000 | 0.000000 | 0.000000 | 2025 |
| ridge | 272 | 10.267425 | 12.945302 | -0.140916 | 0.544999 | 0.193860 | 0.903713 | 2025 |
| boosted | 272 | 10.234609 | 12.943577 | -0.069427 | 0.512182 | 0.164968 | 0.848777 | 2025 |

## Season-by-season ATS results

| model | minimum_edge | games_evaluated | selections | wins | losses | pushes | win_rate_ex_push | win_rate_low | win_rate_high | push_rate | home_selections | home_win_rate | away_selections | away_win_rate | home_minus_away_win_rate | season |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge | 0 | 256 | 256 | 127 | 119 | 10 | 0.516260 | 0.454043 | 0.577977 | 0.039062 | 152 | 0.455782 | 104 | 0.606061 | -0.150278 | 2019 |
| ridge | 3 | 256 | 70 | 33 | 32 | 5 | 0.507692 | 0.389165 | 0.625362 | 0.071429 | 48 | 0.434783 | 22 | 0.684211 | -0.249428 | 2019 |
| ridge | 5 | 256 | 27 | 15 | 11 | 1 | 0.576923 | 0.389486 | 0.744556 | 0.037037 | 19 | 0.578947 | 8 | 0.571429 | 0.007519 | 2019 |
| boosted | 0 | 256 | 256 | 122 | 124 | 10 | 0.495935 | 0.434000 | 0.557995 | 0.039062 | 151 | 0.438356 | 105 | 0.580000 | -0.141644 | 2019 |
| boosted | 3 | 256 | 85 | 41 | 39 | 5 | 0.512500 | 0.404933 | 0.618921 | 0.058824 | 58 | 0.482143 | 27 | 0.583333 | -0.101190 | 2019 |
| boosted | 5 | 256 | 31 | 16 | 14 | 1 | 0.533333 | 0.361423 | 0.697676 | 0.032258 | 24 | 0.500000 | 7 | 0.666667 | -0.166667 | 2019 |
| ridge | 0 | 256 | 256 | 141 | 115 | 0 | 0.550781 | 0.489546 | 0.610515 | 0.000000 | 170 | 0.535294 | 86 | 0.581395 | -0.046101 | 2020 |
| ridge | 3 | 256 | 85 | 47 | 38 | 0 | 0.552941 | 0.447241 | 0.654063 | 0.000000 | 65 | 0.584615 | 20 | 0.450000 | 0.134615 | 2020 |
| ridge | 5 | 256 | 29 | 17 | 12 | 0 | 0.586207 | 0.407378 | 0.744868 | 0.000000 | 24 | 0.583333 | 5 | 0.600000 | -0.016667 | 2020 |
| boosted | 0 | 256 | 256 | 140 | 116 | 0 | 0.546875 | 0.485651 | 0.606713 | 0.000000 | 165 | 0.533333 | 91 | 0.571429 | -0.038095 | 2020 |
| boosted | 3 | 256 | 90 | 48 | 42 | 0 | 0.533333 | 0.431022 | 0.632916 | 0.000000 | 68 | 0.573529 | 22 | 0.409091 | 0.164439 | 2020 |
| boosted | 5 | 256 | 38 | 20 | 18 | 0 | 0.526316 | 0.372590 | 0.675210 | 0.000000 | 31 | 0.516129 | 7 | 0.571429 | -0.055300 | 2020 |
| ridge | 0 | 272 | 272 | 137 | 131 | 4 | 0.511194 | 0.451613 | 0.570459 | 0.014706 | 152 | 0.493333 | 120 | 0.533898 | -0.040565 | 2021 |
| ridge | 3 | 272 | 85 | 39 | 45 | 1 | 0.464286 | 0.361542 | 0.570153 | 0.011765 | 52 | 0.442308 | 33 | 0.500000 | -0.057692 | 2021 |
| ridge | 5 | 272 | 30 | 15 | 15 | 0 | 0.500000 | 0.331541 | 0.668459 | 0.000000 | 20 | 0.450000 | 10 | 0.600000 | -0.150000 | 2021 |
| boosted | 0 | 272 | 272 | 131 | 137 | 4 | 0.488806 | 0.429541 | 0.548387 | 0.014706 | 157 | 0.474359 | 115 | 0.508929 | -0.034570 | 2021 |
| boosted | 3 | 272 | 88 | 42 | 46 | 0 | 0.477273 | 0.376066 | 0.580380 | 0.000000 | 57 | 0.473684 | 31 | 0.483871 | -0.010187 | 2021 |
| boosted | 5 | 272 | 34 | 16 | 18 | 0 | 0.470588 | 0.314515 | 0.632633 | 0.000000 | 21 | 0.476190 | 13 | 0.461538 | 0.014652 | 2021 |
| ridge | 0 | 271 | 271 | 131 | 130 | 10 | 0.501916 | 0.441671 | 0.562105 | 0.036900 | 150 | 0.496552 | 121 | 0.508621 | -0.012069 | 2022 |
| ridge | 3 | 271 | 77 | 39 | 36 | 2 | 0.520000 | 0.408742 | 0.629309 | 0.025974 | 47 | 0.456522 | 30 | 0.620690 | -0.164168 | 2022 |
| ridge | 5 | 271 | 29 | 15 | 12 | 2 | 0.555556 | 0.373130 | 0.724141 | 0.068966 | 17 | 0.562500 | 12 | 0.545455 | 0.017045 | 2022 |
| boosted | 0 | 271 | 271 | 126 | 135 | 10 | 0.482759 | 0.422826 | 0.543191 | 0.036900 | 149 | 0.479167 | 122 | 0.487179 | -0.008013 | 2022 |
| boosted | 3 | 271 | 87 | 41 | 43 | 3 | 0.488095 | 0.384084 | 0.593148 | 0.034483 | 48 | 0.425532 | 39 | 0.567568 | -0.142036 | 2022 |
| boosted | 5 | 271 | 27 | 14 | 11 | 2 | 0.560000 | 0.370673 | 0.733344 | 0.074074 | 15 | 0.571429 | 12 | 0.545455 | 0.025974 | 2022 |
| ridge | 0 | 272 | 272 | 125 | 133 | 14 | 0.484496 | 0.424190 | 0.545257 | 0.051471 | 156 | 0.482993 | 116 | 0.486486 | -0.003493 | 2023 |
| ridge | 3 | 272 | 76 | 34 | 40 | 2 | 0.459459 | 0.350734 | 0.572187 | 0.026316 | 50 | 0.479167 | 26 | 0.423077 | 0.056090 | 2023 |
| ridge | 5 | 272 | 25 | 12 | 13 | 0 | 0.480000 | 0.300313 | 0.665015 | 0.000000 | 14 | 0.500000 | 11 | 0.454545 | 0.045455 | 2023 |
| boosted | 0 | 272 | 272 | 115 | 143 | 14 | 0.445736 | 0.386323 | 0.506742 | 0.051471 | 153 | 0.448276 | 119 | 0.442478 | 0.005798 | 2023 |
| boosted | 3 | 272 | 78 | 35 | 40 | 3 | 0.466667 | 0.358157 | 0.578425 | 0.038462 | 51 | 0.489796 | 27 | 0.423077 | 0.066719 | 2023 |
| boosted | 5 | 272 | 29 | 9 | 20 | 0 | 0.310345 | 0.172756 | 0.492301 | 0.000000 | 18 | 0.277778 | 11 | 0.363636 | -0.085859 | 2023 |
| ridge | 0 | 272 | 272 | 145 | 123 | 4 | 0.541045 | 0.481225 | 0.599704 | 0.014706 | 161 | 0.543750 | 111 | 0.537037 | 0.006713 | 2024 |
| ridge | 3 | 272 | 92 | 48 | 42 | 2 | 0.533333 | 0.431022 | 0.632916 | 0.021739 | 59 | 0.534483 | 33 | 0.531250 | 0.003233 | 2024 |
| ridge | 5 | 272 | 37 | 17 | 20 | 0 | 0.459459 | 0.310386 | 0.616160 | 0.000000 | 25 | 0.520000 | 12 | 0.333333 | 0.186667 | 2024 |
| boosted | 0 | 272 | 272 | 142 | 126 | 4 | 0.529851 | 0.470096 | 0.588762 | 0.014706 | 158 | 0.535032 | 114 | 0.522523 | 0.012509 | 2024 |
| boosted | 3 | 272 | 97 | 50 | 46 | 1 | 0.520833 | 0.422038 | 0.618026 | 0.010309 | 65 | 0.515625 | 32 | 0.531250 | -0.015625 | 2024 |
| boosted | 5 | 272 | 41 | 23 | 18 | 0 | 0.560976 | 0.410405 | 0.701099 | 0.000000 | 29 | 0.620690 | 12 | 0.416667 | 0.204023 | 2024 |
| ridge | 0 | 272 | 272 | 131 | 140 | 1 | 0.483395 | 0.424547 | 0.542707 | 0.003676 | 157 | 0.484076 | 115 | 0.482456 | 0.001620 | 2025 |
| ridge | 3 | 272 | 74 | 30 | 44 | 0 | 0.405405 | 0.300906 | 0.519242 | 0.000000 | 42 | 0.476190 | 32 | 0.312500 | 0.163690 | 2025 |
| ridge | 5 | 272 | 29 | 11 | 18 | 0 | 0.379310 | 0.226880 | 0.559975 | 0.000000 | 19 | 0.368421 | 10 | 0.400000 | -0.031579 | 2025 |
| boosted | 0 | 272 | 272 | 128 | 143 | 1 | 0.472325 | 0.413689 | 0.531734 | 0.003676 | 156 | 0.474359 | 116 | 0.469565 | 0.004794 | 2025 |
| boosted | 3 | 272 | 88 | 38 | 50 | 0 | 0.431818 | 0.333327 | 0.536013 | 0.000000 | 52 | 0.480769 | 36 | 0.361111 | 0.119658 | 2025 |
| boosted | 5 | 272 | 30 | 13 | 17 | 0 | 0.433333 | 0.273775 | 0.608027 | 0.000000 | 21 | 0.523810 | 9 | 0.222222 | 0.301587 | 2025 |

## Interpretation and limitations

The closing reference uses identical games for all three margin estimates. It may include information released after the model feature cutoff. Source-level spread prices are not verified same-book executable quotes; bookmaker, publication time and settlement rules are unknown. No realized ROI, EV, CLV or profitability is estimated. At hypothetical flat −110 only, conditional break-even excluding pushes is 110/210 = 52.38%; this does not establish those historical prices or a betting advantage.

Wilson 95% binomial intervals are descriptive and assume independent selected decisions. Repeated teams, correlated weeks, few seasons and six model/threshold comparisons weaken that assumption; no multiplicity adjustment or validated best threshold is claimed. The paired week bootstrap also assumes independent weeks and misses longer dependence. Margin accuracy improvements do not directly give cover probabilities. Point disagreements are not calibrated betting value.

## Recommendation

Both independent models have larger measured exploratory MAE than the closing reference. A cover-probability model is not justified as a betting deployment from this evidence; keep it a deferred research question and first obtain genuine timestamp-aligned prospective data.

## Reproduction, verification and preservation

`python -m nfl_predictor.cli report-m82` reads cached schedule/metric Parquets and reuses compact historical features. It fits or loads two fixed regression families with annual training prefixes; no raw PBP is read or hashed. First-time data/feature setup follows the existing README historical-data workflow. No network is needed with complete caches.

Game-level audit: `reports/m82/5131ebec918a54a1/predictions.csv` (margins, cutoffs, versions, edge and grading for each threshold). Fold and source fingerprints accompany it. Generated caches/models/run CSV stay gitignored; the committed `M82_SPREAD_PREDICTIONS.csv` contains this run’s small game-level historical audit. Measured command runtime: 2.73 seconds; all outputs are historical, not issued pregame forecasts.

Verification results and preservation hashes are recorded below after execution. Native Windows certification was not performed; this execution uses Linux/Python 3.12.

## Execution and preservation evidence

Starting baseline: `a48540aa3e2b059478d7df44ec5ab99b262b412f` (M8.1), clean working tree. Collection confirmed **180 starting tests**; relevant existing M8.1/feature-leakage baseline: **6 passed in 7.97s**. New targeted suite: **7 passed in 2.33s**, no warnings.

Real cached execution reused all 28 compact season matrices (1999–2026), evaluated 2019–2025 only, and completed in **2.73 seconds**, including all 14 annual estimator fits. There were **1,871 unique game IDs**, all with closing spreads, including **six straight-up ties**; the 2022–2025 primary comparison uses **1,087** identical games. Both model families have worse MAE than closing in every evaluation year; no threshold has a consistent ATS advantage. No parameters were changed after examining results.

Execution dependencies: Python 3.12.14, scikit-learn 1.9.1, pandas 3.1.0, NumPy 2.5.4. Native Windows execution remains unverified.

A preimplementation SHA-256 snapshot covers **2,353 existing model/ledger/report files**, including **151 M7 genuine forecast files**. All bytes were unchanged after the measured historical run. Snapshot manifest SHA-256: `34c7667ed466b57ae5eda7dcb1ec62e87c970d95c08d79500f77c0d1ea49b5cd`. Selected protected SHA-256 values:

| Protected artifact | SHA-256 |
| --- | --- |
| `data/predictions.db` | `3a56d523b930a4aa0ed40bcdb07c74bd0ffa74527d7bd9576b0260ffe6dc4ebd` |
| `data/m8/lab.db` | `a626cf5ac4b7835773e6c136c3b962be3e72f1c07d26b4b44052a37c3db65414` |
| `M81_HISTORICAL_MARKET_REPORT.md` | `265eb1306c70d7aad29b2ecb4d941fa992becefe6727e892ad848401321aa8fe` |

Only new `models/m82` files were added; existing production champion, M5/M7 classifiers and activation pointers were preserved. SQLite files were not opened by the margin report. No M8 odds, wagers or forecast records were created/updated.

Committed audit SHA-256: `66c86b5e23ca50742bdcc36ab3f1bd5e5c12d9c6693150b6f09f779578108e71`. Source cache schedule/metric SHA-256 and retrieval timestamps are recorded in the run’s `metadata.json`; model versions and strict training cutoffs are in both the report and CSV.

Full regression suite was run **once** after the targeted checks: `python -m pytest -q` → **187 passed, 8 warnings in 186.06s**. The eight existing warnings comprise seven Streamlit/pandas deprecation warnings and one synthetic small-play-count coverage warning; the new targeted suite has no warnings. A final post-suite SHA-256 comparison again found **zero changes across all 2,353 protected files**. `git diff --check` passed.

M8.2 acceptance: cached scores/spreads loaded and sign verified; both fixed regressors trained; chronological matched predictions generated; MAE/RMSE/bias and paired intervals reported; three ATS thresholds graded with pushes and Wilson intervals; production/classifier/ledger artifacts preserved; targeted and full suites passed; report and small historical CSV delivered. No native Windows acceptance claim, cover-probability deployment or M9 work is included.
