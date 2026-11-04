# M8.1 historical market benchmark

Source: cached nflverse/nflreadpy schedules, `home_moneyline` and `away_moneyline`; classification `historical_closing_reference`. Predictions: unchanged M7 run `5b401bdc9b161ac3`; selected ensemble `E1_equal__raw`.

No model fitting, calibration, policy selection, API fetch, wager simulation or ledger writes were performed.

## Coverage and exclusions

| season | schedule_games | paired_moneylines | note |
| --- | --- | --- | --- |
| 2019 | 256 | 256 | paired fields present |
| 2020 | 256 | 256 | paired fields present |
| 2021 | 272 | 272 | paired fields present |
| 2022 | 271 | 271 | paired fields present |
| 2023 | 272 | 272 | paired fields present |
| 2024 | 272 | 272 | paired fields present |
| 2025 | 272 | 272 | paired fields present |

| reason_or_count | value |
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

Exclusion counts describe successive eligibility checks, not independent samples. Missing schedule caches also appear as unmatched prediction IDs. Ties and incomplete scores are excluded before moneyline checks. Invalid/missing probabilities are removed for every model in a comparison. Metadata conflicts include team orientation, kickoff, season/week or outcome disagreement.

## Four-way full base-prediction history

| model | games | accuracy | brier | log_loss | difference | difference_low | difference_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 1865 | 0.633244 | 0.224061 | 0.639396 | 0.013514 | 0.009681 | 0.017164 |
| closing_market | 1865 | 0.663807 | 0.210547 | 0.608393 | 0.000000 | 0.000000 | 0.000000 |
| logistic_oos | 1865 | 0.616622 | 0.229082 | 0.649626 | 0.018534 | 0.013559 | 0.023466 |
| margin_elo | 1865 | 0.635925 | 0.223899 | 0.639544 | 0.013352 | 0.009334 | 0.017388 |

Brier deltas are model minus closing market; lower is better. Intervals: paired season-week percentile bootstrap, 2000 replicates, seed 42, nominal 95%. The market self-difference is zero by construction.

Season-by-season results:

| season | model | games | accuracy | brier | log_loss |
| --- | --- | --- | --- | --- | --- |
| 2019 | boosting_oos | 255 | 0.635294 | 0.221941 | 0.636365 |
| 2019 | closing_market | 255 | 0.643137 | 0.212992 | 0.613604 |
| 2019 | logistic_oos | 255 | 0.560784 | 0.250106 | 0.694368 |
| 2019 | margin_elo | 255 | 0.647059 | 0.221737 | 0.635818 |
| 2020 | boosting_oos | 255 | 0.654902 | 0.218221 | 0.627089 |
| 2020 | closing_market | 255 | 0.678431 | 0.201757 | 0.590057 |
| 2020 | logistic_oos | 255 | 0.623529 | 0.223526 | 0.637751 |
| 2020 | margin_elo | 255 | 0.666667 | 0.215695 | 0.623307 |
| 2021 | boosting_oos | 271 | 0.579336 | 0.232405 | 0.656515 |
| 2021 | closing_market | 271 | 0.623616 | 0.216886 | 0.621560 |
| 2021 | logistic_oos | 271 | 0.590406 | 0.236554 | 0.666046 |
| 2021 | margin_elo | 271 | 0.608856 | 0.231481 | 0.657305 |
| 2022 | boosting_oos | 269 | 0.620818 | 0.228129 | 0.648687 |
| 2022 | closing_market | 269 | 0.654275 | 0.210821 | 0.608546 |
| 2022 | logistic_oos | 269 | 0.643123 | 0.221069 | 0.633209 |
| 2022 | margin_elo | 269 | 0.620818 | 0.225287 | 0.640939 |
| 2023 | boosting_oos | 272 | 0.621324 | 0.234441 | 0.663251 |
| 2023 | closing_market | 272 | 0.676471 | 0.218710 | 0.627349 |
| 2023 | logistic_oos | 272 | 0.621324 | 0.231586 | 0.656115 |
| 2023 | margin_elo | 272 | 0.606618 | 0.234201 | 0.662475 |
| 2024 | boosting_oos | 272 | 0.694853 | 0.208422 | 0.604918 |
| 2024 | closing_market | 272 | 0.716912 | 0.200162 | 0.587489 |
| 2024 | logistic_oos | 272 | 0.676471 | 0.212246 | 0.613176 |
| 2024 | margin_elo | 272 | 0.658088 | 0.213194 | 0.615211 |
| 2025 | boosting_oos | 271 | 0.627306 | 0.224445 | 0.638150 |
| 2025 | closing_market | 271 | 0.653137 | 0.212139 | 0.609383 |
| 2025 | logistic_oos | 271 | 0.597786 | 0.229392 | 0.648648 |
| 2025 | margin_elo | 271 | 0.645756 | 0.225096 | 0.640586 |

## Five-way frozen-policy sample

| model | games | accuracy | brier | log_loss | difference | difference_low | difference_high |
| --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 543 | 0.661142 | 0.216419 | 0.621503 | 0.010280 | 0.003721 | 0.017331 |
| closing_market | 543 | 0.685083 | 0.206139 | 0.598416 | 0.000000 | 0.000000 | 0.000000 |
| frozen_ensemble | 543 | 0.650092 | 0.216955 | 0.622611 | 0.010816 | 0.003835 | 0.017791 |
| logistic_oos | 543 | 0.637201 | 0.220803 | 0.630879 | 0.014664 | 0.007047 | 0.022287 |
| margin_elo | 543 | 0.651934 | 0.219134 | 0.627875 | 0.012995 | 0.004907 | 0.021496 |

