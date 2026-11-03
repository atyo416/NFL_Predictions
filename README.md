# NFL Game Prediction Engine — M1

Local experimental NFL regular-season winner model using nflverse, Python, logistic regression, Parquet and SQLite. No betting features. CPU only; allow several GB of free disk space for initial play-by-play downloads. Python 3.11+ is required; Python 3.12 was verified on Linux. Windows 10/11 is the target, but a native Windows run has not been verified.

## Windows PowerShell: clean installation

With Python and Git installed:

```powershell
git clone https://github.com/atyo416/NFL_Predictions.git
cd NFL_Predictions
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
python -m pip install -e ".[test]"
python -m pytest -q
python -m nfl_predictor.cli update
python -m nfl_predictor.cli features
python -m nfl_predictor.cli backtest
python -m nfl_predictor.cli train
python -m nfl_predictor.cli predict
python -m streamlit run app.py
```

Open `http://localhost:8501` on your own computer. If PowerShell activation is restricted, invoke `.\.venv\Scripts\python.exe` directly instead. The lock records tested versions; pyproject.toml defines supported dependencies.

## Operations

Initial `update` downloads 2018–2026 season data. Later invocations reuse cached seasons. Use `python -m nfl_predictor.cli update --seasons 2026 --refresh` to explicitly refresh current data. Source access uses HTTPS to GitHub nflverse release assets. Downloads require Internet; cached comparisons and reports work offline. An unsuccessful source download does not replace its previously cached tables. No automatic scheduling is installed.

`features` writes cached game features. `train` fits a production model to completed eligible games available at execution time. `backtest` independently fits 2018–2022, reports 2023 validation and 2024–2025 held-out results, and separately trains walk-forward models through each preceding year. Production fitting never replaces those benchmark models or metrics. Generated outputs live in ignored data/, models/, reports/ directories.

`predict --cutoff 2026-11-02T12:00:00-05:00` optionally chooses a timezone-aware cutoff. It must be in the past and after the model training cutoff. Only currently unstarted 2026 games qualify; retrospective cutoffs cannot manufacture pregame issuance times. Actual creation time is recorded. The first saved valid forecast is official; revisions append separately. Refresh scores then run `predict` to attach outcomes without changing forecasts.

## Statistical definitions and leakage controls

Rows are home versus away. Differences are oriented so higher EPA, success, scoring, turnover and win percentages favor home; defensive EPA, defensive success and defensive yards signs are inverted. Rest difference is home minus away. Neutral-site status is explicit; the intercept handles average home advantage without a redundant constant feature.

EPA and success use scrimmage run/pass plays including sacks, excluding kneels, spikes, administrative/no-play and special teams. Success means EPA > 0. Defense uses the opponent possession team's EPA and yards, so lower is better. Turnover differential counts eligible scrimmage interceptions and lost fumbles; special-teams turnovers are excluded. Scoring includes all final-score points. Team-game rates are averaged with equal game weights, rather than pooled play weights. Offense/defense yards are included as additional baseline features.

Prior-season team means regress 50% toward prior-season league means, then contribute four pseudo-games to current-season estimates. Missing franchise history falls back to prior-season league means. Recent EPA uses the last three current-season games plus the same prior. No prior data exists for 2018 Week 1; missing inputs remain NaN until the training-fitted mean imputer (all-empty columns use zero). Scaler and model fit only training rows. Ties contribute half a win to historical team ratings but have no binary target and are excluded from model scoring.

Schedules provide Eastern local kickoff clock times, normalized to UTC. Game results enter history only eight hours after kickoff, a conservative proxy because exact game-end timestamps are absent. This excludes overlapping ordinary games, but extraordinary suspensions lasting more than eight hours require manual review. Historical feature reconstruction uses revised present-day sources, not archived as-of snapshots; it cannot prove historical publication availability. Model outputs are experimental probabilities, not demonstrated calibrated confidence.

Historical backtest predictions are simulations. SQLite forecasts record genuine creation times, immutable payloads, model version and cutoff. Results can be updated after source corrections; forecast payloads cannot. Never load untrusted joblib artifacts.

## Reports and interface

The three Streamlit pages show upcoming schedules/forecasts, team ratings with actual scheduled matchup probabilities, and historical performance/calibration. Explicit refresh and generation buttons initiate work. No hypothetical predictions are logged. Historical CSV/Parquet and reliability PNG outputs are generated by backtest. See ENGINEERING_REPORT.md for measured results, coverage and unresolved limitations.

Data attribution: [nflverse](https://github.com/nflverse/nflverse-data), accessed through [nflreadpy](https://github.com/nflverse/nflreadpy). Consult upstream dataset licenses and usage conditions before redistribution.
