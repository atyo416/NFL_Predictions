# M3 engineering report

## Outcome and baseline preservation

M3 adds standalone dynamic Elo, capped margin-sensitive Elo, power rankings, explicit schedule rest/bye context, and an evidence-tagged QB layer on top of M2. No official champion, stored forecast or database schema was changed. M2 statistical comparison, mean-imputation/scaling, calibration diagnostics and paired week-block uncertainty are reused. Baseline tests: 36 passed before implementation on Linux. Native Windows verification remains outstanding.

Recorded champion: `{"version": "20261103T043653-6d77120a", "features": ["off_epa", "def_epa", "scoring", "turnover", "off_success", "def_success", "win", "off_yards", "def_yards", "recent_off_epa", "recent_def_epa", "rest", "neutral"], "training_seasons": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026], "training_cutoff": "2026-11-02T09:20:00+00:00"}`. The production artifact uses its recorded production cutoff; chronological benchmarks independently reproduce the original fixed-period training contract. Baseline hashes and reference metrics are in docs/m3/BASELINE.json; verification results below establish preservation, not the prior engineering report alone.

## Elo methodology

Algorithm elo-m3-v1; parameters: `{"initial": 1500.0, "scale": 400.0, "k": 20.0, "home_advantage": 50.0, "regression": 0.67, "margin": false}`. Standard probability is 1/(1+10^(-(home Elo + HFA - away Elo)/400)); HFA=0 at neutral sites. Each result changes both teams equally and oppositely by K(actual−pregame expected), with ties=0.5. Parameters were fixed before examining M3 results; there was no search.

The event engine snapshots kickoff ratings before any equal-time eligible-result updates. Each result is applied once at its availability time. Stable GSIS-style franchise abbreviations normalize relocations. Postseason and blocked/canceled games do not update ratings. Exact duplicate rows are deduplicated; conflicting duplicate results raise an error. Offseason ratings move toward 1500 with retention 0.67 (compounded for skipped years). Very delayed prior-season updates are attenuated across the offseason and do not alter current-season records.

The first source season (2018) is warmup, never an evaluation season. The main logistic comparison preserves M2 training rows including 2018 to reproduce its benchmark. warmup_sensitivity.csv separately refits all logistic candidates without the initialization season. No claim is made that early-2018 Elo had mature history.

## Margin experiment

clip(log1p(min(abs(margin),42))*2.2/(2.2+.001*clip(winner_pregame_elo_advantage,-1000,1000)),.5,3); ties multiplier=1. Winner advantage includes venue-adjusted pregame Elo. This bounds extreme margins and tempers expected-favorite wins; it is an experimental design assumption rather than a validated NFL optimum.

| model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- |
| elo_margin | accuracy | 0.651934 | 0.012891 | -0.014575 | 0.040293 | 543 |
| elo_margin | brier | 0.219134 | -0.005357 | -0.010454 | -0.000214 | 543 |
| elo_margin | log_loss | 0.627875 | -0.011898 | -0.023944 | 0.000973 | 543 |

Margin-adjusted Elo is not made the default on the basis of this exploratory sample. Standard Elo remains the default experimental rating algorithm; the official M2 model remains unchanged.

## Current power rankings

Cutoff: 2026-11-03T05:16:07.484409+00:00. Standard Elo, all 32 teams. Previous-week rank is the ranking seven calendar days before this cutoff.

