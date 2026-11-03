# M7 engineering report

## Implementation and baseline preservation

M7 combines existing M2 logistic, fixed M5 shallow boosting and fixed M3 margin Elo. It adds annual OOS base caches, eight predefined raw ensemble policies, optional disjoint sigmoid/isotonic calibration, development-only selection, checksum-bound registry references, immutable experimental forecasts/results, CLI commands and Ensemble Analysis. M6 opponent/personnel code is preserved and excluded from these inputs. Production remains M2. No M8 work was performed.

Before implementation the complete suite actually passed 106 tests, matching M6. Full pre-M7 source/dataset/artifact hashes and champion metadata are in docs/m7/BASELINE.json. Earlier comparison implementations are covered by the full regression suite; their old report pointers are deliberately preserved rather than rerunning them into new output generations.

## Chronological contract recorded before coding

# M7 chronological protocol, recorded before implementation

The production M2 artifact and every previous dataset, forecast, Elo history,
registry entry and report are preserved. New research has separate caches and
experimental forecast records. No personnel or M6 adjusted features enter M7.

## Base predictions

For target seasons 2019–2026, refit M2 logistic on 2018 through the previous
season, and fixed M5 shallow HGB on 2008 through the previous season. Filter
training labels by actual result eligibility strictly before the first target
kickoff. Logistic retains its full original features and original 2018 feature
history; HGB retains M5 common features (without rest) and standard Elo warmed
from 1999. Replay fixed M3 margin Elo separately from 2018, its original history.
Ties update team histories/Elo but never binary supervised labels.

Each annual model stays fixed throughout its target season. Features/Elo update
only from results eligible before each game's cutoff. A late prior-season final
cannot enter the annual fit. Models must be fitted before every scored kickoff.
These are retrospective chronological predictions, never backdated forecasts.
Annual base refits differ deliberately from M5's frozen-2022 reference; report
M7's matched annual HGB reference separately from the original M5 scores.

## Meta, calibration and evaluation calendar

| Role | Meta OOS seasons | Disjoint calibration | Evaluation | Selection use |
|---|---|---|---|---|
| Development 1 | 2019–2020 | 2021 | 2022 | Yes |
| Development 2 | 2019–2021 | 2022 | 2023 | Yes |
| Historical 1 | 2019–2022 | 2023 | 2024 | No |
| Historical 2 | 2019–2023 | 2024 | 2025 | No |
| Prospective artifact | 2019–2024 | 2025 | 2026 upcoming only | No |

Meta training requires at least two earlier seasons, 200 binary games and both
classes. Filter all labels by eligibility before calibration starts. Freeze the
meta-model while predicting calibration and evaluation. Calibration labels must
be eligible strictly before evaluation begins. Reject overlapping periods and
in-sample base probabilities. Delayed labels are excluded and counted.

The final policy is selected using equal-season mean development Brier, then
log loss, then candidate name; the strongest individual reference is selected
on the same development years. Selection completes before the first 2024
kickoff. A development-year selected-policy score is explicitly a selection
result, not an independent evaluation. Do not choose 2024/2025 weights from their
outcomes. Updating fitted parameters in later years under the frozen policy is
allowed using earlier eligible labels, never a game's own outcome.

## Preregistered candidates and calibration

Three individual references; E1 equal thirds; E2 half HGB/half margin Elo; three
E3 weight triples (logistic, HGB, margin Elo): (.2,.6,.2), (.25,.5,.25),
(.1,.7,.2); E4 nonnegative SLSQP weights summing to one, initialized at
(.2,.6,.2), minimizing mean Brier + .02 times squared distance from that prior,
analytic gradient, tolerance 1e-12 and maximum 500 iterations. Optimizer failure
is explicit, never a substituted equal-weight result.

E5 has two small predefined representations: probabilities or log odds clipped
at 1e-6. Each uses only three inputs and an intercept, L2 logistic C=1, seed 42,
maximum 1000 iterations. No base or meta hyperparameter search is allowed.

There are eight raw ensemble policies. Each has raw, sigmoid and (when at least
200 calibration games and ten unique scores exist) isotonic versions: at most
24 ensemble configurations. Sigmoid uses log odds and C=1e6. Fit calibrators only
on the separate calibration year; select policy only on development outcomes.
No future-period diagnostics feed selection.

