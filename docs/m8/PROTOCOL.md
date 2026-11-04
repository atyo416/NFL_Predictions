# M8 protocol recorded before implementation

Only NFL two-sided game moneylines are supported. No accounts, money transfers,
bet placement, new ML fits, ensemble selection, or M9 work are included.

Preserve every pre-M8 dataset, forecast, model and report. M8 has its own SQLite
database with immutable rows and append-only events. Read the official forecast
database in SQLite read-only mode; never call its write helpers. M7 probabilities
are read from genuinely saved records, preserving exact artifact versions. M7's
boosting probability is the M5 architecture with M7 annual refits, explicitly
distinguished from the older frozen-2022 M5 experiment.

## Provider and provenance

Fetch only by explicit command. The initial adapter calls the single current
NFL h2h/us/American endpoint. Never store keys, request URLs containing keys, or
raw provider error bodies. Track safe quota headers, enforce a five-minute
cooldown, and allow at most two short bounded attempts. Missing credentials do
not disable the rest of the application. CSV and JSON work offline.

One normalized record is a complete pair from the same provider event, bookmaker,
market object, timestamp and scope. No cross-book no-vig construction. Keep the
original response bytes/fingerprint, quote publication/version timestamp,
provider archive timestamp where present, actual capture/import time, kickoff,
source reference, market scope, and explicit settlement rules separately.
Historical imports never acquire a fictitious earlier capture time. Synthetic
fixtures remain synthetic and cannot create genuinely prospective wagers.

Known exact team names/aliases, designated home/away, NFL season and kickoff
within five minutes determine automatic matches. Neutral games retain their
designated sides. Reversed, ambiguous, duplicate events or changed kickoffs
require review. A versioned audit retains schedule fingerprints and decisions.

## Mathematics and eligibility

American quotes must be finite canonical integers <=−100 or >=+100; decimal
quotes must exceed one. Use decimal arithmetic for price/EV/payout calculations.
Raw implied probabilities are 1/decimal; proportional no-vig divides both by
their sum. This is a convention, not the true win probability.

Binary EV is p*decimal−1 per unit. The NFL model excludes ties: EV is explicitly
a conditional no-tie scenario. Unknown tie rules/scope block paper issuance.
Only documented game-including-overtime markets with tie push/void are eligible;
tie-loss or three-way markets need a different probability model. Unknown
reschedule/cancel rules lead to review, never invented settlements.

A decision requires quote publication, snapshot and actual capture, plus forecast
creation and information cutoff, all no later than the decision, strictly before
kickoff. Artifact training/selection/calibration must precede forecast cutoff.
Quotes older than 15 minutes and forecasts older than 24 hours are flagged and
excluded. Both absent and stale forecasts remain unavailable, never 0.5.

## Cohorts and historical reconstruction

24h, 6h and 1h benchmark decisions use kickoff minus the stated lead. Quotes
must lie in [decision−15min, decision], [decision−10min, decision], and
[decision−5min, decision] respectively. Never take a quote after the decision,
even if it is near the target lead. One game/book/policy/cohort is one matched
observation, not each price update. Choose books by the fixed priority list,
then lexical identity. All compared models must be available at that same cutoff.

Prospective benchmarking requires actually issued forecasts/captured quotes.
Archived provider timestamps can support explicitly reconstructed research,
but never backdated issuance. Existing M7 kickoff-cutoff historical features
cannot be used at 24h/6h/1h: they are too late. Reconstruction, where genuine
odds exist, performs inference only with frozen historical M7 base/ensemble
artifacts and freshly cutoff-specific features. No retraining. 2024–2025 remains
exploratory. Without genuine historical odds, real benchmarking is skipped.

## Fixed paper strategies and reporting

Stake is one simulated unit. Thresholds >0%, >3%, >5% are predefined sensitivity
policies, not optimized. Default is champion logistic and >3%, chosen a priori.
Choose the first eligible book, then the higher-EV side (home on ties).
One opportunity is game+strategy version+timing cohort. Repeated issuance cannot
change the original quote, probability or stake. No backdated paper decision
parameter is accepted. Dry run does not save wagers. Revisions/settlements are
append-only; corrected results supersede earlier events with a traceable chain.

Win profit is stake*(decimal−1); loss is −stake; documented push/void is zero.
Report pending and review separately. ROI divides settled profit by settled
stake including refunded wagers; undefined without settled stakes. Drawdown uses
equity changes grouped at equal result-availability times. Losing streak uses a
documented game-ID tie-break. Separate strategies/books/cohorts; never treat
multiple prices or model strategies for one game as independent games.

CLV requires an explicitly verified final pregame snapshot within ten minutes of
kickoff, same event/book/side/rules. A merely last-observed quote is not certified
closing. Entry/closing decimal ratio minus one is descriptive, not proof of edge.
Future closing quotes cannot enter entry selection or benchmark cohorts.

Export calibration, paired season-week intervals and probability/EV sensitivity
at ±2/±5 percentage points. Sensitivity is not a confidence interval. No real
market profitability or prospective probability result is reported without
genuine matched, graded data. Synthetic examples are isolated and labeled.
Native combined M6/M7/M8 Windows acceptance remains outstanding unless executed.
