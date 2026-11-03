# M2 engineering report

## Outcome and preservation

M2 adds a reproducible exploratory evaluation framework without replacing the M1 architecture or champion. Linux local verification passed before implementation (16 tests), and the expanded suite passes 36 tests. Native Windows execution remains unverified. All original M1 report files, the production model and the prediction database retain their original SHA-256 hashes; docs/m2/M1_PRESERVATION.json records the before/after verification baseline. No database or saved model migration was performed.

## Implementation

New modules: integrity.py (versioned atomic season caches), analysis.py (chronological comparisons, calibration, paired uncertainty and ablations), reporting.py (measured reports and season-gap analysis), dashboard.py (read-only Model Analysis). Existing ingestion, rolling features, pipeline training, CLI, backtesting, persistence and other three UI pages remain in place. A cache-aware build avoids recomputing unchanged historical features. Training now accepts an optional feature subset while its default and serialized M1 pipeline remain compatible.

## Data and leakage audit

Cached nflverse schedules and play-by-play cover 2018–2026. Historical regular-season counts are 256/256/256/272/271/272/272/272 for 2018–2025; 2026 has 272 scheduled games and 121 score-complete games in the preserved source snapshot. No new prospective outcomes were inferred. Historical 2022 includes the canceled BUF–CIN schedule exception. Exact final/publication times and historical source vintages could not be established. The eight-hour availability fallback remains; optional independently verified availability times and blocked game statuses are supported. Current/future data injection cannot change earlier pregame predictions in the tests. See [the per-feature audit](docs/m2/DATA_LEAKAGE_AUDIT.md) for sources, calculation, availability, missing values and risks.

Season generations retain raw/processed tables, hashes, row counts, schemas, retrieval timestamps and earlier versions. They publish through one atomic pointer. Failed-write and corrupt-cache recovery tests pass. Legacy adoption hashes existing bytes; it cannot prove upstream completeness or historical publication timing. Missing/low PBP coverage is flagged rather than silently zero-filled. No original forecast is revised when source statistics change.

## Frozen exploratory protocol

The checked-in config/m2_protocol.json defines seed 42, 2,000 paired season-week bootstrap replicates and 95% percentile intervals. Seven ablation groups use the same games as full models.

| Base training | Calibration | Forward evaluation |
|---|---|---|
| 2018–2020 | 2021 | 2022 |
| 2018–2021 | 2022 | 2023 |
| 2018–2022 | 2023 | 2024 |
| 2018–2022 | 2023 | 2025 |

The 2022/2023 folds are historical development exercises. M1 already exposed 2024–2025; those later comparisons are exploratory reuse, not untouched confirmation. No hyperparameter search or automatic champion replacement is performed. Future independent confirmation requires an unexamined prospective period, not retroactive 2026 forecasts generated after its outcomes.

## Measured comparisons: previously examined 2024–2025

| model | metric | estimate | low | high | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_home | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| always_home | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| always_home | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| historical_home_rate | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| historical_home_rate | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| historical_home_rate | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| isotonic | accuracy | 0.655617 | 0.617807 | 0.693582 | 0.011050 | -0.001869 | 0.027627 | 543 |
| isotonic | brier | 0.218940 | 0.205337 | 0.232599 | -0.002013 | -0.004789 | 0.001012 | 543 |
| isotonic | log_loss | 0.624336 | 0.594947 | 0.653455 | -0.006943 | -0.013758 | 0.000435 | 543 |
| logistic | accuracy | 0.644567 | 0.605503 | 0.681410 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | brier | 0.220954 | 0.207585 | 0.234306 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | log_loss | 0.631279 | 0.602509 | 0.659981 | 0.000000 | 0.000000 | 0.000000 | 543 |
| pregame_win_percentage | accuracy | 0.657459 | 0.611600 | 0.702012 | 0.012891 | -0.022141 | 0.053712 | 543 |
| pregame_win_percentage | brier | 0.222769 | 0.213975 | 0.231584 | 0.001815 | -0.007872 | 0.010635 | 543 |
| pregame_win_percentage | log_loss | 0.637090 | 0.618631 | 0.655367 | 0.005810 | -0.014712 | 0.025073 | 543 |
| sigmoid | accuracy | 0.629834 | 0.593282 | 0.665448 | -0.014733 | -0.029631 | 0.000000 | 543 |
| sigmoid | brier | 0.222519 | 0.210746 | 0.234591 | 0.001565 | -0.000852 | 0.004177 | 543 |
| sigmoid | log_loss | 0.634794 | 0.609787 | 0.659914 | 0.003515 | -0.001980 | 0.009296 | 543 |

Differences are candidate minus logistic. Positive accuracy and negative Brier/log-loss favor a candidate. All compared models use the same 543 non-tie games. Always-home picks have finite training-derived probabilities; this baseline coincides with the historical home-rate baseline here.

The uncalibrated M1 benchmark reproduces accuracy 64.4567%, Brier 0.220954 and log loss 0.631279. The win-percentage baseline has higher observed accuracy (65.7459%), but its paired accuracy interval spans both directions. Its Brier is 0.222769. Isotonic has observed Brier 0.218940 (delta −0.002013, paired 95% interval −0.004789 to +0.001012), which is insufficient evidence for promotion. Sigmoid Brier is 0.222519. No candidate becomes champion.