## Reporting and prospective issuance

Compare every policy on identical complete-base binary games, with explicit
missingness, ties, unfinished and delayed-label exclusions. Export paired
season-week bootstrap intervals (2000 replicates, seed 42), comparisons against
HGB, logistic and the development-selected strongest individual, calibration,
season phase, confidence, disagreements, probability/error correlations and
favorite/underdog diagnostics. Intervals are exploratory, unadjusted for the
24-policy comparison; repeated teams and weeks limit inference. 2024–2025 were
already examined during earlier milestones.

For genuine upcoming 2026 games use annual base models fitted through eligible
2025 games, frozen selected policy and the prospective-artifact calendar above.
Actual creation time cannot be backdated; feature cutoffs may be earlier than
creation only if all base/meta/calibration/selection training also precedes that
cutoff. Store immutable experimental forecasts in a separate append-only ledger,
with separate append-only outcome grading events. No official SQLite writes.
Verify all referenced artifact checksums and feature contracts on every load.

Native M6/M7 Windows testing remains outstanding unless genuinely performed.
All candidates remain activation-blocked. No champion promotion or M8 work.


## Exact fitted fold boundaries

| evaluation | meta_seasons | calibration_season | meta_games | calibration_games | evaluation_games | meta_outcome_cutoff | calibration_start | calibration_outcome_cutoff | evaluation_start | excluded_delayed_meta_labels | excluded_delayed_calibration_labels | meta_fingerprint | calibration_fingerprint |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | [2019, 2020] | 2021 | 510 | 271 | 269 | 2021-01-04T09:20:00+00:00 | 2021-09-10T00:20:00+00:00 | 2022-01-10T09:20:00+00:00 | 2022-09-09T00:20:00+00:00 | 0 | 0 | f354972076e8284ee5e3da732b31fad6fd388cca2e340ae017d5f3626812b82e | 737e66d4b5ba232d955e1e710887e6af43f47d4559608145966c8377cc0e4444 |
| 2023 | [2019, 2020, 2021] | 2022 | 781 | 269 | 272 | 2022-01-10T09:20:00+00:00 | 2022-09-09T00:20:00+00:00 | 2023-01-09T09:20:00+00:00 | 2023-09-08T00:20:00+00:00 | 0 | 0 | e7708eb884d2764c8ed99b55de129c6d394ba50813cb55f0aa4ea5b8ec98f5f1 | e08b183bb7feb7785c9ff608d671319b2a3082bba6ff2fb16612751568ab314a |
| 2024 | [2019, 2020, 2021, 2022] | 2023 | 1050 | 272 | 272 | 2023-01-09T09:20:00+00:00 | 2023-09-08T00:20:00+00:00 | 2024-01-08T09:20:00+00:00 | 2024-09-06T00:20:00+00:00 | 0 | 0 | 8a2e1e069d721e136c017365f9699d7b472ec6d427c426a13ef1f0e1fa4c28fd | 04dd93ba7b3743814d3c878b7e03c9b3cdc2347c99cc036e08af5c2ab6b5bf61 |
| 2025 | [2019, 2020, 2021, 2022, 2023] | 2024 | 1322 | 272 | 271 | 2024-01-08T09:20:00+00:00 | 2024-09-06T00:20:00+00:00 | 2025-01-06T09:20:00+00:00 | 2025-09-05T00:20:00+00:00 | 0 | 0 | 12d50a2be763603abb0f9d5616aef68e0e09d464b58c0b047f1c3b36c9cf7ac0 | d1f95e1cbd51c9502ff025600a0f3a5c35a52cf2d62ae3998788b12ab5141402 |
| 2026 | [2019, 2020, 2021, 2022, 2023, 2024] | 2025 | 1594 | 271 | 0 | 2025-01-06T09:20:00+00:00 | 2025-09-05T00:20:00+00:00 | 2026-01-05T09:20:00+00:00 | 2026-09-10T00:20:00+00:00 | 0 | 0 | 19045ff4983024767c6a1b7658d366834ea7e439ca584ce9359e591a2aaa7dcc | 405adcfc11c1e16679474d8c9420b08078ffed67d8ecc5be591118e5d8d1d979 |