Brier deltas are model minus closing market; lower is better. Intervals: paired season-week percentile bootstrap, 2000 replicates, seed 42, nominal 95%. The market self-difference is zero by construction.

Season-by-season results:

| season | model | games | accuracy | brier | log_loss |
| --- | --- | --- | --- | --- | --- |
| 2024 | boosting_oos | 272 | 0.694853 | 0.208422 | 0.604918 |
| 2024 | closing_market | 272 | 0.716912 | 0.200162 | 0.587489 |
| 2024 | frozen_ensemble | 272 | 0.665441 | 0.209485 | 0.607071 |
| 2024 | logistic_oos | 272 | 0.676471 | 0.212246 | 0.613176 |
| 2024 | margin_elo | 272 | 0.658088 | 0.213194 | 0.615211 |
| 2025 | boosting_oos | 271 | 0.627306 | 0.224445 | 0.638150 |
| 2025 | closing_market | 271 | 0.653137 | 0.212139 | 0.609383 |
| 2025 | frozen_ensemble | 271 | 0.634686 | 0.224453 | 0.638208 |
| 2025 | logistic_oos | 271 | 0.597786 | 0.229392 | 0.648648 |
| 2025 | margin_elo | 271 | 0.645756 | 0.225096 | 0.640586 |

## Interpretation and limitations

All rows within each table use identical games and home-win orientation. The four-way table uses all available base history; the five-way table narrows to availability of the frozen ensemble and its prior meta/calibration/selection cutoffs. Do not compare scores across these different samples as an ensemble effect. No alternative ensemble was selected from these results.

These are source-level closing-line pairs, not verified same-book snapshots. Bookmaker identity, precise quote/publication timestamps, executable prices and settlement rules are unknown and have not been fabricated. M8 decimal conversion and proportional no-vig functions are reused; their margin is only a source-pair overround proxy here. This source is never imported into the M8 sportsbook/wager ledger.

Closing lines may contain later information than the model predictions; exact relative timing cannot be verified. Cached/model/data vintages are retrospective, not genuinely issued market forecasts. Historical model probabilities retain the M7 chronological contracts, including annual base refits; they are not the currently deployed production artifact applied backward. The M2 and M5 labels identify architectures, with the existing M7 annual training policy.

Previously examined 2024–2025 is exploratory, and ensemble choice used earlier development years. Paired intervals are unadjusted descriptive evidence: repeated teams, interweek dependence, few seasons and prior model comparisons limit certainty. Binary scoring excludes ties and does not establish applicable market rules. No profitability, EV strategy, CLV certification or genuine prospective advantage is inferred.

## Recommendation

The closing reference has the lowest measured Brier score on the primary common sample. Further research is worthwhile as a timing/calibration diagnostic, but these results do not support model outperformance. Prioritize genuinely timestamp-aligned prospective comparisons; retain all models and policies unchanged.

## Reproducibility

`python -m nfl_predictor.cli report-m81` reads only schedule Parquets and saved M7 prediction/report files. No full PBP processing is needed.

| season | sha256 | retrieved_at |
| --- | --- | --- |
| 2019 | 490ae0ba90099fc099ab6177b573d177f45c4c26c4a38c78e747184f89c70ab2 | 2026-11-03T04:34:59.065779+00:00 |
| 2020 | a585db1c876ba699c9e02f07ed22a2dda37526b25b6924e1b6ae94a6e02b3400 | 2026-11-03T04:35:00.721465+00:00 |
| 2021 | 8273e3b50d26a010b83927dc1273f6eb2f8e13031065428770d92bfcfc41149f | 2026-11-03T04:35:02.348737+00:00 |
| 2022 | 1e80b33dae054fb5e35e958d58ce62084e0232efd40a1e2082fed618a62a1404 | 2026-11-03T04:35:04.263541+00:00 |
| 2023 | 16432451e901643d9521d703c377c93202e3ba3bb369bc4265bb6fbeed38812f | 2026-11-03T04:35:05.990159+00:00 |
| 2024 | 3c9b4ac76f93e7b62673ddf220df9e3574fdf02694d18ab7f7f121f15a202a5a | 2026-11-03T04:35:07.731837+00:00 |
| 2025 | da34c7753becfa89be45efa321a1e27c5ba5065eb332680b01f224e9ca5ad83f | 2026-11-03T04:34:39.067514+00:00 |

M7 input SHA-256:

| input | sha256 |
| --- | --- |
| base_predictions.parquet | a3ca327bda1879b35e71d45993602884e7ce05f3fedb0ab47ae1f20cefe4f0ae |
| predictions.parquet | c8c8cd8e4fda45df1832052dd97cac2f8551d0d5cc026074d27c920ff680e743 |
| selection.json | b37d2128803cc9f1aaf75545290c4c456ae1dad4ec883811c411b7fc4b8310ac |
| metadata.json | 9c1f7c48b6daa451244219177ceb0780a044cf402d1d87088bf2caeedce6fac3 |

## Handoff verification

- Targeted offline tests: 5 passed.
- Full existing regression suite, run once: 180 passed, 8 warnings in 164.70s (0:02:44).
- 2352 saved model/registry and ledger artifacts remained byte-for-byte unchanged, including the official forecast database, M7 experimental forecasts and M8 paper ledger.
- Verification ran on Linux/Python 3.12; native Windows testing is not claimed. Regression fixtures are isolated from the benchmark inputs.

These are recorded handoff checks; `report-m81` does not run tests or train models.
