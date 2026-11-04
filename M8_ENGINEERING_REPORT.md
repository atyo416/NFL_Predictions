# M8 engineering report

## Implementation and preservation

M8 adds an independent NFL moneyline research lab: read-only provider adapter, immutable normalized same-book pairs, CSV/JSON import, exact event matching, timestamped forecast references, no-vig/EV mathematics, fixed one-unit paper strategies, append-only settlements/corrections, market benchmarking, CLV and a Betting Lab page. No sportsbook accounts, payments, real-money execution, ML training, ensemble optimization or M9 functionality was added.

M7 baseline fingerprints and source hashes are in docs/m8/BASELINE.json. The M2 champion, official SQLite, M3 ratings, M4–M7 artifacts and all 151 previously issued M7 forecasts are preserved. Existing commands remain covered by regression tests. M8 reads official SQLite with mode=ro and creates only data/m8/lab.db.

## Provider verification and data availability

```json
{
  "reviewed_at": "2026-11-04T03:11:50.526017+00:00",
  "official_references": [
    {
      "url": "https://github.com/the-odds-api/samples-python/blob/master/odds.py",
      "sha256": "b134e97ee935c2820b26c0e23c55dbc4b64960c3b128e443ca7ea2b5e6a0c2d8",
      "bytes": 2955
    },
    {
      "url": "https://github.com/the-odds-api/apps-script/blob/master/Odds.gs",
      "sha256": "3432db119e12c872292a78b43fc03a369d6e73c92ae62adc5a103d90bea03cc4",
      "bytes": 5255
    },
    {
      "url": "https://github.com/the-odds-api/apps-script/blob/master/HistoricalOdds.gs",
      "sha256": "114905e6801ca1c07b512f39d1c298927810468a0b7de8bfe21e7c42a0d17ade",
      "bytes": 6157
    },
    {
      "url": "https://github.com/the-odds-api/apps-script/blob/master/ClosingLinesFeaturedMarkets.gs",
      "sha256": "00f052238bf23900acd6466932bad0561cf18d51f463f713fe868be90736782c",
      "bytes": 8641
    }
  ],
  "verified_contract": {
    "endpoint": "GET /v4/sports/americanfootball_nfl/odds",
    "parameters": [
      "apiKey",
      "regions=us",
      "markets=h2h",
      "oddsFormat=american",
      "dateFormat=iso"
    ],
    "fields": [
      "id",
      "commence_time",
      "home_team",
      "away_team",
      "bookmakers[].key",
      "bookmakers[].last_update",
      "bookmakers[].markets[].key",
      "bookmakers[].markets[].outcomes[].name",
      "bookmakers[].markets[].outcomes[].price"
    ],
    "historical_envelope": [
      "timestamp",
      "data"
    ],
    "quota_headers_documented": [
      "x-requests-used",
      "x-requests-remaining"
    ],
    "optional_header_recorded_if_present": "x-requests-last; not observed live",
    "published_example_live_cost": "number of markets times number of regions",
    "published_example_historical_cost": "10 times markets times regions; no historical network fetch implemented"
  },
  "limitations": [
    "Official guide URL https://the-odds-api.com/liveapi/guides/v4/ was blocked by active proxy HTTP 403.",
    "A network domain draft was saved but publication/application is not established by saving it.",
    "ODDS_API_KEY was absent. No authenticated request, remaining quota, live prices or paid history was observed.",
    "Current official GitHub code/documentation was inspected instead of relying on an old third-party response. Contract fixtures remain explicitly synthetic."
  ],
  "runtime_configuration_instruction": {
    "skill": "cloud-environment:cloud-environment-runtime",
    "source": "skill://plugin_connector_1p_c5b7d5df5d7081918f2c4be5a633ed5d/cloud-environment-runtime/SKILL.md",
    "instruction": "Configuration changes require the environment configuration workflow and its user review.",
    "effect": "Network draft saving alone does not activate access; independent offline implementation continued."
  }
}
```

The adapter uses apiKey, regions=us, markets=h2h, oddsFormat=american, dateFormat=iso. It does not request unrelated sports or paid historical endpoints. Official current GitHub examples confirmed event/bookmaker/market nesting, publication timestamps, historical timestamp/data envelopes and x-requests-used/remaining; x-requests-last is captured only if returned. The published current-example cost formula is markets×regions for this endpoint (one×one); no actual quota balance or charge is claimed without live observations.

An environment network draft was saved for the-odds-api.com and api.the-odds-api.com; draft saving is not network activation. Review/save and Publish in environment settings is required to apply it. No credential value was requested, printed, stored or committed. Local Windows users can set ODDS_API_KEY themselves. Missing API credentials or paid archive access does not block imports, tests, existing prediction pages or offline reports.

