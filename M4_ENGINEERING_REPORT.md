# M4 engineering report

## Baseline and preservation

M4 extends the established M3 implementation. The actual starting suite passed 62 tests on Linux/Python 3.12. The original M2 logistic production artifact, official forecast database, Elo ratings, source caches and historical reports are preserved. No destructive database migration was introduced; the candidate registry is an additive file store. Baseline fingerprints are recorded in docs/m4/BASELINE.json. No candidate was activated.

Recorded champion metadata: `{"version": "20261103T043653-6d77120a", "features": ["off_epa", "def_epa", "scoring", "turnover", "off_success", "def_success", "win", "off_yards", "def_yards", "recent_off_epa", "recent_def_epa", "rest", "neutral"], "training_seasons": [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026], "training_cutoff": "2026-11-02T09:20:00+00:00"}`. Chronological logistic comparisons reconstruct the original training windows rather than evaluating the later production refit retrospectively.

## Algorithms and resource bounds

Primary nonlinear estimator: sklearn HistGradientBoostingClassifier, log-loss objective, random_state=42. Every fit disables internal early stopping; no random internal validation split is used. Native partial-missing routing is learned only from training rows; trees need neither mean imputation nor scaling. The installed sklearn 1.9 binning routine fails on all-empty columns, so they are excluded using training rows only and recorded per artifact. If every input is empty, an intercept-only constant provides the training-prior prediction; later data cannot activate a previously excluded column. Named feature lists, parameters, cutoff, dataset/code fingerprints and calibration are serialized with the fitted predictor. A wrapper limits fitting and scoring to the configured CPU thread count, including reloads. No GPU is required.

Optional XGBoost: Deferred optional comparison: not installed; no native Windows verification. M4 uses sklearn without adding a second native dependency. This is a scope/verification limitation, not a claim that installation was attempted and failed. Two or more controlled nonlinear configurations are supplied by sklearn.

## Features and leakage

The original M2 features remain intact. Additional feature sets test pregame standard Elo difference, margin-adjusted Elo difference, venue-adjusted relative Elo probability, M3 rest/bye replacement, and six explicit matchup interactions. Team-perspective offense/defense EPA and success ratings are computed with the same strict pregame cutoff and four-game previous-season shrinkage as M2; they are not reconstructed from differences.

Interaction definitions: home offensive EPA × away defensive EPA allowed; reverse pairing; home offensive success × away defensive success allowed; reverse pairing; recent-offensive-EPA difference minus long-term difference; (standard Elo difference / 400) × scoring differential. Signs/scales are model inputs, not claimed causal advantages. The interaction experiment adds them to M2+Elo, and group permutation diagnoses their conditional influence.

Elo replay uses only results eligible before each kickoff. Live M4 feature preparation explicitly snapshots ratings at issuance cutoff rather than allowing intervening outcomes before future kickoff. QB features remain excluded from all main comparisons. M3 context, normalized evidence and leakage safeguards are preserved. Historical eight-hour availability proxies, corrected sources and revised schedules still limit true point-in-time replay.

## Controlled optimization

The protocol was saved before M4 results were examined. Four predefined configurations vary learning rate (.05/.1), depth (2/3/4), leaves (4/7/15) at 100 iterations, minimum leaf size 20 and L2=1. Development folds are 2018→2019, 2018–2019→2020 and 2018–2020→2021. Selection uses equal-season mean validation Brier, then mean log loss, then configuration name. Accuracy is reported but not optimized. Selected: **shallow**.

| configuration | validation_brier | validation_log_loss | validation_accuracy |
| --- | --- | --- | --- |
| shallow | 0.229965 | 0.652613 | 0.615947 |
| conservative | 0.233505 | 0.661823 | 0.618252 |
| larger | 0.238834 | 0.675358 | 0.611716 |
| faster | 0.241455 | 0.684646 | 0.612257 |

The selection function never examines later outcomes. Reported forward folds preserve M2/M3 training/calibration/evaluation periods. Selection through 2021 precedes every evaluation; the first calibration period is also 2021, so it is not an independent model-selection validation set. Models are trained on earlier periods, calibrators on a distinct later season, and all scoring occurs after both. No chronological early-stopping machinery is required because iteration counts are fixed.