Annual base cutoffs, versions, training counts and source fingerprints are retained with the base matrix metadata and every row. Ensemble registry references verify exact base artifact checksums, feature schemas and training cutoffs. Margin Elo retains its original 2018 replay origin, whereas M5’s standard Elo feature retains 1999 warmup. The current production artifact is never used in historical folds.

The primary comparison uses annual prior-season refits, including 2023 training for 2024 and 2024 training for 2025. This differs from the M5/M6 frozen-2022 HGB evaluation; differences from that older reported number cannot be attributed solely to ensembling. All M7 direct comparisons share the annual base matrix and identical eligible games.

## Alignment and exclusions

```json
{
  "scheduled_games": 1871,
  "included_games": 1865,
  "missing_base_predictions": 0,
  "ties": 6,
  "incomplete_labels": 0,
  "unavailable_or_delayed_labels": 0,
  "exclusions_are_overlapping": true
}
```

Ties update underlying histories but do not enter binary fitting or scoring. Incomplete and unavailable final outcomes are excluded. Missing base predictions are counted and never replaced with 0.5. These categories may overlap. No dropped row can silently create different model evaluation samples.

## Development selection and parameter fitting

| model | brier | log_loss | seasons |
| --- | --- | --- | --- |
| logistic | 0.226327 | 0.644662 | 2 |
| E1_equal__raw | 0.227374 | 0.646630 | 2 |
| E3_25_50_25__raw | 0.228158 | 0.648459 | 2 |
| E3_20_60_20__raw | 0.228690 | 0.649710 | 2 |
| E1_equal__sigmoid | 0.228973 | 0.650442 | 2 |
| E4_optimized__raw | 0.229165 | 0.650735 | 2 |
| E2_boost_elo__raw | 0.229347 | 0.651058 | 2 |
| E5_probabilities__sigmoid | 0.229392 | 0.651119 | 2 |
| E3_10_70_20__raw | 0.229423 | 0.651412 | 2 |
| E3_25_50_25__sigmoid | 0.229548 | 0.651634 | 2 |
| elo_margin | 0.229744 | 0.651707 | 2 |
| E3_20_60_20__sigmoid | 0.229932 | 0.652435 | 2 |
| E5_logits__sigmoid | 0.230105 | 0.652545 | 2 |
| E2_boost_elo__sigmoid | 0.230170 | 0.652763 | 2 |
| E4_optimized__sigmoid | 0.230188 | 0.652906 | 2 |
| E3_10_70_20__sigmoid | 0.230404 | 0.653391 | 2 |
| E1_equal__isotonic | 0.231082 | 0.675953 | 2 |
| E2_boost_elo__isotonic | 0.231280 | 0.678346 | 2 |
| boosting | 0.231285 | 0.655969 | 2 |
| E5_probabilities__raw | 0.231620 | 0.656208 | 2 |
| E5_probabilities__isotonic | 0.231766 | 0.679015 | 2 |
| E5_logits__isotonic | 0.232483 | 0.660452 | 2 |
| E5_logits__raw | 0.232729 | 0.658679 | 2 |
| E4_optimized__isotonic | 0.233368 | 0.682729 | 2 |
| E3_25_50_25__isotonic | 0.233667 | 0.683332 | 2 |
| E3_10_70_20__isotonic | 0.235930 | 0.688286 | 2 |
| E3_20_60_20__isotonic | 0.235990 | 0.689082 | 2 |

Selected policy metadata: `{"method": "E1_equal__raw", "strongest_individual": "logistic", "seasons": [2022, 2023], "outcome_cutoff": "2024-01-08T09:20:00+00:00", "rules": "Equal-season development mean Brier, then log loss, then name. Freeze before 2024. Annual parameter refits follow the fixed calendar.", "ensemble_configurations_compared": 24}`. There are eight raw policies and up to 24 ensemble/calibration configurations, plus three individual references. Equal-season development mean Brier, then log loss, then name chooses the policy. Later evaluation labels do not choose weights, representation, regularization or calibration method. Parameters are refitted annually using only the scheduled earlier meta/calibration periods.