## Normalization, matching and time semantics

A normalized quote contains both selections from one event/book/market object and coherent timestamps. Quote publication/version time, provider snapshot time and actual capture/import time are distinct. Live responses use market or bookmaker update time as snapshot version; historical envelopes retain the provider archive time. Repeated unchanged quotes retain their first raw reference/capture; receipt events record later retrievals. Raw source bytes and hashes remain immutable. CSV needs two coherent selection rows with identities, aware times, season, source reference and prices. Undated or unverified history cannot enter verified research.

Exact canonical team mapping includes current names and relocated/renamed aliases. Automatic matching requires designated home/away, NFL season and kickoff within five minutes; neutral games retain their designated teams. Reversed sides, rescheduled kickoffs, ambiguous or duplicate provider events require review. Audits are versioned by schedule fingerprints. Later duplicate events cannot change an earlier as-of decision.

Prospective comparisons require the forecast creation/cutoff and quote publication/snapshot/capture to be known by the decision, all before kickoff. Historical archive imports are labeled reconstructed; their import time is never backdated. Cohorts are 24h/6h/1h with one-sided prior windows of 15/10/5 minutes. Later snapshots are excluded, including near-closing prices. Existing M7 kickoff features are too late for earlier cohorts; optional reconstruction uses new as-of features with frozen annual M7 artifacts, never retraining.

M8 distinguishes actual M2 champion saved forecasts (original/revised source designation retained), M5-architecture boosting from M7 annual refits, and the fixed M7 ensemble. Historical logistic inference is labeled M2-architecture OOS refit, not a genuinely issued champion forecast. Missing artifacts/probabilities are exclusions, never substituted 0.5.

## Probability, EV, rules and uncertainty

American +A maps to 1+A/100, −A to 1+100/abs(A); decimal arithmetic validates finite canonical quotes. Raw break-even probability is 1/D. Same-book overround is raw_home+raw_away and margin=overround−1. Proportional no-vig divides each raw probability by that sum; it is a convention, not truth. EV=pD−1 per unit, separate from percentage-point model/no-vig disagreement. +150 gives D=2.5; p=.45 gives EV=.125 per unit. These are arithmetic examples, not verified market opportunities.

NFL binary models omit ties. EV is a conditional no-tie scenario; it is not an unconditional return forecast. Paper issuance requires documented game-including-overtime scope and tie push/void rules. Unknown or tie-loss/three-way rules block issuance. Missing cancel/reschedule rules cause manual review rather than invented outcomes. Quoted prices are not claimed executable. Probability shifts ±2/±5 percentage points are sensitivity scenarios, not calibrated confidence intervals.

## Measured real-data status

```json
{
  "actual_quote_pairs": 0,
  "synthetic_quote_pairs": 0,
  "available_saved_forecasts": 453,
  "match_status_counts": {},
  "comparison_rows": 0,
  "real_matched_probability_games": 0,
  "real_matched_rows": 0,
  "benchmark_status": "unavailable_no_genuine_matched_graded_market_data",
  "provider": {
    "credential_configured": false,
    "requests_attempted": 0,
    "last_fetch": null,
    "last_success_at": null,
    "quota": null,
    "implementation_documentation_review": "The implementation environment blocked the direct official guide with HTTP 403; current official GitHub provider examples were reviewed. See docs/m8/PROVIDER_REVIEW.json. Current fetch/quota observations, if any, are listed separately."
  },
  "paper_summary": {
    "wagers": 0,
    "unique_games": 0,
    "wins": 0,
    "losses": 0,
    "pushes": 0,
    "voids": 0,
    "pending": 0,
    "review": 0,
    "total_stake_units": 0,
    "settled_stake_units": 0,
    "net_simulated_profit_units": null,
    "realized_roi": null,
    "average_model_ev": null,
    "maximum_drawdown_units": null,
    "longest_losing_streak": null,
    "roi_convention": "Settled stake includes refunded push/void entries; pending stakes excluded",
    "drawdown_convention": "Aggregate equal availability timestamps before equity updates; losing streak ties use game ID; pushes do not reset streak"
  },
  "reconstructed_summary": {
    "wagers": 0,
    "unique_games": 0,
    "wins": 0,
    "losses": 0,
    "pushes": 0,
    "voids": 0,
    "pending": 0,
    "review": 0,
    "total_stake_units": 0,
    "settled_stake_units": 0,
    "net_simulated_profit_units": null,
    "realized_roi": null,
    "average_model_ev": null,
    "maximum_drawdown_units": null,
    "longest_losing_streak": null,
    "roi_convention": "Settled stake includes refunded push/void entries; pending stakes excluded",
    "drawdown_convention": "Aggregate equal availability timestamps before equity updates; losing streak ties use game ID; pushes do not reset streak"
  },
  "storage": {
    "raw_responses": 0,
    "raw_bytes": 0,
    "database_bytes": 692224
  }
}
```