| rank | team | elo | previous_week_rank | weekly_change | record | last_opponent | last_result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | BUF | 1601.970018 | 1 | 6.605693 | 6-1-0 | BAL | W |
| 2 | DEN | 1592.900670 | 2 | 7.389462 | 6-2-0 | KC | W |
| 3 | MIN | 1573.877789 | 3 | -9.390560 | 6-1-0 | DET | L |
| 4 | SF | 1571.062164 | 4 | 0.000000 | 6-1-0 | ATL | L |
| 5 | SEA | 1568.730637 | 5 | 0.000000 | 4-3-0 | KC | W |
| 6 | DET | 1563.859302 | 6 | 9.390560 | 5-2-0 | MIN | W |
| 7 | PIT | 1556.519273 | 7 | 6.759720 | 6-2-0 | CLE | W |
| 8 | JAX | 1548.412795 | 9 | 6.285038 | 5-2-0 | IND | W |
| 9 | NE | 1545.246196 | 10 | 9.018214 | 5-3-0 | MIA | W |
| 10 | GB | 1537.415910 | 12 | 6.849015 | 5-3-0 | CAR | W |
| 11 | LA | 1537.045117 | 13 | 7.066943 | 4-4-0 | LAC | W |
| 12 | KC | 1535.273417 | 8 | -7.389462 | 5-2-0 | DEN | L |
| 13 | CHI | 1534.755611 | 11 | 0.000000 | 5-2-0 | NE | W |
| 14 | BAL | 1515.957886 | 15 | -6.605693 | 4-4-0 | BUF | L |
| 15 | CIN | 1513.886115 | 16 | 5.174037 | 5-2-0 | TEN | W |
| 16 | HOU | 1505.908962 | 17 | 0.000000 | 2-5-0 | NYG | L |
| 17 | PHI | 1503.820074 | 14 | -23.287461 | 2-6-0 | WAS | L |
| 18 | TB | 1477.861864 | 22 | 8.870860 | 3-5-0 | ATL | W |
| 19 | CLE | 1476.212455 | 18 | -6.759720 | 5-3-0 | PIT | L |
| 20 | DAL | 1472.082157 | 21 | -0.367270 | 3-5-0 | ARI | L |
| 21 | ATL | 1470.721803 | 19 | -8.870860 | 3-5-0 | TB | L |
| 22 | LAC | 1467.923384 | 20 | -7.066943 | 0-7-0 | LA | L |
| 23 | WAS | 1461.925966 | 26 | 10.363081 | 2-4-1 | PHI | W |
| 24 | CAR | 1460.385821 | 23 | -6.849015 | 3-4-0 | GB | L |
| 25 | IND | 1450.288057 | 24 | -6.285038 | 2-6-0 | JAX | L |
| 26 | NYG | 1450.206306 | 27 | 0.000000 | 4-2-1 | HOU | W |
| 27 | MIA | 1442.988791 | 25 | -9.018214 | 1-6-0 | NE | L |
| 28 | NO | 1436.595258 | 28 | 0.000000 | 2-5-0 | PIT | L |
| 29 | LV | 1431.693818 | 29 | 10.981191 | 4-4-0 | NYJ | W |
| 30 | ARI | 1429.880156 | 30 | 13.291651 | 3-5-0 | DAL | W |
| 31 | NYJ | 1393.931530 | 31 | -10.981191 | 2-6-0 | LV | L |
| 32 | TEN | 1370.660698 | 32 | -5.174037 | 1-7-0 | CIN | L |

Snapshots include pregame/postgame values, update time, record, last opponent/result, rank and seven-day change. History charts place postgame ratings at availability time, never before kickoff. Ratings/exports are checksummed immutable Parquet/CSV bundles with configuration and source manifests.

## Rest and bye methodology

Rest days use scheduled target kickoff minus the latest known played kickoff in the same season. A previous game must be result-eligible before cutoff; no previous game produces missing rest rather than zero. Short rest is <6 days; extended rest is >10 days without a scheduled bye. Thresholds are configurable. Bye detection uses a complete-looking team schedule (at least 16 entries), exactly one absent week within weeks 4–14, and the immediately following week. It never labels a long gap alone as a bye. Incomplete/ambiguous schedules yield unknown indicators; late missing/canceled weeks are not turned into byes.

This is schedule-derived identification, not an authoritative separately published bye registry. Unusual early/late byes outside the accepted window remain unknown. Current schedule vintages can include historical postponement revisions; archived schedule knowledge cannot be reconstructed. Known postponed/canceled games are excluded as played predecessors. Individual rest-days, bye, short/extended rest, joint replacement and redundant-rest control experiments are exported. The joint model removes the old rest column to avoid automatic duplication; no new features are deployed. Post-bye result tables are descriptive diagnostics, not automatic score adjustments.

## QB sources and safeguards

Inspected installed nflreadpy 0.1.5 APIs and actual depth-chart (2024/2026), injury-report and weekly-roster schemas. 2024 depth charts are weekly records without publication timestamps; 2026 has dt/team/gsis_id/pos_abb/pos_rank snapshot fields. Weekly injuries/rosters lack reliable pregame publication timestamps. The inspected 2026 depth snapshot ends in March and is stale for this November source snapshot. None proves the actual future starter or healthy status.

The normalized layer preserves GSIS player IDs, source and retrieval times, designation, quality and availability. Old weekly data is retrospective; unverified modern depth candidates remain unknown. Neither automatically enters experiments. Reviewed local evidence may be imported with named source, game ID, timezone-aware source and observation timestamps and explicit verified-pregame classification. Both timestamps must strictly precede the target cutoff. This validation cannot independently authenticate user-supplied evidence; users must retain the underlying report. Actual completed-game starter IDs are only previous-game observations after result eligibility, never that game’s own pregame designation.