## Feature contribution

| group | mean_brier_contribution | positive_seasons | seasons | mean_accuracy_contribution | mean_log_loss_contribution |
| --- | --- | --- | --- | --- | --- |
| offensive_efficiency | 0.000862 | 3 | 4 | 0.001845 | 0.001485 |
| defensive_efficiency | 0.000192 | 2 | 4 | -0.002798 | 0.000302 |
| win_percentage | 0.000173 | 2 | 4 | -0.004657 | 0.000425 |
| turnovers | 0.000163 | 3 | 4 | 0.001842 | 0.000251 |
| scoring | 0.000060 | 3 | 4 | -0.002791 | 0.000152 |
| recent_performance | -0.000258 | 1 | 4 | 0.000919 | -0.000654 |
| rest_venue | -0.000510 | 2 | 4 | -0.003687 | -0.000864 |

Positive Brier contribution means the group improved observed Brier when present. Removing recent performance or rest/venue improved the point estimate on average, but **all seven paired Brier contribution intervals include zero**. No features were removed. These are conditional ablations of correlated variables; standardized coefficients are not causal effects. Training correlations, fold-level coefficients, every ablation metric and paired intervals are exported.

## Calibration and errors

Reliability diagrams, probability/confidence buckets, diagnostic calibration intercept/slope and forward-season metrics are generated. Constant forecasts cannot identify both slope and intercept; their diagnostic slope is omitted and an intercept shift is reported with slope fixed at one. Evaluation outcomes are used for diagnostics only, never for fitting the deployed map. Isotonic is skipped if fewer than 200 calibration games or ten distinct probabilities are available.

The 2024 versus 2025 uncalibrated accuracy gap is 7.87 percentage points; independently resampling weeks within each season gives a descriptive interval of 0.61 to 15.08 points. That interval excludes zero under this method, but it does not establish a repeatable cause or account for every cross-week dependency. There is insufficient evidence to attribute the variation to a specific football mechanism.

Error slices cover season/week, actual home/away winner, model favorite/underdog outcome, division status, probability, recent EPA difference and early/late season. Incorrect-prediction CSVs contain pregame features, probabilities and standardized feature × coefficient contributions to the linear score. They are downloadable from Model Analysis.

## Verification and performance

36 offline automated tests passed, including all M1 tests. Two Streamlit/Pandas deprecation warnings originate in dependency internals. Checks include future-statistic invariance at the prediction level, delayed/suspended/postponed games, chronological calibration boundaries, evaluation-target isolation, aligned paired comparisons, deterministic fresh experiment regeneration, constant-forecast diagnostics, cache corruption and interrupted publication, source revisions, unchanged SQLite compatibility, feature-cache reuse/rebuild and dashboard rendering. All four actual pages also executed through AppTest without exceptions against the prepared cache and reports.

A repeated full `analyze` invocation reused checksummed feature/experiment artifacts and completed in 1.43 seconds on this cloud machine. Initial feature construction still scans game histories; no unsupported speed claim is made for Windows. Only CPU libraries are used. Versioned source caches occupy approximately 327 MB here; retained generations grow with refreshes.

## Artifacts and reproduction

Current measured run: `reports/m2/63fc15ee7ad7e8e1`. Its metadata includes source manifests with retrieval times/hashes, training/calibration cutoffs, evaluation periods, feature sets, preprocessing, hyperparameters, Git reference, full module/data/runtime fingerprints and the frozen protocol. outputs.json authenticates all generated experiment files against local alteration (not upstream truth). Identical fresh inputs/configuration produce identical artifact hashes in tests.

The run includes MODEL_COMPARISON.md, FEATURE_ABLATION.md, CALIBRATION.md, ERROR_ANALYSIS.md, comparison.csv, ablations.csv, ablation_uncertainty.csv, coefficients.csv, training_feature_correlations.csv, calibration.csv, probability_buckets.csv, confidence_buckets.csv, error_slices.csv, incorrect_predictions.csv, predictions.parquet, reliability.png, season_gap.json and metadata.json. Original M1 reports remain unchanged.

## Launch and remaining limitations

From a virtual environment in the repository: `python -m pip install -r requirements.lock.txt`, `python -m pip install --no-deps -e ".[test]"`, `python -m nfl_predictor.cli update`, `python -m nfl_predictor.cli analyze`, then `python -m streamlit run app.py`. Open the locally running interface on port 8501. Full PowerShell instructions are in README.md. No cloud deployment was added.

Outstanding: native Windows execution; exact historical final/publication timestamps; archived source vintages; conclusive completeness checks for partially published PBP; stronger dependence-aware inference across more seasons; independent prospective confirmation. Bootstrap intervals are unadjusted for multiple exploratory comparisons and assume independent week blocks; they cannot establish unconditional superiority. Existing 151 official forecasts have no attached resolved outcomes in this preserved database, so prospective performance remains unmeasured. Source revisions create new caches and experiments, never rewrite issued forecast payloads. Avoid concurrent refreshes for the same season; atomic visibility does not serialize competing publishers.

M2 framework verification is complete within these documented source/platform limitations. No claim of improved predictive performance, native Windows certification or prospective validation is made. M3 was not started.