Actual genuine market performance is unavailable when matched prices/outcomes are absent. No real odds history, bet return or profitability is fabricated. All-game M7 accuracy is not used as matched market evidence. CSV import and offline synthetic verification work without paid historical access.

## Strategies, ledger, settlement and CLV

Default paper policy is champion logistic, EV strictly >3%, one simulated unit, fixed book priority then lexical identity, higher-EV side and home on ties. >0%/>3%/>5% and other model families are distinct sensitivity strategy versions, not outcome-optimized winners. Opportunity identity is game+strategy+timing cohort. Quotes, stake and probability never change after saving. Dry run writes no wagers. Corrections and changed official results append events with supersession references; manual void requires a reason.

Wins return stake*(D−1) profit, losses −stake, documented pushes/voids zero. Pending/review remain ungraded. ROI divides settled profit by settled stake including refunds; it is undefined without settlements. Drawdown aggregates equal availability timestamps before equity changes; streak ties sort by game ID. Strategy/book/model/cohort/season reports retain unique-game counts and correlated exposure is not treated as independent observations.

Verified CLV needs an explicitly evidenced final pregame snapshot within ten minutes, same provider/book/event/side/scope/tie rules. Merely last-observed prices are not certified closing. EntryD/closingD−1 and no-vig movement are descriptive; unavailable closing lines remain unavailable. Later closing prices never enter entry decisions.

## Benchmarking and diagnostics

| model | metric | estimate | difference | difference_low | difference_high | cohort | games |
| --- | --- | --- | --- | --- | --- | --- | --- |

Matched scoring uses identical games for all three model families and same-book no-vig, one selected book per game/cohort. Brier, log loss, accuracy, calibration buckets/slopes and paired season-week bootstrap intervals are exported when genuine graded data exist. Separate cohorts are not pooled as independent games. Repeated teams, small samples, exploratory 2024–2025 reuse and threshold sensitivity limit inference. No operational policy is selected from evaluated P&L.

## Synthetic verification and operation

tests/fixtures/m8/provider_v4.json contains explicitly artificial prices/events and a synthetic bookmaker. demo-m8 runs the real parsing/comparison/strategy/settlement code in an isolated temporary database, with synthetic classifications throughout. Its outputs verify software only and are excluded from actual market scores.

```powershell
python -m nfl_predictor.cli import-odds --odds-file reviewed_quotes.csv
python -m nfl_predictor.cli fetch-odds
python -m nfl_predictor.cli audit-odds
python -m nfl_predictor.cli compare-market
python -m nfl_predictor.cli issue-paper-bets --dry-run
python -m nfl_predictor.cli issue-paper-bets
python -m nfl_predictor.cli settle-paper-bets
python -m nfl_predictor.cli report-m8
python -m nfl_predictor.cli demo-m8
python -m pytest -q
python -m streamlit run app.py
```

fetch-odds is optional and explicit; configure a local ODDS_API_KEY first. Imported rules require source references; provider responses alone do not establish house rules. Dashboard rendering only reads local data; no fetch, model fit or wager issuance occurs when opening a page. No continuous polling is implemented.

## Verification, runtime and Windows exception