QB candidate changes compare verified candidate IDs to the latest already-observed starter. Missing prior identity, injury reports or designations remain unknown. Conflicting equally recent designations remain unknown. A historical QB candidate requires matched verified training/evaluation coverage; no full-season versus subset comparisons are allowed. Current experiment coverage/status:

| evaluation | qb_training_games | qb_evaluation_games | qb_status |
| --- | --- | --- | --- |
| 2022 | 0 | 0 | Skipped: no sufficient matched, verified pregame QB coverage |
| 2023 | 0 | 0 | Skipped: no sufficient matched, verified pregame QB coverage |
| 2024 | 0 | 0 | Skipped: no sufficient matched, verified pregame QB coverage |
| 2025 | 0 | 0 | Skipped: no sufficient matched, verified pregame QB coverage |

## Chronological experiments

Same frozen M2 chronological folds: train 2018–2020/evaluate 2022; train 2018–2021/evaluate 2023; train 2018–2022/evaluate 2024 and 2025. The intervening calibration years are retained in fold metadata for protocol consistency but no M3 calibrator or hyperparameter is selected on them. All compared candidates use identical binary games. Elo updates causally on eligible earlier results during the evaluation season; logistic coefficients remain fitted only on the training period.

2024–2025 was previously examined and is explicitly exploratory. Independently issued prospective 2026 results remain separate. No retroactive forecast issuance or M4 work was added.

| model | accuracy | brier | log_loss |
| --- | --- | --- | --- |
| always_home | 0.535912 | 0.248721 | 0.690586 |
| elo_margin | 0.651934 | 0.219134 | 0.627875 |
| elo_only | 0.639042 | 0.224492 | 0.639773 |
| historical_home_rate | 0.535912 | 0.248721 | 0.690586 |
| logistic | 0.644567 | 0.220954 | 0.631279 |
| m2_bye | 0.637201 | 0.220973 | 0.631232 |
| m2_elo | 0.642726 | 0.220227 | 0.630039 |
| m2_elo_rest | 0.639042 | 0.220119 | 0.629768 |
| m2_extended_rest | 0.640884 | 0.220721 | 0.630724 |
| m2_rest | 0.639042 | 0.220845 | 0.630937 |
| m2_rest_days | 0.642726 | 0.220973 | 0.631315 |
| m2_rest_redundancy_check | 0.639042 | 0.220827 | 0.630898 |
| m2_short_rest | 0.642726 | 0.220977 | 0.631296 |
| pregame_win_percentage | 0.657459 | 0.222769 | 0.637090 |

## Paired uncertainty and calibration

| model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- |
| elo_margin | accuracy | 0.651934 | 0.007366 | -0.025936 | 0.039108 | 543 |
| elo_margin | brier | 0.219134 | -0.001819 | -0.009637 | 0.006045 | 543 |
| elo_margin | log_loss | 0.627875 | -0.003404 | -0.020536 | 0.014756 | 543 |
| elo_only | accuracy | 0.639042 | -0.005525 | -0.044447 | 0.032613 | 543 |
| elo_only | brier | 0.224492 | 0.003538 | -0.004322 | 0.011979 | 543 |
| elo_only | log_loss | 0.639773 | 0.008493 | -0.008243 | 0.026349 | 543 |
| m2_elo | accuracy | 0.642726 | -0.001842 | -0.018834 | 0.016636 | 543 |
| m2_elo | brier | 0.220227 | -0.000727 | -0.004449 | 0.003046 | 543 |
| m2_elo | log_loss | 0.630039 | -0.001241 | -0.010101 | 0.007823 | 543 |
| m2_elo_rest | accuracy | 0.639042 | -0.005525 | -0.024489 | 0.014870 | 543 |
| m2_elo_rest | brier | 0.220119 | -0.000834 | -0.004523 | 0.003026 | 543 |
| m2_elo_rest | log_loss | 0.629768 | -0.001511 | -0.010425 | 0.007811 | 543 |
| m2_rest | accuracy | 0.639042 | -0.005525 | -0.016514 | 0.005474 | 543 |
| m2_rest | brier | 0.220845 | -0.000108 | -0.000833 | 0.000574 | 543 |
| m2_rest | log_loss | 0.630937 | -0.000342 | -0.001901 | 0.001098 | 543 |

Deltas are candidate minus M2 logistic. Positive accuracy and negative Brier/log-loss favor candidates. Confidence intervals reuse M2 paired season-week cluster resampling (2,000 replicates, seed 42, 95% by default). They are unadjusted exploratory intervals; repeated teams and interweek dependence, multiple comparisons and few seasons restrict inference. Small apparent improvements alone do not justify promotion.