## Measured 2024–2025 results (previously examined)

| model | accuracy | brier | log_loss |
| --- | --- | --- | --- |
| elo_margin | 0.651934 | 0.219134 | 0.627875 |
| elo_only | 0.639042 | 0.224492 | 0.639773 |
| hgb_config_conservative | 0.650092 | 0.220177 | 0.630451 |
| hgb_config_faster | 0.626151 | 0.226551 | 0.645176 |
| hgb_config_larger | 0.657459 | 0.222335 | 0.636630 |
| hgb_config_shallow | 0.661142 | 0.217426 | 0.624715 |
| hgb_interactions | 0.650092 | 0.218354 | 0.626884 |
| hgb_isotonic | 0.661142 | 0.221302 | 0.656650 |
| hgb_m2_only | 0.659300 | 0.219418 | 0.628963 |
| hgb_margin_elo | 0.664825 | 0.218380 | 0.626795 |
| hgb_relative_strength | 0.664825 | 0.217715 | 0.625594 |
| hgb_rest | 0.662983 | 0.217501 | 0.624989 |
| hgb_selected | 0.661142 | 0.217426 | 0.624715 |
| hgb_sigmoid | 0.646409 | 0.219496 | 0.629086 |
| historical_home_rate | 0.535912 | 0.248721 | 0.690586 |
| logistic | 0.644567 | 0.220954 | 0.631279 |
| m2_elo | 0.642726 | 0.220227 | 0.630039 |
| pregame_win_percentage | 0.657459 | 0.222769 | 0.637090 |

Selected candidates: paired Brier differences versus logistic

| model | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- |
| hgb_interactions | 0.218354 | -0.002600 | -0.007936 | 0.002960 | 543 |
| hgb_isotonic | 0.221302 | 0.000348 | -0.005527 | 0.006823 | 543 |
| hgb_selected | 0.217426 | -0.003528 | -0.009152 | 0.002531 | 543 |
| hgb_sigmoid | 0.219496 | -0.001457 | -0.006334 | 0.003783 | 543 |

Full paired accuracy/Brier/log-loss intervals and candidate differences: see the run MODEL_COMPARISON.md and comparison.csv. Identical games and targets are required for all direct comparisons. 2024–2025 is exploratory reuse, not an untouched test, and apparent gains cannot independently justify promotion.

## Calibration, interpretation and overfitting

Sigmoid and conditionally isotonic calibration reuse M2 chronological fitting guards. Probability buckets, confidence buckets, reliability plots and identifiable calibration intercept/slope are generated. No calibrator is selected as a production default. All registry entries are experimental.

Held-out individual and grouped permutation loss increases are reported for selected boosting and interaction variants, with multiple fixed-seed repeats. M2 standardized logistic coefficients are exported for comparison. Correlations and off-manifold permutations limit causal interpretation.

| model | group | brier_increase |
| --- | --- | --- |
| hgb_selected | group:offense | 0.007632 |
| hgb_selected | feature:off_success | 0.006944 |
| hgb_selected | feature:elo_difference | 0.005588 |
| hgb_interactions | group:elo | 0.005580 |
| hgb_interactions | feature:off_success | 0.005150 |
| hgb_selected | group:elo | 0.005084 |
| hgb_interactions | feature:elo_difference | 0.005007 |
| hgb_interactions | group:offense | 0.004316 |
| hgb_selected | group:scoring_turnovers | 0.003825 |
| hgb_interactions | feature:away_success_defense | 0.002317 |
| hgb_interactions | group:scoring_turnovers | 0.002188 |
| hgb_interactions | group:interactions | 0.002089 |
| hgb_selected | feature:recent_off_epa | 0.001640 |
| hgb_selected | feature:scoring | 0.001520 |
| hgb_selected | group:recent | 0.001390 |
| hgb_interactions | feature:scoring | 0.001329 |
| hgb_interactions | feature:recent_off_epa | 0.001232 |
| hgb_interactions | group:recent | 0.000939 |
| hgb_selected | group:defense | 0.000617 |
| hgb_interactions | feature:home_success_defense | 0.000566 |