| evaluation | model | method | weights | representation | coefficients | intercept | calibration_method |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | E1_equal__raw | E1_equal | [0.3333333333333333, 0.3333333333333333, 0.3333333333333333] | probabilities | nan | nan | raw |
| 2023 | E1_equal__raw | E1_equal | [0.3333333333333333, 0.3333333333333333, 0.3333333333333333] | probabilities | nan | nan | raw |
| 2024 | E1_equal__raw | E1_equal | [0.3333333333333333, 0.3333333333333333, 0.3333333333333333] | probabilities | nan | nan | raw |
| 2025 | E1_equal__raw | E1_equal | [0.3333333333333333, 0.3333333333333333, 0.3333333333333333] | probabilities | nan | nan | raw |

Constrained optimization uses SLSQP with an analytic gradient, nonnegative unit-sum weights and fixed .02 shrinkage toward (.2,.6,.2). The two stackers use three inputs plus intercept, L2 C=1, no interactions and deterministic seed. Exact optimizer status/weights and meta/calibration fingerprints are stored per fold. There is no base hyperparameter/window search.

## Measured already-examined 2024–2025 results

The development-selected E1_equal__raw scored Brier 0.216955 versus annual boosting 0.216419; its model-minus-boosting difference was +0.000536, with exploratory interval [-0.001811, +0.002656]. Lower is better. These examined results do not justify replacing the frozen policy with a later-period winner or promoting an ensemble.

| model | accuracy | brier | log_loss |
| --- | --- | --- | --- |
| E1_equal__isotonic | 0.661142 | 0.222060 | 0.652216 |
| E1_equal__raw | 0.650092 | 0.216955 | 0.622611 |
| E1_equal__sigmoid | 0.651934 | 0.220379 | 0.631473 |
| E2_boost_elo__isotonic | 0.674033 | 0.219602 | 0.668377 |
| E2_boost_elo__raw | 0.668508 | 0.216671 | 0.622067 |
| E2_boost_elo__sigmoid | 0.655617 | 0.219746 | 0.630103 |
| E3_10_70_20__isotonic | 0.659300 | 0.222188 | 0.651108 |
| E3_10_70_20__raw | 0.651934 | 0.216346 | 0.621294 |
| E3_10_70_20__sigmoid | 0.653775 | 0.220142 | 0.630901 |
| E3_20_60_20__isotonic | 0.659300 | 0.221413 | 0.650174 |
| E3_20_60_20__raw | 0.653775 | 0.216515 | 0.621652 |
| E3_20_60_20__sigmoid | 0.653775 | 0.220307 | 0.631265 |
| E3_25_50_25__isotonic | 0.659300 | 0.220966 | 0.648803 |
| E3_25_50_25__raw | 0.648250 | 0.216645 | 0.621932 |
| E3_25_50_25__sigmoid | 0.659300 | 0.220301 | 0.631270 |
| E4_optimized__isotonic | 0.664825 | 0.220600 | 0.648180 |
| E4_optimized__raw | 0.657459 | 0.216474 | 0.621559 |
| E4_optimized__sigmoid | 0.651934 | 0.220129 | 0.630889 |
| E5_logits__isotonic | 0.662983 | 0.219934 | 0.650799 |
| E5_logits__raw | 0.661142 | 0.216112 | 0.621662 |
| E5_logits__sigmoid | 0.655617 | 0.219889 | 0.630411 |
| E5_probabilities__isotonic | 0.662983 | 0.222292 | 0.673578 |
| E5_probabilities__raw | 0.668508 | 0.216373 | 0.622798 |
| E5_probabilities__sigmoid | 0.653775 | 0.219965 | 0.631088 |
| boosting | 0.661142 | 0.216419 | 0.621503 |
| elo_margin | 0.651934 | 0.219134 | 0.627875 |
| logistic | 0.637201 | 0.220803 | 0.630879 |

Selected ensemble versus matched annual boosting:

| model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- |
| E1_equal__raw | accuracy | 0.650092 | -0.011050 | -0.027675 | 0.005598 | 543 |
| E1_equal__raw | brier | 0.216955 | 0.000536 | -0.001811 | 0.002656 | 543 |
| E1_equal__raw | log_loss | 0.622611 | 0.001108 | -0.004536 | 0.006149 | 543 |

## Individual seasons