Every model has probability buckets, reliability diagrams, diagnostic calibration intercept/slope, seasonal results and aligned sample sizes. Diagnostic calibration is assessed using outcomes but never fitted into deployed predictions. elo_vs_win_percentage.csv separately compares both Elo variants to the pregame win-percentage baseline on identical games.

| period | model | estimate | difference | difference_low | difference_high |
| --- | --- | --- | --- | --- | --- |
| 2022 | elo_margin | 0.225287 | 0.003930 | -0.006736 | 0.013237 |
| 2022 | elo_only | 0.232579 | 0.011223 | -0.002538 | 0.021919 |
| 2022 | logistic | 0.221357 | 0.000000 | 0.000000 | 0.000000 |
| 2022 | m2_elo | 0.224569 | 0.003213 | -0.006194 | 0.012729 |
| 2022 | m2_elo_rest | 0.226137 | 0.004780 | -0.005949 | 0.015489 |
| 2022 | m2_rest | 0.223639 | 0.002282 | -0.002265 | 0.006922 |
| 2023 | elo_margin | 0.234201 | 0.002041 | -0.006704 | 0.011526 |
| 2023 | elo_only | 0.234711 | 0.002551 | -0.008574 | 0.013339 |
| 2023 | logistic | 0.232160 | 0.000000 | 0.000000 | 0.000000 |
| 2023 | m2_elo | 0.233110 | 0.000950 | -0.004494 | 0.006099 |
| 2023 | m2_elo_rest | 0.234118 | 0.001958 | -0.004465 | 0.008765 |
| 2023 | m2_rest | 0.233488 | 0.001328 | -0.001912 | 0.004770 |
| 2024 | elo_margin | 0.213194 | 0.002089 | -0.009217 | 0.012372 |
| 2024 | elo_only | 0.220565 | 0.009460 | -0.002021 | 0.020808 |
| 2024 | logistic | 0.211105 | 0.000000 | 0.000000 | 0.000000 |
| 2024 | m2_elo | 0.208286 | -0.002819 | -0.007828 | 0.002944 |
| 2024 | m2_elo_rest | 0.208166 | -0.002939 | -0.008275 | 0.003047 |
| 2024 | m2_rest | 0.211118 | 0.000013 | -0.000982 | 0.000931 |
| 2025 | elo_margin | 0.225096 | -0.005743 | -0.014734 | 0.006185 |
| 2025 | elo_only | 0.228433 | -0.002406 | -0.011743 | 0.008226 |
| 2025 | logistic | 0.230839 | 0.000000 | 0.000000 | 0.000000 |
| 2025 | m2_elo | 0.232211 | 0.001372 | -0.003461 | 0.006388 |
| 2025 | m2_elo_rest | 0.232117 | 0.001278 | -0.003459 | 0.006240 |
| 2025 | m2_rest | 0.230608 | -0.000231 | -0.001314 | 0.000755 |

## Verification evidence