```json
{
  "checked_at": "2026-11-04T03:44:03.106804+00:00",
  "status": "Implemented and verified on Linux; live provider/account, genuine market performance and native Windows acceptance remain unverified.",
  "baseline_tests": {
    "passed": 129,
    "warnings": 8,
    "seconds": 174.38,
    "matches_M7_report": true
  },
  "complete_tests": {
    "command": "python -m pytest -q",
    "passed": 175,
    "new_tests": 46,
    "warnings": 8,
    "seconds": 162.04,
    "platform": "Linux Python 3.12.14",
    "log": "docs/m8/PYTEST.txt"
  },
  "original_artifacts_preserved": 3486,
  "changed_original_artifacts": [],
  "champion_sha256": "34031d18cb2a1e94a511f11061070ebda07eb95491e34f0e9a70f2709a8370a8",
  "official_sqlite_sha256": "3a56d523b930a4aa0ed40bcdb07c74bd0ffa74527d7bd9576b0260ffe6dc4ebd",
  "M7_policy": "E1_equal__raw preserved; no refit or reselection",
  "M7_forecast_count_preserved": 151,
  "old_registry_candidates_loaded": 1099,
  "local_acceptance": {
    "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
    "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
    "native_windows": false,
    "checked_at": "2026-11-04T03:26:54.948178+00:00",
    "checks": {
      "champion_load": "passed",
      "upcoming_predictions": "passed",
      "Upcoming Games": "passed",
      "Team Comparison": "passed",
      "Model Performance": "passed",
      "Model Analysis": "passed",
      "Team Power Rankings": "passed",
      "Betting Lab": "passed",
      "registry_load": "passed",
      "M7_forecast_ledger": "passed",
      "M8_SQLite_integrity": "passed",
      "M8_offline_fixture_pipeline": "passed",
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
    "M8_quote_pairs": 0,
    "M8_paper_wagers": 0,
    "M8_demo_classification": "Synthetic software verification only; no real market results",
    "preserved_artifacts": 2359,
    "status": "Review required; no automatic Windows certification. Native Windows, full data/model steps, manual UI startup and RAM behavior must all be verified."
  },
  "UI_smoke": {
    "Betting_Lab": "passed",
    "tab_count": 5,
    "render_did_not_mutate_M8_database": true,
    "native_windows": false,
    "streamlit_http_health": "passed"
  },
  "nonempty_market_UI": "Offline synthetic test validates raw probabilities/margin, side-by-side models and artifact provenance without database mutation",
  "operational_commands": {
    "timings_seconds": {
      "audit": 2.1455214930028887,
      "dry_run": 2.6221827389963437,
      "zero_opportunity_issue": 1.691874098003609,
      "settlement": 2.3082048680007574,
      "demo": 1.5146409000008134,
      "report": 2.346435956998903
    },
    "commands": {
      "audit": 0,
      "dry_run": 0,
      "zero_opportunity_issue": 0,
      "settlement": 0,
      "demo": 0,
      "report": 0,
      "missing_key_guard": "verified; no authenticated request sent"
    },
    "cache_reuse": {
      "run": "05defa04e5459458",
      "cutoff": "2026-11-04T03:23:06.986440+00:00",
      "cache_reused": true,
      "seconds": 2.4290130139997927,
      "files_unchanged": 14
    },
    "live_api": "unrun: no configured key"
  },
  "real_data": {
    "saved_forecast_references": 453,
    "genuine_quote_pairs": 0,
    "paper_wagers": 0,
    "matched_graded_market_games": 0,
    "market_accuracy_brier_log_loss": null,
    "realized_simulated_roi": null,
    "verified_closing_lines": 0,
    "provider_authenticated_requests": 0,
    "quota_observations": null
  },
  "synthetic_verification": {
    "file": "docs/m8/SYNTHETIC_DEMO.json",
    "classification": "Artificial software verification, not real NFL prices/results or profitability",
    "artificial_games": 3,
    "correlated_strategy_wagers": 27,
    "unique_games": 3,
    "statuses": {
      "win": 9,
      "loss": 9,
      "push": 9
    },
    "fixture_import_deduplicated": true,
    "settlement_idempotent": true
  },
  "storage": {
    "raw_responses": 0,
    "raw_bytes": 0,
    "database_bytes": 692224
  },
  "new_direct_dependency": "requests>=2.31; requests 2.34.2 already present in unchanged lockfile",
  "dependency_check": "python -m pip check: No broken requirements found",
  "Windows_script": "scripts/windows_m8_acceptance.ps1 -Full; optional -LiveOdds; original M7 script preserved",
  "limitations": [
    "No configured ODDS_API_KEY; authenticated live schema, prices and quota were not observed.",
    "The direct official guide was blocked by proxy HTTP 403; current official provider GitHub documentation/code was inspected instead.",
    "The saved network-access draft requires review/save and publication; saving it did not apply access.",
    "No genuine historical market data supplied; genuine benchmark/returns unavailable, not fabricated.",
    "House rules require operator evidence; unknown scope/tie rules block paper issuance.",
    "Historical 2024\u20132025 remains exploratory; inference uses earlier cutoff-specific features and frozen artifacts.",
    "Native M6/M7/M8 Windows acceptance remains outstanding.",
    "Existing missing PBP for 2026_08_CHI_SEA remains missing and warned."
  ]
}
```

The combined PowerShell acceptance script retains M6/M7 checks and adds deterministic M8 checks. Live fetching is opt-in via -LiveOdds. Linux test/UI results do not certify native Windows. Runtime, storage and cache observations are machine-specific. Existing missing PBP/source-vintage and conservative final-eligibility assumptions remain.

## Handoff and M9 recommendations

Retain the M2 champion and fixed M7 policy. Collect genuine timestamped prices and paper decisions with documented market rules, then grade independent outcomes. Verify native Windows and quota behavior with a configured account. Improve dashboard navigation/readability in M9 only after real coverage exists; M9 was not started.
