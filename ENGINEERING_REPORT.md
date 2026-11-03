# M1 engineering report

Implemented and verified on Linux with Python 3.12.14. Native Windows execution remains unverified; Windows instructions are provided. No claim of full M1 acceptance is made because exact result-availability timestamps and vintage source snapshots are unavailable.

## Functionality and structure

Modules in nfl_predictor/ separate ingestion, coverage validation, pregame features, sklearn model, evaluation, backtests, SQLite persistence, predictions and CLI. app.py supplies three Streamlit pages; tests/test_engine.py supplies offline deterministic tests. pyproject.toml, requirements.lock.txt and README.md support installation. Generated data/, models/ and reports/ are ignored.

## Actual source coverage

nflverse schedules and play-by-play were downloaded through nflreadpy 0.1.5. Installed load_schedules, load_pbp and load_team_stats signatures were inspected. Weekly summaries are intentionally not used: play-by-play directly supplies the required efficiency statistics. Retrieval timestamps and game counts are stored per season.

| Season | Scheduled REG | Final scores | Binary outcomes |
|---|---:|---:|---:|
| 2018 | 256 | 256 | 254 |
| 2019 | 256 | 256 | 255 |
| 2020 | 256 | 256 | 255 |
| 2021 | 272 | 272 | 271 |
| 2022 | 271 | 271 | 269 |
| 2023 | 272 | 272 | 272 |
| 2024 | 272 | 272 | 272 |
| 2025 | 272 | 272 | 271 |
| 2026 | 272 | 121 | 120 |

2022 has 271 completed games due to the canceled BUF–CIN game. 2026 has 121 score-complete games at retrieval, but the most recent game is still within the conservative eight-hour availability delay and lacks play-by-play metrics. That game cannot contribute to current ratings yet. Nine ties across the cached seasons are excluded from binary labels (9/2,399 scheduled regular-season games, approximately 0.38%); ties remain half-wins in historical ratings.

## Architecture and validity

Training-only mean imputation → StandardScaler → L2 logistic regression, C=1, seed=42. The serialized pipeline keeps preprocessing and model together. Features are home-minus-away season-to-date EPA, defensive EPA (sign reversed), scoring and turnover differentials, offensive/defensive success, win fraction, offensive/defensive yards, recent three-game EPA, rest difference and neutral venue. The intercept supplies average home advantage. Priors regress previous-season team means 50% toward previous-season league means and carry four games of weight. Missing franchise history uses league means; no-prior values remain missing until training-only imputation. See README for precise eligibility and units.

## Measured fixed benchmark

Train 2018–2022; validate 2023; test 2024–2025. No test tuning was performed. Production fitting is independent.

| Period/model | Games | Accuracy | Brier | Log loss |
|---|---:|---:|---:|---:|
| validation/logistic | 272 | 62.1324% | 0.231586 | 0.656115 |
| validation/home_pick | 272 | 55.5147% | 0.247216 | 0.687571 |
| validation/training_rate | 272 | 55.5147% | 0.247216 | 0.687571 |
| validation/pregame_win_percentage | 272 | 59.1912% | 0.241008 | 0.675257 |
| test/logistic | 543 | 64.4567% | 0.220954 | 0.631279 |
| test/home_pick | 543 | 53.5912% | 0.248721 | 0.690586 |
| test/training_rate | 543 | 53.5912% | 0.248721 | 0.690586 |
| test/pregame_win_percentage | 543 | 65.7459% | 0.222769 | 0.637090 |

Home pick uses a finite training-derived probability (not hard 0/1). In this dataset its forecasts coincide with the training-rate baseline because the training home win rate exceeds one half. The additional win-percentage baseline uses clipped 0.5 + pregame win-fraction difference/2.

| Fixed test season | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 2024 | 68.3824% | 0.211105 | 0.610522 |
| 2025 | 60.5166% | 0.230839 | 0.652113 |

## Separate walk-forward results

| Evaluation | Training through | Games | Accuracy | Brier | Log loss |
|---|---|---:|---:|---:|---:|
| 2023 | 2022 | 272 | 62.1324% | 0.231586 | 0.656115 |
| 2024 | 2023 | 272 | 67.6471% | 0.212246 | 0.613176 |
| 2025 | 2024 | 271 | 59.7786% | 0.229392 | 0.648648 |

reports/ contains current-run historical prediction Parquet, calibration/confidence CSVs, backtest JSON and reliability PNG. Calibration is reported, not asserted.

## Verification and persistence

16 offline synthetic pytest tests passed. They exercise normalization/deduplication, missing schemas, failed downloads preserving cache, future scores, current/future statistic injection, eight-hour overlap exclusion, deterministic priors and orientation, training-only imputation, probability validity, serialization, chronological walk-forward boundaries, ties, upcoming games, future cutoff rejection, immutable official forecasts, appended revisions, and corrected results preserving original forecasts. All three pages executed through Streamlit AppTest without exceptions. The server started on port 8501, and both the HTTP root and health endpoint returned success.

## Performance and limitations

Initial source ingestion completed for all nine seasons in approximately 30 seconds on this cloud machine. Feature construction is deliberately straightforward and currently takes tens of seconds; it scans history per matchup and should be cached/vectorized before larger workloads. No GPU is used. Initial downloads persist as Parquet; unchanged seasons are skipped.

Exact game completion timestamps are absent: kickoff plus eight hours is a conservative proxy for ordinary games, not a proof for extraordinary suspended games. Historical sources are current revised datasets, not archived as-of snapshots. Raw source status and kickoff updates are only as reliable as nflverse. Cache writes are atomic per table, not a multi-table crash-safe transaction. Mean imputation uses zero only for an entirely missing training column. Special-teams turnovers and separate special-teams efficiency are outside the initial model. No Windows machine was available for native testing. Dependencies were installed in a fresh Linux venv. 151 genuine upcoming-game official forecasts were generated and stored in SQLite. Forecast issuance and SQLite history were exercised separately from retrospective backtests. These limits prevent unconditional certification of every M1 acceptance criterion.

## Launch and handoff

From repository root with the venv active: `python -m streamlit run app.py`. See README.md for complete Windows installation and all CLI operations. Cloud installation and service startup instructions are saved in the environment draft; saving is not publication or proof of fresh-task restoration. Review/save environment settings and publish through the product to capture the prepared filesystem.

## M2 priorities

Obtain authoritative final timestamps and vintage data snapshots; test natively on Windows; add transactional season manifests and source hashes; cache/vectorize feature generation; assess calibration on a separate validation protocol; expand special-teams accounting.