```json
{
  "recorded_at": "2026-11-03T05:25:36.411811+00:00",
  "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
  "python": "3.12.14",
  "native_windows": "not verified",
  "baseline_tests_passed": 36,
  "final_tests_passed": 62,
  "test_command": "python -m pytest -q",
  "dependency_warnings": 2,
  "preserved_m2_artifact_hashes_verified": 128,
  "champion_and_database_unchanged": true,
  "dashboard_pages_passed": [
    "Upcoming Games",
    "Team Comparison",
    "Model Performance",
    "Model Analysis",
    "Team Power Rankings"
  ],
  "real_scheduled_matchup_checked": "2026_09_JAX_BAL",
  "real_matchup_checks": [
    "champion probability",
    "Elo-only probability",
    "rest/bye fields",
    "QB context"
  ],
  "performance": {
    "elo_replay_games": 2399,
    "elo_eligible_updates": 2248,
    "elo_replay_seconds": 0.38605477099963537
  },
  "module_hashes": {
    "m3_dashboard.py": "5351a7f3c795b59a7205b25aeb959df19b4c5a025addaa3859caa7bf07812632",
    "schedule_features.py": "9729eeb3858191e1c89adf8e6c3f2a4e251268fa993fd4b9e93deb1f791001dd",
    "model.py": "1b8f73c4803e1fcb311bf13ee17f3c5a2a52b7c49cb0f70a62439ed205a10f2b",
    "m3.py": "42d8fd33f580e6eb182a5888192da4399f54edf1ae441f9cf873d76a257f68c0",
    "elo.py": "97bf2249618d43d21ab07d7c5437c4cb3371cc0bb5d6269504aa5db7754c5451",
    "reporting.py": "185fddd2facda141021a56a55dd0ad31707e61447f705a3edf6b90268975371b",
    "cli.py": "206d3471d558b995eac9f22709eaf7fc5afc269890fbf09d627659dbab47a563",
    "data_loader.py": "969330217a55698f53c1dd16fd4be72cb4b8fb62c60b562a4be94f9a60f9a2ad",
    "backtest.py": "8d177789ebefadee6faad10b98b88e6c60df9db3023b3d41e9ff7aaed76d80d9",
    "database.py": "0702742af2c55912ea929f86d94fc57274aa1a3375c86affc0693559aafb76ca",
    "predictions.py": "463fcfd652b8c12c4556d48a742d07b588c9a53ad92e3a75226977f818bdfb58",
    "__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "evaluation.py": "8a2dc24b652bc7e7e83fa8d26b973352403408cb7b1aa9ab0549e6b186daccd3",
    "m3_report.py": "19bd0681bbfe85de698834e53d61ffbd430918a112cc80f552f28ee0fae0274e",
    "feature_engineering.py": "f35d57068ac65d83c28e9f8902fa44d1e453e04b26d23f99bddc34310625f044",
    "quarterbacks.py": "bbf4cafb6c8e18e553a1c559f19a58958df636e0a198beac5e981b726c1ebc59",
    "analysis.py": "6d9588137f1ca80f758c83aa53c1824604bccc054216a9a513dc5a1254b271a3",
    "integrity.py": "29115341b9af63c6516d3588c68df5209c4b11c84e1d0287d6f43b950f8f8f78",
    "dashboard.py": "957dd6e4a6409a82606b923c459d30b2c9344c9af4e1b1251b53efd96828bb38",
    "data_validation.py": "92049d2d37fcf1869457b3f7b91c4a136f877a7f6852eaece18509be09b584ac"
  },
  "test_file_hashes": {
    "test_m2.py": "2fb65d03af4d252ded29a6ff1624a9b120511b281f38dc66845cdc7702ff56e4",
    "test_m3.py": "bcf4e819ef0343e0052a5172bdaa6443014020ea058b47975c44bf61e066cf9f",
    "test_engine.py": "d8288426b53285d33a94e22018733a9200970c1c6da8a77009ba99fefd56a6e4"
  }
}
```

All applicable checks are offline; the source-schema investigation used live network access separately. New tests cover symmetric Elo updates, ties, initialization/regression, stable identities, duplicate/conflicting results, exact-time result eligibility, simultaneous games, future-outcome/feature injection, delayed finals, margin caps, 32-team snapshots, rest/bye cases, historical/modern QB schemas, conflicting/missing statuses, CLI preservation, dashboard loading and artifact reproduction/corruption. Existing M2 tests cover SQLite/model compatibility and chronological statistics.

## Reproduction and artifacts

From a virtual environment: `python -m pytest -q`; `python -m nfl_predictor.cli ratings`; `python -m nfl_predictor.cli compare-m3`; `python -m nfl_predictor.cli report-m3`; `python -m streamlit run app.py`. Launch locally on port 8501. `rankings` aliases rating export; optional `--cutoff` must include timezone. Rating bundles are stored under data/ratings/ with CSV history/ranking exports; experimental outputs remain separate under reports/m3/.

Measured comparison run: `reports/m3/3e7c9f1bcf35c5f6`. Metadata records parameters, sources/hashes, exact feature sets, training/evaluation cutoffs, preprocessing, runtime and code fingerprints. Outputs include comparison, Elo-variant and win-percentage comparisons, calibration, buckets, coefficients, missingness, post-bye diagnostics and initialization sensitivity. These are experimental results, not official prediction logs.

## Limitations and promotion recommendation

Retain the M2 champion and standard experimental Elo. No candidate is automatically promoted. Historical source-vintage and final-publication timestamps remain unresolved; the M2 kickoff+8h fallback is retained. Unknown extraordinary suspensions cannot be repaired by a duration proxy. Bye inference is bounded and source-vintage-dependent. Sufficient historical pregame QB evidence was not established in the inspected sources, so no historical QB improvement is claimed. Native Windows execution is not verified. No new dependencies or GPU are required.

## M4 recommendations

Reserve a genuinely unexamined prospective period; collect immutable timestamped starter designations and authoritative final timestamps; validate bye mappings against published schedules; run Windows-native smoke tests; assess stability across more seasons before considering promotion. M4 was not started.