| period | model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024 | E1_equal__raw | accuracy | 0.665441 | -0.029412 | -0.048877 | -0.007461 | 272 |
| 2024 | E1_equal__raw | brier | 0.209485 | 0.001063 | -0.002540 | 0.004185 | 272 |
| 2024 | E1_equal__raw | log_loss | 0.607071 | 0.002153 | -0.006744 | 0.009889 | 272 |
| 2024 | boosting | accuracy | 0.694853 | 0.000000 | 0.000000 | 0.000000 | 272 |
| 2024 | boosting | brier | 0.208422 | 0.000000 | 0.000000 | 0.000000 | 272 |
| 2024 | boosting | log_loss | 0.604918 | 0.000000 | 0.000000 | 0.000000 | 272 |
| 2024 | elo_margin | accuracy | 0.658088 | -0.036765 | -0.079422 | 0.003788 | 272 |
| 2024 | elo_margin | brier | 0.213194 | 0.004772 | -0.002995 | 0.012282 | 272 |
| 2024 | elo_margin | log_loss | 0.615211 | 0.010293 | -0.008114 | 0.028971 | 272 |
| 2024 | logistic | accuracy | 0.676471 | -0.018382 | -0.058829 | 0.021980 | 272 |
| 2024 | logistic | brier | 0.212246 | 0.003824 | -0.003615 | 0.011986 | 272 |
| 2024 | logistic | log_loss | 0.613176 | 0.008258 | -0.008197 | 0.025438 | 272 |
| 2025 | E1_equal__raw | accuracy | 0.634686 | 0.007380 | -0.018182 | 0.032612 | 271 |
| 2025 | E1_equal__raw | brier | 0.224453 | 0.000007 | -0.002362 | 0.002614 | 271 |
| 2025 | E1_equal__raw | log_loss | 0.638208 | 0.000059 | -0.005782 | 0.005929 | 271 |
| 2025 | boosting | accuracy | 0.627306 | 0.000000 | 0.000000 | 0.000000 | 271 |
| 2025 | boosting | brier | 0.224445 | 0.000000 | 0.000000 | 0.000000 | 271 |
| 2025 | boosting | log_loss | 0.638150 | 0.000000 | 0.000000 | 0.000000 | 271 |
| 2025 | elo_margin | accuracy | 0.645756 | 0.018450 | -0.015152 | 0.049057 | 271 |
| 2025 | elo_margin | brier | 0.225096 | 0.000651 | -0.005277 | 0.008139 | 271 |
| 2025 | elo_margin | log_loss | 0.640586 | 0.002436 | -0.010518 | 0.019162 | 271 |
| 2025 | logistic | accuracy | 0.597786 | -0.029520 | -0.059265 | 0.003704 | 271 |
| 2025 | logistic | brier | 0.229392 | 0.004947 | -0.001387 | 0.010848 | 271 |
| 2025 | logistic | log_loss | 0.648648 | 0.010498 | -0.005047 | 0.024599 | 271 |

comparison.csv additionally supplies matched intervals against logistic and the development-selected strongest individual. Nominal intervals are unadjusted exploratory diagnostics, not a superiority or promotion certificate.

## Complementarity, calibration and uncertainty

| period | first | second | games | probability_correlation | error_correlation | disagreement_fraction | mean_absolute_probability_gap | mean_confidence_first | mean_confidence_second |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | logistic | boosting | 541 | 0.938110 | 0.993451 | 0.125693 | 0.047949 | 0.620073 | 0.637331 |
| development | logistic | elo_margin | 541 | 0.860947 | 0.985683 | 0.158965 | 0.067968 | 0.620073 | 0.642177 |
| development | boosting | elo_margin | 541 | 0.907000 | 0.989901 | 0.103512 | 0.053767 | 0.637331 | 0.642177 |
| examined_2024_2025 | logistic | boosting | 543 | 0.938524 | 0.992180 | 0.116022 | 0.049508 | 0.631739 | 0.648894 |
| examined_2024_2025 | logistic | elo_margin | 543 | 0.865325 | 0.982812 | 0.169429 | 0.072156 | 0.631739 | 0.651993 |
| examined_2024_2025 | boosting | elo_margin | 543 | 0.924971 | 0.989858 | 0.097606 | 0.052543 | 0.648894 | 0.651993 |

Probability correlation and residual (p−y) correlation are descriptive; shared outcomes induce residual correlation. Disagreement and agreement subsets, average confidence gaps and pairwise disagreement outcomes are in pair_disagreements.csv and disagreement.csv. Elo already enters HGB as a standard-Elo feature, so algorithm names alone do not establish diversity. M7 tests margin Elo separately; no claim of causal independent contribution follows from correlation.

