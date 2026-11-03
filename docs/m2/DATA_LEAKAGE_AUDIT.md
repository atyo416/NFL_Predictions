# M2 data integrity and leakage audit

The M1 baseline ran successfully on Linux/Python 3.12 before modification: 16 tests passed. Its architecture is nflreadpy → season Parquet → team-game rates → rolling/shrunk matchup features → training-fitted mean imputer/scaler/L2 logistic → SQLite immutable forecast payloads. M1 reports and production artifacts are preserved, not refitted by M2 analysis. Native Windows execution remains unverified.

## Sources and availability

Inspected the cached 2025 schedule schema: kickoff clock (`gameday`, `gametime`) is present but no final/publication timestamp. Inspected play-by-play fields including `time_of_day`, `start_time`, `end_clock_time`, and drive clocks. In that source 2.96% of `time_of_day` is missing and the last administrative row has no timestamp. These fields describe event/clock timing, not guaranteed final-statistic publication or revision availability. No authoritative, complete historical final/publication field was established. Taking the maximum play timestamp would invent availability guarantees; this implementation does not do that.

Fallback availability is actual recorded kickoff + eight hours. Features use **strictly earlier** kickoff and availability than cutoff. A timezone-aware `result_available_at` optional schedule column can supply a verified final-availability time; values before kickoff are rejected. This override must come from an independently verified source or reviewed local input. It is not auto-derived from play clocks. Suspended, postponed, canceled and in-progress statuses block inclusion; ingestion also removes their training targets even if scores are populated. An extraordinary suspension not identified by source status cannot be solved by a duration proxy. No assertion of a complete point-in-time replay is made.

## Feature inventory

Each statistical source is available only after the preceding game's availability time. Each rating uses current-season eligible games plus four pseudo-games from the previous season, regressed halfway toward that previous-season league mean. Current-game and later-game rows are excluded. All descriptions below apply independently to both teams; the modeled value is home minus away, with defensive signs reversed.

| Feature | Source and calculation | Earliest availability/cutoff | Missing values and risks |
|---|---|---|---|
| off_epa | Eligible scrimmage EPA mean per game, then average game means | Prior game's final proxy/verified time < cutoff | Missing game EPA excluded from count; prior or training-only imputation; revised EPA risk |
| def_epa | Opposing possession team's EPA mean against defense | Same rule, never current game | Sign reversed; same imputation/revision risk |
| scoring | Final points scored minus allowed, mean per game | Score final proxy/verified time < cutoff | No valid scores means no completion/target; late score corrections are retrospective |
| turnover | Defensive takeaways minus offensive giveaways on eligible scrimmage plays | Prior game's availability < cutoff | Missing metrics stay NaN; unknown turnover indicators use upstream zero-event encoding; special teams omitted |
| off_success | Fraction of eligible scrimmage plays with EPA > 0, mean game fractions | Prior game's availability < cutoff | Missing EPA rows excluded; incomplete PBP can bias rate |
| def_success | Opponent success fraction against defense | Prior game's availability < cutoff | Sign reversed; incomplete PBP/revisions remain risks |
| win | Final win fraction (tie=0.5), mean eligible games | Score final proxy/verified time < cutoff | Ties excluded only from binary target; missing history uses prior/imputer |
| off_yards | Eligible yards gained/play, mean game rates | Prior game's availability < cutoff | Missing stays NaN; ignores special teams, correlated with efficiency |
| def_yards | Opponent eligible yards/play | Prior game's availability < cutoff | Sign reversed, same missing/revision risks |
| recent_off_epa | Last three eligible current-season games, shrunk with four prior games | Select history before cutoff first, then tail(3) | NaN metrics omitted, no future league mean |
| recent_def_epa | Same rolling rule for defensive EPA | Same cutoff-first rule | Sign reversed; correlated with season-to-date EPA |
| rest | Days from last eligible kickoff to cutoff | Last game must be available before cutoff | No history yields NaN; at early live cutoffs uses elapsed rest rather than future scheduled rest |
| neutral | Schedule venue designation (`location == Neutral`) | Known current schedule at retrieval, applied to game row | Missing location currently defaults to home (M1 compatibility); historical venue revisions lack vintage proof |

There is no prior before 2018. Missing priors use available current means or remain NaN. The imputer learns means from training games only, with zero for an entirely missing training column. This is a preprocessing fallback, not fabricated source data. StandardScaler and logistic coefficients also fit only training rows. Mean game rates weight games equally, not all plays equally.

## Function review and tests

`team_games()` joins unique team-game metrics to completed regular-season schedules and assigns availability. `rating()` filters by availability and kickoff *before* prior/rolling aggregation. `build()` uses min(actual kickoff, explicitly supplied cutoff). Deliberate current/future statistics injection is tested at both feature and prediction levels. Tests cover short rest/Thursday–Sunday, Monday/holiday spacing, overlapping games, explicit delayed finals, suspension, postponed scores, missing PBP, malformed schemas, corrected histories and immutable original forecasts. Exact equality at availability is conservatively excluded.

Cached sources are retrospective nflverse revisions. A later revision may change regenerated historical features, but cannot rewrite issued SQLite forecast payloads. The original champion can still be loaded; M2 never updates its artifact or database. Calibration uses base-model predictions from an earlier, separate calibration season and evaluates strictly later. M1's already-inspected 2024–2025 period is explicitly exploratory in M2.

## Cache protocol and remaining limits

M2 writes immutable season generations (raw PBP, normalized schedules and metrics), verifies Parquet round-trips, hashes files, then atomically replaces one manifest pointer. Schema version, retrieval timestamp, columns, rows and previous generation are recorded. Failed downloads/writes do not publish half a season. Old generations remain available for explicit corruption recovery; they are not silently substituted. SHA-256 detects local changes, not upstream truth or original publication times. Existing M1 caches are adopted with a current integrity hash and retained retrieval timestamp; this does not reconstruct their historical source vintages. Orphan staging generations after interrupted writes can consume disk and require manual cleanup.

Reads verify hashes, keys and timezone-aware kickoff schemas. Feature caches key the source dataframe content plus feature code, check their own checksum, and rebuild only for a changed key or explicit refresh. Missing team-game PBP triggers warnings. Newly aggregated metrics also record eligible-play counts and flag fewer than 40 plays for review; that heuristic cannot certify full coverage. Checksums cannot detect semantically incomplete upstream data. Current-season stale warnings use current-season retrieval metadata, rather than the newest unrelated historical retrieval.

No 2026 prospective performance is manufactured: Model Analysis reads saved official records and attached binary outcomes through read-only SQLite. There are currently no resolved attached outcomes, so independent prospective confirmation remains pending.
