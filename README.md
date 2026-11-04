# NFL Game Prediction Engine — M8

Local experimental NFL regular-season winner model using nflverse, Python, logistic regression, Parquet and SQLite. Includes a separate simulation-only moneyline research lab; no real-money execution. CPU only; allow several GB of free disk space for initial play-by-play downloads. Python 3.11+ is required; Python 3.12 was verified on Linux. Windows 10/11 is the target, but a native Windows run has not been verified.

## Windows PowerShell: clean installation

With Python and Git installed:

```powershell
git clone --branch m8-moneyline-paper-lab https://github.com/atyo416/NFL_Predictions.git
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

## M2: statistical validation and data integrity

M2 preserves the M1 champion, reports and prediction database. Model Analysis displays **exploratory experiments**, separate from historical M1 benchmarks and genuinely issued official forecasts. No new model or calibrator is automatically deployed.

With the existing virtual environment active:

```powershell
python -m pip install -r requirements.lock.txt
python -m pip install --no-deps -e ".[test]"
python -m pytest -q
python -m nfl_predictor.cli update
python -m nfl_predictor.cli analyze
python -m streamlit run app.py
```

`update` adopts existing M1 caches into hashed, versioned generations without downloading them again. New downloads publish schedules, metrics and raw PBP together through an atomic season manifest. Old generations and all saved forecasts are retained. A corrupt cache raises an error instead of quietly using damaged data. To restore a previous verified generation: `python -m nfl_predictor.cli recover-cache --seasons 2026`. If no previous valid generation exists, use `python -m nfl_predictor.cli update --seasons 2026 --refresh` with Internet access. Each refresh retains history, so monitor disk usage. Legacy files can remain present; active manifests take precedence.

Feature construction caches by dataframe content and feature code, with a separate integrity checksum. For a damaged feature cache, run `python -m nfl_predictor.cli features --refresh`. Refresh never rewrites the original SQLite forecasts. Newly aggregated metrics also include eligible-play counts for low-coverage warnings; pre-M2 adopted metrics may lack those counts. Missing play-by-play warnings do not certify complete upstream data.

`analyze` uses the frozen `config/m2_protocol.json`. An alternate protocol can be passed with `--protocol PATH`. Baseline training, chronological calibration and evaluation are disjoint. Development folds evaluate 2022 and 2023 using earlier seasons; 2024–2025 repeats the M1 training window plus a separate 2023 calibration year. Those already-inspected years are **not an untouched test for new choices**. Use a future unexamined prospective period for independent confirmation.

Experiments compare logistic regression, finite-probability always-home and training home-rate baselines, pregame win percentage, sigmoid calibration and (with sufficient data) isotonic calibration. Seven feature groups are ablated individually. Paired season-week resampling gives accuracy/Brier/log-loss intervals and candidate-minus-champion intervals on aligned games. These assume independence across week blocks; repeated teams, limited seasons, exploratory subgroup searches and unadjusted multiple comparisons restrict inference. Coefficients and contribution charts are associations, not causal explanations.

Outputs go to `reports/m2/<content-key>/`; `latest.json` selects the dashboard run. The key includes data/features, configuration, module code, lockfile and runtime versions. Existing run outputs are checked before reuse. Each run contains model comparisons, calibration, ablation and error-analysis Markdown/CSV reports; coefficients, training correlations, prediction Parquet, incorrect-prediction CSV with feature/log-odds contributions, reliability diagram, immutable metadata and output checksums. Identical inputs/settings reproduce the measured artifacts; changed inputs create a separate run. M1 reports remain at their original paths. Run records include training/calibration cutoffs, evaluation periods, feature set, preprocessing, hyperparameters and code/runtime fingerprints. Concurrent cache publishers are atomic per generation but not serialized; avoid simultaneous refreshes of the same season.

The Model Analysis page includes a download button for incorrect predictions, uncertainty tables, seasonal results, calibration and experiment metadata. Prospective summaries read official forecasts and attached outcomes through read-only SQLite. Use the ordinary M1 refresh/predict workflow to attach verified outcomes; analysis itself does not modify forecasts or outcomes.

See [M2_ENGINEERING_REPORT.md](M2_ENGINEERING_REPORT.md), [data/leakage audit](docs/m2/DATA_LEAKAGE_AUDIT.md), and the generated reports. Neither exact historical publication timestamps nor original source vintages are available. Native Windows verification remains outstanding; all claimed execution checks were performed on Linux.

## M3: dynamic ratings and matchup context

M3 extends M2 with **experimental** Elo ratings, explicit schedule rest/bye features and a conservative QB evidence layer. The official M2 champion and saved SQLite forecast payloads remain unchanged.

With your existing virtual environment active and season data cached:

```powershell
python -m pytest -q
python -m nfl_predictor.cli ratings
python -m nfl_predictor.cli rankings
python -m nfl_predictor.cli compare-m3
python -m nfl_predictor.cli report-m3
python -m streamlit run app.py
```

`ratings` builds an immutable pregame/postgame history and all-32-team rankings. `rankings` is an alias that also prints the table. Both export Parquet and CSV to `data/ratings/<key>/`; `latest.json` selects the dashboard snapshot. A historical snapshot can be generated with `ratings --cutoff 2025-11-01T12:00:00-04:00`. The cutoff is timezone-aware; completed results enter only strictly before it. The seven-day prior snapshot determines previous-week ranks and weekly changes. These can include offseason regression if the interval crosses a season boundary.

Default Elo: initial 1500, logistic scale 400, K=20, home adjustment 50 (zero at neutral sites), offseason retention 0.67. Updates are equal and opposite, use the pregame expectation, and treat ties as half a win. First-source-season ratings are initialized without earlier history and are marked warmup. Kickoff snapshots precede equal-time eligible results. No postseason updates occur. Conflicting duplicate game results raise an error instead of double-counting. Exact duplicates are harmless.

`compare-m3` evaluates standard and margin Elo, M2+Elo, explicit rest/bye models and combinations against the original M2 logistic benchmark and baselines on identical games. It reuses M2's chronological folds and paired season-week uncertainty. `config/m3_protocol.json` freezes parameters; use `--protocol PATH` for a documented alternative. No automatic champion promotion occurs. Margin Elo caps both the margin input (42 points) and update multiplier (0.5–3), with a pregame winner-advantage correction; it remains experimental. Separate files compare Elo variants directly and against the pregame win-percentage baseline.

Rest days refer to target scheduled kickoff minus the latest eligible played kickoff in the same season. Missing previous games remain missing. Short rest is less than six days, extended rest more than ten days without an identified bye. Bye identification uses the **season schedule**, not elapsed rest alone: at least 16 team games, exactly one absent week in weeks 4–14, and the immediately following game week. Incomplete or ambiguous schedules remain unknown. Historical schedule revisions, extraordinary bye weeks and suspended games limit certainty. Individual indicators, joint features, an old-rest redundancy control, initialization sensitivity and descriptive post-bye results are exported. Joint rest models replace the old rest feature; none is automatically deployed.

### Quarterback data

Optional source refresh (Internet required):

```powershell
python -m nfl_predictor.cli update-qb --seasons 2024 2026
```

Raw depth charts, injuries and rosters are retained with source hashes/timestamps. Weekly historical depth charts and current timestamped snapshots have different schemas. Neither is automatically promoted to a verified pregame starter designation. Actual completed-game QB IDs provide only already-observed prior starters; they cannot identify that same game's pregame starter. No injury report means **unknown**, never healthy. Unverified/stale candidates are displayed explicitly as such. The inspected 2026 depth snapshots end in March, so they are stale for the November data snapshot.

If you possess independent timestamped pregame evidence, `import-qb --qb-file PATH` accepts a JSON list with these fields:

```json
[{
  "team": "LV", "player_id": "GSIS player identifier", "name": "Player name",
  "source": "Name and reference of independently reviewed report",
  "source_at": "2026-11-01T10:00:00-05:00", "observed_at": "2026-11-01T10:05:00-05:00",
  "classification": "verified_pregame", "availability_status": "unknown",
  "designation": "candidate", "game_id": "exact nflverse game ID", "season": 2026, "week": 9,
  "quality": "independently reviewed pregame evidence"
}]
```

This is a schema illustration, not a real designation. Supply actual evidence and IDs. `designation` must be `candidate` or `confirmed_starter`; timezone-aware source and observation timestamps must both precede the target cutoff, and observations cannot be future-dated. The software validates structure/timing, not the truth of supplied evidence. Retain the original report. Refreshes preserve imported verified evidence. Historical QB experiments require sufficient verified records for both teams and a known prior starter, and compare only matched samples. The inspected data does not satisfy that requirement; no QB improvement is claimed.

### Dashboard and reports

Team Power Rankings shows ratings, records, seven-day changes and history plotted at **result eligibility**, never before kickoff. It also exposes M3 comparisons, calibration and coverage. Team Comparison adds venue-specific Elo probability, rating differential, explicit rest/bye context and verified QB context for an actual scheduled matchup. These experimental displays never log official forecasts. Generate the snapshots/reports first; no background network work occurs on page load.

`report-m3` generates `M3_ENGINEERING_REPORT.md` from measured outputs and available verification evidence. Results live separately in `reports/m3/<key>/` with metadata and output checksums. Old M1/M2 reports are preserved. No native Windows execution has been verified; PowerShell commands follow the existing installation steps. Historical final-publication timestamps, source vintages and adequate historical pregame QB evidence remain unresolved. See the M3 engineering report for measured comparisons and the promotion decision. M4 is not implemented.

## M4: controlled nonlinear model experiments

M4 adds CPU-only sklearn histogram gradient boosting, controlled chronological selection, calibration, permutation diagnostics, and an additive candidate registry. It **retains the M2 logistic champion** and preserves M3 Elo, QB context, ratings and immutable official forecasts. Native Windows acceptance is still pending.

With your existing virtual environment active (no new dependencies required):

```powershell
python -m pytest -q
python -m nfl_predictor.cli train-m4
python -m nfl_predictor.cli compare-m4
python -m nfl_predictor.cli report-m4
python -m streamlit run app.py
```

The three M4 commands share one staged experiment pipeline: development selection, candidate fitting/registration and forward comparisons. `train-m4` therefore also produces comparison artifacts. Repeated identical calls validate and reuse the completed run. Training occurs only through explicit CLI commands, never while rendering Streamlit. `report-m4` additionally generates `M4_ENGINEERING_REPORT.md`. Source seasons must already be cached; these commands do not refresh or repeatedly reprocess raw PBP. Matchup features have a separate content/code/checksum cache.

`config/m4_protocol.json` freezes four conservative configurations before results are examined: learning rates .05/.1, depths 2/3/4, leaf limits 4/7/15, 100 iterations, minimum leaf size 20 and L2=1. Random state is 42. Internal early stopping is **disabled**; no shuffled internal validation is used. Native NaN handling is fitted on training rows without tree scaling or imputation. Fit/scoring wrappers cap CPU threads (default two), including serialized/reloaded models. A GPU is neither used nor required. Optional XGBoost was not installed or evaluated; its additional native dependency and Windows acceptance are deferred, rather than blocking sklearn comparisons. This is not a claim that an XGBoost installation attempt failed.

Development folds train 2018→validate 2019, train 2018–2019→validate 2020 and train 2018–2020→validate 2021. Selection minimizes equal-season validation Brier, then log loss, then configuration name; accuracy is not optimized. The code prevents M4 selection using seasons after 2021. Hyperparameter selection never uses 2024–2025 outcomes. The existing forward folds retain their separate base/calibration/evaluation periods. The first calibration year is also 2021 development data, so it is not independent evidence for choosing a calibration method. All calibration performance is scored on strictly later games.

Candidate comparisons include original logistic, logistic+Elo, standard/margin Elo, pregame win percentage, historical home rate, all four boosting configurations, the development-selected model, selected features and sigmoid/isotonic variants. Feature sets test M2 alone, standard Elo differential, margin Elo differential, venue-adjusted relative strength probability, explicit M3 rest/bye replacement and six controlled interactions. Team-perspective EPA/success features are computed with the original chronological rating function; they are not reconstructed from matchup differences. Historical QB data is excluded from the main comparison because verified pregame coverage remains insufficient. M3's evidence layer remains intact.

Interactions pair home offense with away defense and vice versa, pair success rates the same way, compare recent and long-term offensive differences, and multiply scaled Elo and scoring differences. They are experimental mathematical inputs, not assumed causal effects. Forward permutation importance shuffles individual features and whole groups, reports repeated loss changes, and is labeled exploratory. Correlated features can mask redundant information or yield unrealistic permutations; importance must not become post-hoc tuning against 2024–2025. M2 standardized coefficients are exported alongside it.

Model Analysis now displays M4 comparisons, calibration, confidence buckets, selection trials, training/calibration/forward gaps, feature-importance charts and candidate metadata. All five existing pages remain functional. Selecting a model in a diagnostic chart never changes the champion or logs forecasts. Previously examined 2024–2025 remains exploratory. Future independent confirmation must use genuinely issued prospective forecasts rather than retrospectively manufactured issuance dates.

### Candidate registry and explicit activation

Candidate joblib files and metadata live under ignored `models/registry/candidates/<version>/`. Each immutable entry records version, algorithm, feature schema/list/configuration, parameters, training/calibration cutoff, dataset fingerprint, report reference and artifact checksum. Serialized M1/M2 models remain readable. Report bundles under `reports/m4/<key>/` include registry metadata/checksums without committing trained model artifacts. Load only trusted local joblib files; integrity hashes do not make an untrusted pickle safe.

M4 **does not activate any candidate**. A future operator may use the explicit workflow below only after completing a documented statistical review and native Windows acceptance. JSON assertions do not prove that the review occurred; retain the actual evidence.

```json
{
  "candidate_version": "exact registered version",
  "decision": "approve",
  "reviewer": "named reviewer",
  "rationale": "documented forward probability-quality and stability decision",
  "windows_verified": true,
  "artifact_sha256": "checksum from candidate metadata",
  "evidence_report": "path to an existing review report (relative to this JSON or absolute)",
  "evidence_sha256": "SHA-256 of that review report"
}
```

```powershell
python -m nfl_predictor.cli activate-model --decision-file reviewed_decision.json
python -m nfl_predictor.cli rollback-model --event-id EVENT_ID_FROM_ACTIVATION
```

Activation verifies the exact reviewed artifact and evidence file, saves the previous champion to an immutable hash-named backup, records a prepared event, then atomically replaces the production artifact. Rollback verifies the current champion corresponds to that event and restores the preserved bytes. Both old and M4 feature adapters are supported when scoring upcoming games; M4 uses Elo known at **issuance time**, not results becoming available before a future kickoff. Existing SQLite payloads are never rewritten. Avoid concurrent activation/rollback commands. If interrupted after replacement, a `prepared` event can still support rollback when artifact hashes match. The existing `train` command remains an explicit logistic production refit; it is distinct from M4 candidate training.

All candidate results remain exploratory. A small historical accuracy gain, an unadjusted importance score or a single favorable interval is insufficient for promotion. Windows testing, historical source vintages, final-publication timestamps, limited seasons, repeated-team dependence and multiplicity remain limitations. M5 and M7 are not implemented.

The installed sklearn 1.9 binning routine cannot fit an entirely missing training column. M4 excludes such columns based only on training rows and records them in candidate metadata; they stay excluded even if later values become available. Partially missing columns still use native tree routing. An entirely empty feature matrix uses an intercept-only constant. No source statistics are invented. If a cached report exists but its ignored candidate artifacts are absent/corrupt, `compare-m4 --refresh` creates a new versioned run with identical parameters and an explicit rebuild revision, preserving the previous evidence.

## M5: historical windows and recency weighting (at-risk development)

M5 expands cached source support to **1999–2026** and compares earliest-label policies W1=2018, W2=2013, W3=2008 and W4=1999. The original M2 champion, M4 registry, official SQLite forecasts and Elo snapshots remain unchanged. Every M5 model is explicitly activation-blocked. Native combined M4/M5 Windows acceptance remains pending; at-risk development is not promotion approval.

```powershell
python -m nfl_predictor.cli update-history --start 1999 --end 2017
python -m nfl_predictor.cli audit-history
python -m nfl_predictor.cli compare-history
python -m nfl_predictor.cli report-m5
python -m pytest -q
python -m streamlit run app.py
```

Historical downloads require Internet. They operate one season at a time, disable nflreadpy's accumulating memory cache, and publish through the existing atomic manifest framework. Interrupted runs resume by verifying/skipping previously committed seasons. Use `--refresh` only to deliberately retrieve a revised season range; previous generations stay available for `recover-cache`. Required-column errors are actionable; unsupported metrics are never silently filled with zeros. Each new manifest records schemas, null rates, source and retrieval time, hashes, row/game counts, processing version, distribution summaries and completeness. `reports/history_audit/source_audit.json` preserves detailed audits; its CSV provides a compact season summary.

Normal existing M1–M4 commands continue loading **2018–2026 only**. Adding older manifests does not silently change their early-season priors or Elo initialization. `compare-history` explicitly loads the expanded compact schedules/metrics. Raw PBP is not reprocessed for each model. Statistical feature caches are hashed **per season**, with only current/prior-season context; Elo replay uses the compact full schedule. Existing source generations, feature caches and official models are retained.

### Historical time and feature compatibility

The inspected 1999 schedule/PBP sources have no kickoff clock, start_time or time_of_day. A date-only row uses midnight Eastern as a labeled **lower bound** for pregame features and next day 08:00 Eastern as conservative result availability. No actual kickoff time is inferred. These bounds deliberately exclude same-day results. Known-clock rows retain source scheduled times, which are not certified actual play-start timestamps. Historical final-publication times and original source vintages remain unavailable.

Because exact rest is unavailable for date-only rows, all main window experiments use an explicitly labeled common set: original M2 features **minus rest**, plus pregame standard Elo for shallow HGB. Unknown venue remains missing. All windows share the same expanded pregame/Elo history so only the training-label start changes. W1-common is therefore **different from the exact original full-feature reference**. Separate original M2/M4 references preserve their 2018 history and reproduce their original metrics. Never attribute a reference/common feature difference to additional training records.

The original four-game prior and 50% offseason regression remain fixed. 1999 has no 1998 prior, and newly appearing Houston has no pre-2002 team history; league fallback/missing values are explicit. No current-game or future-game statistics enter earlier features. Source EPA is itself a modern retrospective estimate; consistent field names do not establish stable cross-era calibration. Passing production is net eligible pass-play yards (including sacks), not official gross passing yards. Descriptive passing/rushing totals are audited, not added to the fixed feature set. Early source PBP gaps, ties, canceled games and schedule revisions remain visible in the audit.

### Staged experiments and weighting

`config/m5_protocol.json` freezes shallow HGB at M4's selected parameters. Uniform windows are compared on development validation years 2019/2020/2021. The top two windows **per algorithm** receive predefined half-lives of 3, 5 and 8 years; one primary window/weight policy is selected using those development years. No tree, feature-group or prior-weight retuning occurs. 2024–2025 remains repeatedly examined exploratory evidence, never final selection authority.

Weights are `0.5 ** (age_in_years / half_life)`, with age relative to each historical training cutoff and a 365.25-day year. They normalize to mean one, preserving total loss scale within each window at fixed regularization; effective sample size is reported. Larger windows still alter sample size and therefore relative regularization. No rows are duplicated. Logistic uses training-only mean imputation, **weighted StandardScaler and weighted logistic fitting**; HGB receives sample weights directly. Means used for imputation remain unweighted by design. Calibration uses a disjoint intervening season and is evaluated only forward, for development-selected policies. Neither calibration nor weighting variants become official models.

Reports separate three comparisons: `comparison.csv` versus the exact original logistic champion; `within_algorithm.csv` versus same-algorithm W1-common; `decay_effects.csv` versus the **same-window uniform** policy. `vs_original_boosting.csv` compares expanded HGB against the M4 reference, and `elo_warmup.csv` isolates 1999 versus 2018 Elo initialization. `season_phase.csv` provides weeks 1–3 versus later diagnostics without tuning the four-game prior. All compared models use identical evaluation games. Paired week-block intervals are unadjusted exploratory diagnostics; repeated teams, correlated games, few seasons and many comparisons prevent a single favorable interval from establishing superiority.

Model Analysis includes **Historical Training Analysis** with coverage, window/decay comparisons, seasonal accuracy/Brier, calibration, selected experimental policies and limitations. It only reads saved outputs; no training occurs during rendering. M5 registry metadata records window, half-life, cutoff, normalization, effective sample size, algorithm, feature schema, hashes and evaluation. Existing activation/rollback code remains compatible, but explicitly refuses M5 candidates during this milestone.

### Combined native Windows acceptance

On a genuine Windows 10/11 machine with Python 3.12, follow the existing installation instructions and retain your original local data/model/forecast backups. `scripts/windows_acceptance.ps1 -Full` runs the combined command checklist; `scripts/verify_local_acceptance.py` records platform evidence, tests scoring in a **temporary database copy**, and verifies existing model/forecast files are unchanged. It never activates a candidate. A missing original champion, absent caches, skipped upcoming games or incomplete manual UI/RAM checks remain unrun acceptance items. For data processing, run with enough disk space for retained generations and record actual Windows RAM/runtime. Start Streamlit manually and verify all five pages and Historical Training Analysis.

These scripts were provided for later native execution; Linux checks do not certify Windows. See `M5_ENGINEERING_REPORT.md` for actual measured results and outstanding acceptance limitations. Downloaded raw datasets and trained binaries remain ignored by Git; use the CLI to reproduce local caches. M5 behavior remains available alongside M6.

## M6: opponent adjustment and evidence-qualified player context

M6 preserves the M2 production champion and fixed M5 experimental baseline: shallow HGB, labels from 2008, uniform weights. No window or boosting search is added, and every new candidate remains activation-blocked.

```powershell
python -m nfl_predictor.cli build-adjusted-efficiency
python -m nfl_predictor.cli audit-personnel
python -m nfl_predictor.cli compare-m6
python -m nfl_predictor.cli report-m6
python -m pytest -q
python -m streamlit run app.py
```

These commands use existing 1999–2026 caches. Run M5 ingestion first if seasons are missing. Opponent snapshots are source/configuration/code/cutoff-keyed and cached per season. QB summaries read only relevant cached PBP columns, one season at a time; model experiments reuse compact matrices. The UI never downloads or trains models. `build-adjusted-efficiency --cutoff 2026-11-03T08:00:00-05:00` limits snapshots to information eligible at that explicit cutoff. Original caches, forecasts, registry entries and Elo histories are retained.

### Opponent-adjustment model

`config/m6_protocol.json` fixes the additive model `observed offense = league mean + offensive strength + opposing defensive-allowed strength`. Eight simultaneous Jacobi iterations apply four-game shrinkage, half-weight offseason retention, 0.5 damping and bounded opponent/strength contributions (EPA ±0.5; success ±0.2). Lower defensive-allowed strength is stronger. All observations, prior-season means and league references are filtered **before** solving at the target cutoff. Future opponent improvement cannot rewrite an earlier snapshot. Same-time and delayed results remain ineligible until strictly earlier availability. First-season missing history produces a neutral algorithm prior, not observed zero statistics.

A preserves M5 raw features. B replaces four season EPA/success differences, while retaining M5 recent EPA, yards and other controls. C adds adjusted measures to raw. D uses adjusted home/away matchup pairs; D2 uses overall differential separately, avoiding exact linear redundancy. Fixed C ablations test Elo/offensive/defensive contribution. Two/eight-game adjustment prior sensitivity is reported only on 2019–2021 development periods; it never selects a new default against 2024–2025. All candidates use identical eligible evaluation games; the already-examined years remain exploratory.

### QB performance and availability

The player-performance cache aggregates identified prior dropbacks, including sacks and QB scrambles, excluding kneels/spikes and missing EPA. GSIS identities persist across team changes and multiple passers per game. A passer role on a play is performance context, not a roster-position or starter designation. EPA and success pool current/prior-season eligible samples and shrink with 80 league-prior dropbacks. Recent EPA uses the last three eligible player-games. Career samples provide experience; `1/sqrt(n+80)` is an uncertainty index, not calibrated confidence. Rookies/missing recent performance stay unknown. Advanced fields such as CPOE are descriptive when present, not fabricated historical inputs.

The original M3 QB layer is retained. M6 requires stronger named references, positions and explicit forecast cutoffs; old unverified depth/roster/injury data is **never automatically upgraded**. Actual previous starters are historical observations only. Contemporary NFL injury/depth data without provable publication timing cannot enter a historical verified experiment.

To import independently reviewed evidence, create a JSON list and run:

```powershell
python -m nfl_predictor.cli import-personnel --evidence-file reviewed_personnel.json
```

Example **schema only**, not a real designation:

```json
[{
  "game_id": "exact nflverse target game ID", "team": "LV", "player_id": "GSIS player ID",
  "position": "QB", "source_name": "Independently reviewed team report",
  "source_reference": "URL or retained source document reference",
  "source_at": "2026-11-03T10:00:00-05:00", "observed_at": "2026-11-03T10:05:00-05:00",
  "forecast_cutoff": "2026-11-03T11:00:00-05:00", "availability": "likely_starter",
  "quality": "reviewed timestamped evidence", "verification_status": "verified_pregame",
  "is_starter": true, "coverage_groups": []
}]
```

Supported availability statuses: `confirmed_starter`, `likely_starter`, `questionable`, `ruled_out`, `unknown`. Verification classes: `verified_pregame`, `retrospective`, `unverified`. Verified claims require timezone-aware source and observation times strictly before both the declared and actual feature cutoffs, and a nonempty reference. The declared cutoff must already have occurred at the feature cutoff. Unknown timestamps remain unverified; equally recent conflicts remain unknown. A later ruled-out report supersedes an older starter claim. Code validates recorded assertions, not authenticity of user-supplied sources; retain the underlying documents.

Position groups OL, WR, RB, TE, DL, LB and DB are supported. `is_starter` must reflect independently established role information, not current-game participation. `coverage_groups` may name a group **only if the cited verified report actually provides complete relevant coverage**. Otherwise its unavailable-starter count remains unknown. Even with complete scope, unknown or conflicting unavailable-player roles cannot become zero absences. Missing injury reports never imply healthy players. Initial F uses OL counts only; no arbitrary point-spread/player-impact values are assigned.

```powershell
python -m nfl_predictor.cli snapshot-personnel --game-id ACTUAL_UPCOMING_GAME_ID
```

Snapshots record actual creation time and are allowed only before a genuine unstarted target kickoff. They are immutable, checksummed **context records**, not official winner forecasts; revised snapshots are separate files. Historical evidence imported today may support a labeled reconstruction, never backdated genuine issuance. Original SQLite forecasts stay unchanged.

Personnel E/F experiments require matched verified samples, minimum 100 training/50 evaluation games and 50% eligible game coverage by default. G uses fixed B+QB+OL only if both independent studies qualify. A skipped experiment is reported with counts/coverage; no fabricated starters, healthy assumptions or unmatched full-season baseline comparison is allowed.

### Dashboard, reports and Windows

Team Comparison adds raw/adjusted EPA, success, opponent schedule context, previous observed QB, verified expected context and position-group unknowns. Model Analysis adds M6 comparisons, noncausal permutation diagnostics, coverage, calibration and model metadata. Source player statistics/participation/snap-count schemas were inspected; complete historical **verified pregame** availability was not established. See `M6_ENGINEERING_REPORT.md` for measured successful and unsuccessful experiments.

The brief reports M5 native acceptance; M6's Linux tests do not constitute a new genuine Windows run. The corrected file-based PowerShell preflight remains in place. On Windows Python 3.12, run the full test suite, both feature/analysis commands, verify all existing pages, champion predictions, registry loading and persistence using the acceptance checklist. M7 is not implemented.


## M7: chronological ensembles and separate experimental forecasts

The official M2 champion and its forecast SQLite remain unchanged. M7 uses the
established logistic architecture, fixed M5 2008-onward/uniform shallow boosting,
and fixed M3 margin Elo. M6 adjusted features and personnel models are excluded.
Every M7 base refit and ensemble remains experimental and activation-blocked.

```powershell
python -m nfl_predictor.cli build-ensemble-predictions
python -m nfl_predictor.cli compare-m7
python -m nfl_predictor.cli report-m7
python -m nfl_predictor.cli forecast-ensemble
python -m nfl_predictor.cli grade-ensemble
python -m pytest -q
python -m streamlit run app.py
```

Reuse your existing 1999–2026 source caches (see M5 ingestion above). These commands
never retrain or replace the official model. The first historical run fits annual
base models; later ensembles reuse compact predictions. `forecast-ensemble` reads
fitted artifacts and never trains them. The default cutoff is the actual current
time; an explicit aware cutoff is supported, for example:

```powershell
python -m nfl_predictor.cli forecast-ensemble --cutoff 2026-11-03T17:00:00-05:00
```

That example is valid only after that cutoff and while eligible games are still
unstarted; it never backdates issuance. `--game-id` restricts issuance to an actual
upcoming game. Historical commands reject `--cutoff` because their fold calendar
is fixed. The `grade-ensemble` command appends eligible results and revised result
events separately; forecasts never change.

The pre-implementation calendar and candidate definitions are recorded in
[docs/m7/PROTOCOL.md](docs/m7/PROTOCOL.md). Each historical target season uses
base models trained through the preceding season. M2 retains original full
features/2018 history; M5 retains common features plus standard Elo warmed from
1999, while standalone margin Elo retains its original 2018 replay origin.
Consequently M7's annual HGB reference differs from M5's frozen-2022 evaluation.
Only matched M7 comparisons isolate the ensemble contribution.

OOS seasons 2019 onward supply meta-training rows. Development evaluation uses
2022–2023, with separate earlier meta and calibration years; 2024–2025 is
repeatedly examined exploratory evaluation. The eight raw ensemble methods are
equal weights, boosting/Elo average, three predefined fixed-weight triples,
constrained Brier-optimized weights with fixed shrinkage, and two regularized
three-input stackers (probabilities/log odds). Raw/sigmoid/isotonic alternatives
make up to 24 policies. Equal-season development Brier, then log loss and name,
selects the policy. Later annual fits update parameters under that frozen policy
using earlier eligible outcomes. No future-game outcomes choose that game's
weights, calibrator or policy. Confidence intervals are exploratory and are not
adjusted for selecting among many correlated candidates.

The base matrix includes actual generation time, retrospective classification,
per-game cutoffs, base versions/training times, source fingerprints, missing flags
and outcomes. Ties/incomplete/unavailable labels and missing predictions are
reported explicitly; missing probabilities never become 0.5. Complete earlier
rows are required for fitting and aligned comparisons.

Actual experimental forecasts are separate append-only checksummed JSON files in
`data/m7/experimental_forecasts`, with immutable game/version/cutoff identities,
base probabilities/checksums, calibration, actual creation time and provenance.
A repeated identical request reuses the saved record. Changed probabilities or
sources at the same identity raise an error; use a new cutoff/version for a
revision. Separate result events support later grading. Multiple revisions of one
game are correlated and must not be counted as independent forecast evidence.
The original SQLite database is never opened by M7 issuance or grading.

Model Analysis adds **Ensemble Analysis**, including base/ensemble comparisons,
weights, calibration, disagreements, fold boundaries and genuine forecast records.
Team Comparison shows saved experimental probabilities only when their referenced
artifacts verify; unavailable results remain unavailable. The existing official
champion estimate has its own labeled cutoff. Rendering neither trains nor issues
forecasts. Reports and source code are committed; downloaded data, local SQLite
and fitted joblib files remain ignored, so a clean ZIP requires cache reproduction.

On genuine Windows Python 3.12, run `.\scripts\windows_acceptance.ps1 -Full`
for combined M6/M7 processing and then inspect all pages, CPU and peak RAM.
M6/M7 native Windows acceptance remains outstanding when only Linux checks are
reported. See [M7_ENGINEERING_REPORT.md](M7_ENGINEERING_REPORT.md) for measured
results, preservation evidence and limitations. No M8 features are implemented.


## M8: moneyline market research and paper simulations

M8 preserves existing M2/M5/M7 models, official SQLite and issued forecasts. Its
own append-only database is `data/m8/lab.db`. Quotes and paper wagers cannot be
updated or deleted; settlements and corrections append revision events. Upgrading
an existing installation should retain its `data/` and `models/` folders. M8 never
trains models or automatically replaces M7's frozen `E1_equal__raw` policy.

```powershell
python -m nfl_predictor.cli audit-odds
python -m nfl_predictor.cli compare-market
python -m nfl_predictor.cli issue-paper-bets --dry-run
python -m nfl_predictor.cli issue-paper-bets
python -m nfl_predictor.cli settle-paper-bets
python -m nfl_predictor.cli report-m8
python -m nfl_predictor.cli demo-m8
python -m streamlit run app.py
```

No real sportsbook bet-placement, accounts or payments exist. All stake/P&L is in
simulated units. Opening **Betting Lab** only reads local data. Refreshing/importing
odds never trains a model. No prices or returns are invented if real data is absent.

### Optional live prices

The read-only Odds API v4 adapter requests NFL `h2h`, region `us`, American prices.
Set a personal key in the current local PowerShell process, then explicitly fetch:

```powershell
$env:ODDS_API_KEY = "YOUR_LOCAL_KEY"
python -m nfl_predictor.cli fetch-odds
```

Never put a real key in committed files or share it in chat. No key is required for
tests, imports, saved reports or `demo-m8`. The cloud runtime had no key and blocked
the direct official guide; current official provider GitHub examples were inspected
for endpoint/schema/quota. See `docs/m8/PROVIDER_REVIEW.json`. A network draft alone
does not apply permissions: cloud users must review/save and publish environment
settings. This does not affect ordinary Windows Internet access.

Default cooldown is five minutes, with at most two short bounded attempts. Safe
quota headers are saved when returned; balances are unknown until a real fetch.
Unchanged responses/markets deduplicate, while every request receipt remains
traceable. Provider errors do not erase earlier quotes or affect prediction pages.
No paid historical API fetch is implemented.

### Offline and historical imports

```powershell
python -m nfl_predictor.cli import-odds --odds-file reviewed_quotes.csv
python -m nfl_predictor.cli import-odds --odds-file saved_v4_response.json --rules-file reviewed_rules.json
```

CSV uses **two selection rows per coherent bookmaker market**, with required columns:
`provider,bookmaker,event_id,market,selection,price,odds_format,home_team,away_team,
kickoff,season,snapshot_at,quote_at,source_reference`. All dates must be timezone
aware. Optional rules columns: `scope,tie_rule,cancel_rule,reschedule_rule,
rules_reference`; optional closing columns: `closing_status,closing_reference`.
Use `--source-kind unverified` for unverified provenance. `verified_archive` is an
operator assertion requiring genuine timestamped evidence, not software
verification of a source's authenticity. Actual import time is never backdated.

`tests/fixtures/m8/historical_example.csv` is **artificial**, not NFL price history;
import it only with `--source-kind synthetic`, preferably in a separate demo copy.
The JSON fixture declares itself synthetic and cannot silently be promoted by an
import flag. `demo-m8` exercises parsing, matching, EV and settlement in an isolated
temporary database and writes `reports/m8_demo/SYNTHETIC_DEMO.json`; it does not add
quotes/wagers to the real lab or claim actual model/market performance.

API responses do not establish bookmaker house rules. For actual paper issuance,
retain reviewed, applicable rule evidence. Example **schema only**, not a claim
about any real bookmaker:

```json
{"bookmaker_key": {
  "scope": "game_including_overtime",
  "tie_rule": "push",
  "cancel_rule": "manual_review",
  "reschedule_rule": "manual_review",
  "rules_reference": "retained genuine rules URL/document applicable to this market"
}}
```

Scope defaults to unknown. Unknown tie rules, regulation-only/three-way markets
or ties treated as losses cannot use our binary probabilities for paper issuance.
Only documented tie push/void rules are supported for issuance. Cancellations and
rescheduling with unknown rules remain in review. Corrected final scores append
new settlements; original quoted odds, model probability and stake never change.
An explicit audit correction is available:

```powershell
python -m nfl_predictor.cli void-paper-bet --wager-id EXACT_ID --reason "Documented correction reason"
```

### Temporal and statistical contract

Read `docs/m8/PROTOCOL.md`. Exact team aliases/designated sides, season and kickoff
within five minutes determine matching. Ambiguous/reversed/rescheduled/duplicate
events need review. Both sides for no-vig must come from the same market object.
No-vig is proportional normalization, not a true probability. EV `p*D-1` is a
conditional binary/no-tie scenario; probability edge in percentage points is a
separate quantity. ±2/±5-point sensitivity scenarios are not confidence intervals.

Quotes, captures and forecast creation/information must precede the decision and
kickoff. Default freshness: 15 minutes for quotes, 24 hours for forecast information.
Market cohorts use 24h/6h/1h lead times with one-sided earlier windows of 15/10/5
minutes; later quotes are excluded. Every probability comparison uses identical
eligible games and one selected bookmaker per game/cohort, never each price update
as an independent game. Prices are not assumed executable. Model estimates are not
called profitable merely because EV is positive.

The default paper policy is champion logistic, EV strictly greater than 3%, and one
unit. The first eligible book follows fixed priority then lexical identity; choose
the higher-EV side, home on ties. Optional `--model-family boosting` or `ensemble`,
`--ev-threshold 0`/`0.03`/`0.05`, and `--cohort manual`/`24h`/`6h`/`1h` create distinct
preregistered strategy versions. No threshold is optimized using evaluated returns.
No `--cutoff` is accepted for paper issuance: it always records actual current time.
Repeated opportunity issuance reuses the first immutable wager. Dry run saves no
wagers; source/reference audits may be populated.

Genuine market benchmarking requires genuinely issued predictions and observed
prices. Optional historical reconstruction uses:

```powershell
python -m nfl_predictor.cli report-m8 --reconstructed
python -m nfl_predictor.cli reconstruct-paper-bets --reconstructed
```

Genuine archived odds are required. Existing M7 kickoff-cutoff predictions are too
late for earlier cohorts. Reconstruction performs inference using frozen annual
M7 artifacts with **new decision-cutoff features**, without fitting any model;
its logistic output is a historical M2-architecture refit, not the official issued
champion forecast. The frozen M7 policy must still match. 2024–2025 remains
exploratory; reconstructed decisions are never labeled genuinely issued wagers.

Report ROI is settled profit / settled stake including push/void refunds, excluding
pending stakes; it is undefined without settlements. Drawdown aggregates equal-time
results before updating equity. Compare models/books/thresholds/seasons/cohorts
separately. Multiple strategies on one game are correlated exposures. CLV requires
an explicitly evidenced final pregame price within ten minutes, same bookmaker and
selection; merely last observed is not verified closing, and CLV does not prove
profitability. Real market metrics remain unavailable without genuine matched data.

### Combined native Windows verification

On genuine Windows Python 3.12, use the M8 checklist:

```powershell
.\scripts\windows_m8_acceptance.ps1 -Full
```

This preserves accepted model selections while checking M6 data, existing M7
forecast artifacts, all tests, M8 offline fixtures, the ledger and all six pages.
Live API fetching is optional and costs quota only when explicitly requested:
`.\scripts\windows_m8_acceptance.ps1 -Full -LiveOdds`. The older M7 acceptance
script remains available unchanged; its historical model comparisons can refit
research models, so the M8 checklist avoids those selection commands. Start the
UI manually, inspect all tabs and record actual Windows RAM/runtime. Linux checks
do not establish native M6/M7/M8 Windows acceptance.

See `M8_ENGINEERING_REPORT.md` for actual coverage, tests, ungraded/missing data and
limitations. Existing source PBP gaps and retrospective data-vintage assumptions
remain. M9 is not implemented.