Raw, sigmoid and supported isotonic variants are all exported. Calibrators fit only the intervening year’s OOS base probabilities transformed by the frozen meta-model. Annual deployment base models are refitted after those OOS calibration predictions were made; calibration transfer across base refits remains a limitation. Reliability diagrams, calibration slopes/intercepts, confidence buckets, early/late seasons, and model-defined favorites/underdogs are saved. Favorites use >=50% model probability, not market odds. A tie at 50% deterministically picks home.

## Prospective forecasts, registry and dashboard

forecast-ensemble uses versioned 2026 annual base refits and the development-selected policy; it never fits models. Both source features and online Elo updates obey the chosen cutoff. Actual creation time must precede kickoff and cannot be backdated. All base/meta/calibration/selection training must precede that cutoff. Historical research rows are labeled retrospective and carry actual generation time.

Experimental forecasts live under data/m7/experimental_forecasts, separately from SQLite. A game/version/cutoff identifies an immutable forecast; repeated identical issuance reuses it, while changed probabilities or provenance are rejected rather than overwriting it. Revised cutoffs/versions create separate forecasts. Result grading appends events, including revisions and ties, without modifying forecasts. Multiple forecasts for one game are correlated revisions and must not be treated as independent evidence.

Registry loading verifies the ensemble checksum plus every base checksum/schema/version/cutoff; missing or incompatible artifacts are errors. Existing registry rollback and activation paths remain compatible; M7 artifacts are explicitly activation-blocked. The official champion and SQLite bytes remain preserved. Team Comparison shows only available, checksum-verified experimental saved forecasts alongside the existing champion estimate, with their own cutoffs labeled. Ensemble Analysis reads saved results and forecast records; rendering never trains or issues forecasts.

## Runtime and cache evidence

| evaluation | fitting_prediction_seconds |
| --- | --- |
| 2022 | 0.310162 |
| 2023 | 0.306252 |
| 2024 | 0.345513 |
| 2025 | 0.359901 |

Measured research runtime: 15.852 seconds; peak RSS where measurable: 340283392 bytes. CPU-only, existing dependencies. Base predictions are built once per source/code/config fingerprint; weight/calibration experiments operate on compact matrices.

## Verification and Windows status