Training/calibration-diagnostic/forward gaps, model complexity comparisons, learning-rate/depth sensitivity and year/early-versus-late-season metrics are exported. A lower training loss with worse forward probability loss is evidence of overfit in this sample; larger models or confidence do not establish reliability. Neither permutations nor later-year sensitivity diagnostics feed back into selection.

## Registry and promotion

Each version has algorithm, feature list/configuration, hyperparameters, training and calibration cutoffs, dataset fingerprint, report reference, artifact checksum and experimental designation. Existing serialized models remain loadable. New tree artifacts use a versioned m4-v1 feature adapter; the original logistic path is unchanged.

Activation is an explicit CLI operation requiring an approved decision JSON with named reviewer, rationale, Windows acceptance, exact candidate checksum and an existing checksummed evidence report. The previous production artifact is copied into an immutable hash-named backup before atomic replacement. An event journal supports rollback and detects replacement of unrelated champions. M4 did not execute activation on the actual champion. These checks validate recorded operator assertions, not the truth of the statistical review. Operators must not run concurrent activation/rollback commands.

## Verification

```json
{
  "recorded_at": "2026-11-03T05:46:36.354137+00:00",
  "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
  "python": "3.12.14",
  "native_windows": "not verified; activation remains gated",
  "baseline_tests": 62,
  "final_tests": 74,
  "test_command": "python -m pytest -q",
  "dependency_deprecation_warnings": 3,
  "preserved_m3_artifacts_verified": 196,
  "champion_and_sqlite_unchanged": true,
  "actual_model_activations": 0,
  "registered_experimental_candidates_verified": 48,
  "comparison_artifact_checksums_verified": 17,
  "dashboard_pages": [
    "Upcoming Games",
    "Team Comparison",
    "Model Performance",
    "Model Analysis",
    "Team Power Rankings"
  ],
  "m4_dashboard": "Comparison, importance, calibration, training/forward diagnostics and registry metadata rendered without exceptions",
  "xgboost": "Not installed/evaluated; optional comparison deferred, no failed installation claimed",
  "module_hashes": {
    "m3_dashboard.py": "5351a7f3c795b59a7205b25aeb959df19b4c5a025addaa3859caa7bf07812632",
    "schedule_features.py": "9729eeb3858191e1c89adf8e6c3f2a4e251268fa993fd4b9e93deb1f791001dd",
    "model.py": "1b8f73c4803e1fcb311bf13ee17f3c5a2a52b7c49cb0f70a62439ed205a10f2b",
    "m3.py": "42d8fd33f580e6eb182a5888192da4399f54edf1ae441f9cf873d76a257f68c0",
    "elo.py": "97bf2249618d43d21ab07d7c5437c4cb3371cc0bb5d6269504aa5db7754c5451",
    "reporting.py": "185fddd2facda141021a56a55dd0ad31707e61447f705a3edf6b90268975371b",
    "cli.py": "16d45a39cb4ae04cf8bc3b6cc7e0ee0a5a5c4d9fb79e43eccb8365934f2b5301",
    "data_loader.py": "969330217a55698f53c1dd16fd4be72cb4b8fb62c60b562a4be94f9a60f9a2ad",
    "backtest.py": "8d177789ebefadee6faad10b98b88e6c60df9db3023b3d41e9ff7aaed76d80d9",
    "database.py": "0702742af2c55912ea929f86d94fc57274aa1a3375c86affc0693559aafb76ca",
    "m4.py": "f9d5295a8bc6d6def814240deac98de3bfcbc397d669fe50a87f59f701c84899",
    "predictions.py": "c71f5a2e87c06dc16fd10e74d7de2ba36a2c46d8aa31a2eec99906b73440a556",
    "__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "evaluation.py": "8a2dc24b652bc7e7e83fa8d26b973352403408cb7b1aa9ab0549e6b186daccd3",
    "m3_report.py": "19bd0681bbfe85de698834e53d61ffbd430918a112cc80f552f28ee0fae0274e",
    "feature_engineering.py": "ee4bcfc79052a2b726af4157e2041d02936c51956676b69884fa8eb0d65daa07",
    "m4_report.py": "1e1239612ace980b20dd217bb435f65bfee31e181140f08799a905554e83f558",
    "quarterbacks.py": "bbf4cafb6c8e18e553a1c559f19a58958df636e0a198beac5e981b726c1ebc59",
    "analysis.py": "6d9588137f1ca80f758c83aa53c1824604bccc054216a9a513dc5a1254b271a3",
    "integrity.py": "29115341b9af63c6516d3588c68df5209c4b11c84e1d0287d6f43b950f8f8f78",
    "dashboard.py": "957dd6e4a6409a82606b923c459d30b2c9344c9af4e1b1251b53efd96828bb38",
    "m4_dashboard.py": "2b0a7e4564dfed036ff255e34ab5f519b569193646f2ebc0b8edc2c5ea0e6fe2",
    "m4_features.py": "83c4207b219fc1bd3f3bb8a1e5f56b428726fcfbc9d808b19a28a5824640e1b4",
    "registry.py": "b1af23175fa4d02b4ef1557a3942e28475d4a45c46f54bdca45ca10c120e2ce5",
    "boosting.py": "0775a166ecde0ac220b65c3f9825a23c6976c0ad5f7cc8b6657207cd20a94fe2",
    "data_validation.py": "92049d2d37fcf1869457b3f7b91c4a136f877a7f6852eaece18509be09b584ac"
  },
  "test_hashes": {
    "test_m4.py": "c5f7d5d25ae155d620410f02630ccb70c242d503b92f8ebea32ce10af00aa2a5",
    "test_m2.py": "2fb65d03af4d252ded29a6ff1624a9b120511b281f38dc66845cdc7702ff56e4",
    "test_m3.py": "bcf4e819ef0343e0052a5172bdaa6443014020ea058b47975c44bf61e066cf9f",
    "test_engine.py": "d8288426b53285d33a94e22018733a9200970c1c6da8a77009ba99fefd56a6e4"
  }
}
```

