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