```json
{
  "checked_at": "2026-11-03T23:37:52.584863+00:00",
  "status": "Implemented and verified on Linux. Native combined M6/M7 Windows acceptance remains outstanding. No champion promotion.",
  "baseline_suite": {
    "passed": 106,
    "warnings": 7,
    "seconds": 123.32,
    "matches_M6_report": true
  },
  "complete_suite": {
    "command": "python -m pytest -q",
    "passed": 129,
    "warnings": 8,
    "seconds": 201.17,
    "new_tests": 23,
    "platform": "Linux Python 3.12.14",
    "log": "docs/m7/PYTEST.txt"
  },
  "all_preexisting_artifacts_preserved": 2378,
  "changed_preexisting_artifacts": [],
  "champion_version": "20261103T043653-6d77120a",
  "champion_sha256": "34031d18cb2a1e94a511f11061070ebda07eb95491e34f0e9a70f2709a8370a8",
  "sqlite_sha256": "3a56d523b930a4aa0ed40bcdb07c74bd0ffa74527d7bd9576b0260ffe6dc4ebd",
  "local_acceptance": {
    "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
    "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
    "native_windows": false,
    "checked_at": "2026-11-03T23:35:19.789769+00:00",
    "checks": {
      "champion_load": "passed",
      "upcoming_predictions": "passed",
      "Upcoming Games": "passed",
      "Team Comparison": "passed",
      "Model Performance": "passed",
      "Model Analysis": "passed",
      "Team Power Rankings": "passed",
      "registry_load": "passed",
      "M7_forecast_ledger": "passed",
      "preservation": "passed"
    },
    "champion_version": "20261103T043653-6d77120a",
    "upcoming_count": 151,
    "registered_candidates_loaded": 1099,
    "experimental_ensemble_forecasts": {
      "genuinely_issued_forecasts": 151,
      "unique_games": 151,
      "graded": 0,
      "ties": 0,
      "binary_metrics": null,
      "metric_cohort": "First genuinely issued experimental forecast per game; future research should also compare fixed model-version/cutoff cohorts.",
      "note": "Multiple forecasts per game are revisions, not independent games."
    },
    "preserved_artifacts": 2208,
    "status": "Review required; no automatic Windows certification. Native Windows, full data/model steps, manual UI startup and RAM behavior must all be verified."
  },
  "additional_ui": {
    "scheduled_matchup": "2026_09_JAX_BAL",
    "M6_team_context": "passed",
    "saved_experimental_probabilities": "passed",
    "Ensemble_Analysis": "passed",
    "native_windows": false,
    "streamlit_http_health": "passed"
  },
  "cache_reuse": {
    "command": "python -m nfl_predictor.cli report-m7",
    "cache_reused": true,
    "run": "5b401bdc9b161ac3",
    "seconds": 9.935315805996652,
    "report_files_unchanged": 22
  },
  "source_cache_reuse": {
    "M5_season_feature_generations_reused": 28,
    "source_order_correction_max_prediction_difference": 1.4489520694382918e-12,
    "development_selection_unchanged": true
  },
  "historical_matrix": {
    "scheduled_games": 1871,
    "included_games": 1865,
    "missing_base_predictions": 0,
    "ties": 6,
    "incomplete_labels": 0,
    "unavailable_or_delayed_labels": 0,
    "exclusions_are_overlapping": true
  },
  "matrix_processing_seconds": 17.043980284994177,
  "research_seconds": 15.851969346003898,
  "peak_rss_bytes": 340283392,
  "ensemble_artifacts_in_final_run": 97,
  "base_artifacts_in_final_run": 24,
  "all_final_artifacts_activation_blocked": true,
  "prospective_issuance": {
    "cutoff": "2026-11-03T23:33:53.574764+00:00",
    "commands": [
      "forecast-ensemble --cutoff <actual-now>",
      "same explicit-cutoff command repeated",
      "grade-ensemble"
    ],
    "timings": {
      "initial_seconds": 17.144573732002755,
      "repeat_seconds": 16.99705448100576
    },
    "issuance_count": 151,
    "idempotent_repeat": "passed",
    "champion_unchanged": true,
    "sqlite_unchanged": true,
    "summary": {
      "genuinely_issued_forecasts": 151,
      "unique_games": 151,
      "graded": 0,
      "ties": 0,
      "binary_metrics": null,
      "metric_cohort": "First genuinely issued experimental forecast per game; future research should also compare fixed model-version/cutoff cohorts.",
      "note": "Multiple forecasts per game are revisions, not independent games."
    },
    "first_record": {
      "away_probability": 0.19333909956877215,
      "away_team": "LAC",
      "base_checksums": {
        "boosting": "c4f228ed7ab6ced72c446b94a3183d07b48afb4fd62125157941c2097af4122b",
        "elo_margin": "f5b0c6e881fa3ac9903ef17c59c4af8a9bd8d3d09f3fd26beb53d20bf4af5748",
        "logistic": "b993e155152db65456cf1d330d85e58c1babf3480359da94b4b374b77672ceac"
      },
      "base_probabilities": {
        "boosting": 0.8041510769064223,
        "elo_margin": 0.835018501923925,
        "logistic": 0.7808131224633366
      },
      "base_versions": {
        "boosting": "m7-base-2026-boosting-079349ddbe0f0ce9",
        "elo_margin": "m7-base-2026-elo-b920e7a522eea884",
        "logistic": "m7-base-2026-logistic-df27c7bcf964bdef"
      },
      "calibration": {
        "cutoff": "2026-01-05T09:20:00+00:00",
        "method": "raw",
        "season": 2025
      },
      "created_at": "2026-11-03T23:34:10.481351+00:00",
      "data_cutoff": "2026-11-03T23:33:53.574764+00:00",
      "designation": "experimental",
      "ensemble_method": "E1_equal__raw",
      "ensemble_version": "m7-ensemble-2026-b1f6fd75323087f88037",
      "forecast_id": "05cda7f5f445353e80bebcc2ee51e3e0ea924e2c43b3ba6f62c7ed59169713e9",
      "game_id": "2026_18_LAC_DEN",
      "home_probability": 0.8066609004312278,
      "home_team": "DEN",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "kind": "experimental_ensemble_forecast",
      "season": 2026,
      "selection": {
        "ensemble_configurations_compared": 24,
        "method": "E1_equal__raw",
        "outcome_cutoff": "2024-01-08T09:20:00+00:00",
        "rules": "Equal-season development mean Brier, then log loss, then name. Freeze before 2024. Annual parameter refits follow the fixed calendar.",
        "seasons": [
          2022,
          2023
        ],
        "strongest_individual": "logistic"
      },
      "source_fingerprints": {
        "eligible_metrics_fingerprint": "1068c309eb27f20e3bceb0420c4f1a5954e84518e95913942456227376f2e72b",
        "eligible_schedule_fingerprint": "6f8e5f91fee565e50591dc080589410fd402916e6698f1ef2e2d0d2814efbc97",
        "elo_config_fingerprint": "1108eee3bed458dd896efd3761d634ebd4a876fbf944124e93bcddf1972bc9b8",
        "feature_fingerprint": "e294c2affd3008c05000d2e899325d26b16045c160b6c289fcfac1e1769f8444"
      },
      "training_cutoff": "2026-01-05T09:20:00+00:00",
      "week": 18
    }
  },
  "prospective_archive": {
    "file": "docs/m7/PROSPECTIVE_FORECASTS.json",
    "sha256": "bcdaaa0ce7f8e7e75f70ac57e858a8c4a17be3c50d3047bf6f8019310e120da2",
    "records": 151,
    "graded": 0
  },
  "measured_findings": {
    "selection": "E1_equal__raw, selected on 2022\u20132023 only",
    "examined_2024_2025_games": 543,
    "selected_brier": 0.21695526117366443,
    "matched_annual_boosting_brier": 0.21641911640151965,
    "interpretation": "No demonstrated incremental improvement over annual boosting. Do not switch to a post-hoc winner or promote.",
    "independent_prospective_results": "None yet; 151 issued forecasts are ungraded."
  },
  "limitations": [
    "Native M6/M7 Windows tests were not executed.",
    "2024\u20132025 were repeatedly examined; bootstrap intervals are exploratory and unadjusted for multiple policies.",
    "M7 annual base refits differ from the M5 frozen-2022 reference.",
    "Existing missing PBP for 2026_08_CHI_SEA remains missing and warned; no cache refresh or zero substitution.",
    "Inherited conservative timing/source-vintage limitations remain.",
    "Historical model-selection and calibration transfer may not generalize to new games."
  ]
}
```