The dashboard loads precomputed reports only; normal rendering never trains or promotes models. All earlier pages remain available. Model Analysis distinguishes experimental M4 statistics, existing historical evidence and actual prospective forecasts. Native Windows execution remains unverified; source-ZIP/Git-absent behavior and Python compatibility are covered where the Linux test environment permits.

## Runtime and reproduction

Development fits: 12, measured total training seconds 2.389; individual fit range 0.074–0.617. CPU threads: 2. Times are machine-specific and not deterministic outputs.

With a virtual environment and cached source seasons: `python -m pytest -q`; `python -m nfl_predictor.cli train-m4`; `python -m nfl_predictor.cli compare-m4`; `python -m nfl_predictor.cli report-m4`; `python -m streamlit run app.py`. The three M4 experiment commands share one cached staged pipeline, so identical requests reuse results. Initial feature creation is content/code-cached and never rereads raw PBP for each parameter fit. Full PowerShell installation remains in README.md.

Measured run: `reports/m4/e615a644e92b3823`. reports/m4 contains selection, comparisons, diagnostics and run metadata; models/registry contains trusted local artifacts (excluded from Git). Reports preserve model hashes/metadata for audit; trained artifacts can be reproduced with the pinned dependencies and sources. Wall-clock timings vary across reruns; selection and predicted probabilities are deterministic at fixed inputs/runtime.

## Recommendation, limitations and M5 priorities

Retain the M2 champion pending meaningful stable forward evidence, Windows acceptance and independent prospective confirmation. No activation, prospective issuance, betting integration or M5/M7 implementation occurred. Optional XGBoost is deferred. QB coverage, final timestamps, source vintages, correlated-feature diagnostics, repeated-team/week dependence and unadjusted exploratory multiple comparisons remain limitations. Collect genuine prospective outcomes, complete Windows acceptance, and expand independent evaluation before considering additional complexity.