M6 was accepted as an engineering milestone by the user. Native M6 and M7 Windows execution was not independently demonstrated here. Linux tests, imports, UI checks and the provided combined Windows script do not establish native Windows acceptance.

## Launch and reproduce

Use Python 3.12 and the locked dependencies: `python -m pip install -r requirements.lock.txt`; `python -m pip install -e ".[test]"`. Restore existing data/model caches or run documented M1/M5 ingestion first. Then run:

```powershell
python -m nfl_predictor.cli build-ensemble-predictions
python -m nfl_predictor.cli compare-m7
python -m nfl_predictor.cli report-m7
python -m nfl_predictor.cli forecast-ensemble
python -m nfl_predictor.cli grade-ensemble
python -m pytest -q
python -m streamlit run app.py
```

Open http://localhost:8501. On genuine Windows use `.\scripts\windows_acceptance.ps1 -Full` for combined M6/M7 processing, then perform manual UI and memory checks. Cached results can be inspected offline. Downloaded datasets, SQLite and fitted joblib artifacts are not committed; reproducible measured reports are included.

## Limitations and promotion recommendation

Retain M2 as the official champion. Any future promotion needs explicit approval, independent prospective evidence and native Windows verification. Development chooses among up to 24 correlated policies; repeatedly examined 2024–2025 is exploratory. Schedule/model/data vintages and final-publication timestamps remain retrospective. The inherited eight-hour eligibility proxy and date-only historical bounds remain assumptions. Personnel coverage is still insufficient and deliberately unused. No probability is called calibrated merely because a calibration transform was applied.

For M8 planning only: first collect independent prospective outcomes and verify Windows behavior. Any proposed Betting Lab must be separately scoped and approved; no odds, wagering, expected-value calculations or M8 implementation were added.
