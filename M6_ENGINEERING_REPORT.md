# M6 engineering report

## Baseline and implementation

M6 adds cutoff-specific opponent-adjusted EPA/success, matchup features, retrospective QB dropback performance and a versioned pregame personnel evidence ledger. The M5 2008/uniform shallow-HGB configuration is fixed. No additional window search, new algorithm, ensemble, sportsbook integration or M7 implementation was performed. Original champion, forecast SQLite, source caches, registry, Elo histories and prior reports are preserved.

The supplied brief reports M5 Windows acceptance. No independently supplied Windows JSON was available here; M6 native Windows execution is not claimed. The actual starting suite has 91 tests, not 86: five preflight/quoting regression tests were added after the M5 engineering handoff. Baseline fingerprints are in docs/m6/BASELINE.json.

## Opponent-adjustment equations and assumptions

For each eligible offensive team-game rate y against defense j: y = mu + O_i + D_j. D is efficiency ALLOWED; negative D means stronger defense. mu is the current eligible league mean with four prior-league pseudo-observations. Previous-season team offense/defense means regress halfway toward that eligible prior-season league mean. Missing franchise history uses neutral relative strength; no earlier source statistics are fabricated.

At each of eight simultaneous Jacobi iterations: O_i_new = [w*O_i_prior + sum(y−mu−clip(D_opponent))]/(w+n_i); D_j_new = [w*D_j_prior + sum(y−mu−clip(O_opponent))]/(w+n_j). Updates use 0.5 damping and bounded strengths/opponent terms (EPA ±0.5; success ±0.2). w=4 game observations. Teams without games retain their regularized prior and report zero current samples. This is an additive, game-weighted approximation, not a causal opponent correction or an empirically optimal model.

The solver never reads season-end ranks to initialize earlier weeks. All observations, league means, priors and opponent strengths are filtered by BOTH earlier kickoff and result eligibility before iteration. Contemporaneous re-estimation may use later games than an opponent’s past matchup only when those later games are already eligible before the current prediction cutoff. Same-time results are excluded. M5 date-only lower/availability bounds and the eight-hour proxy remain in force.

## Feature perspectives and independent experiments

Adjusted offensive difference is O_home−O_away. Defensive advantage is D_away−D_home, so stronger home defense is positive. Home matchup EPA is mu+O_home+D_away, away matchup EPA is mu+O_away+D_home. Success follows the same equations with displayed matchup values clipped to [0,1]. Overall advantage is the offense plus defensive advantage. D uses the two matchup pairs instead of their exactly redundant difference; D2 uses overall EPA/success differences separately.

A preserves M5. B replaces raw season-to-date offensive/defensive EPA and success; raw recent EPA, yards and other M5 controls remain. C retains raw and adds adjusted features. D/D2 are fixed matchup alternatives. C-without-Elo, C-without-adjusted-offense and C-without-adjusted-defense are prespecified ablations. QB/personnel research is evaluated independently before any combined model.

Configuration: `{"prior_games": 4.0, "offseason_retention": 0.5, "iterations": 8, "damping": 0.5, "epa_cap": 0.5, "success_cap": 0.2}`. Four-game adjustment prior is not optimized against 2024–2025. The fixed 2/8-game sensitivity below uses 2019–2021 development outcomes only and does not replace the default.

| prior_games | training_end | validation | games | accuracy | brier | log_loss | home_win_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4.000000 | 2018 | 2019 | 255 | 0.623529 | 0.224497 | 0.641975 | 0.517647 |
| 4.000000 | 2019 | 2020 | 255 | 0.647059 | 0.217690 | 0.627408 | 0.498039 |
| 4.000000 | 2020 | 2021 | 271 | 0.597786 | 0.232672 | 0.657340 | 0.516605 |
| 2.000000 | 2018 | 2019 | 255 | 0.643137 | 0.223928 | 0.640799 | 0.517647 |
| 2.000000 | 2019 | 2020 | 255 | 0.658824 | 0.216448 | 0.623901 | 0.498039 |
| 2.000000 | 2020 | 2021 | 271 | 0.594096 | 0.232547 | 0.657521 | 0.516605 |
| 8.000000 | 2018 | 2019 | 255 | 0.627451 | 0.221570 | 0.634681 | 0.517647 |
| 8.000000 | 2019 | 2020 | 255 | 0.635294 | 0.220620 | 0.633641 | 0.498039 |
| 8.000000 | 2020 | 2021 | 271 | 0.594096 | 0.231983 | 0.656014 | 0.516605 |

## Historical coverage and leakage audit

| season | adj_off_epa_diff | adj_def_epa_advantage | adj_off_success_diff | adj_def_success_advantage | home_matchup_epa | away_matchup_epa | home_matchup_success | away_matchup_success | qb_expected_epa_difference | qb_change_gap_difference | qb_recent_epa_difference | qb_experience_difference | ol_unavailable_starters_advantage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1999 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2001 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2002 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2003 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2004 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2005 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2006 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2007 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2008 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2009 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2010 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2011 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2012 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2013 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2014 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2015 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2016 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2017 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2018 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2019 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2020 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2021 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2022 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2023 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2024 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2025 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2026 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

Source schedules and compact team metrics cover 1999–2026. The first initialization season lacks a preceding NFL history and adjusted values there are neutral regularized priors, not observed zero statistics. Unknown 1999 clocks use M5 conservative date bounds. Strict cutoff-specific caches hash data, parameters, code and cutoff; future outcomes cannot rewrite a previously generated earlier snapshot. Adversarial tests explicitly strengthen a previously faced opponent later in the season and verify earlier features/predictions do not change. Tests also cover delayed results, simultaneous kickoffs, signs, priors and deterministic fixed iterations.

## Measured 2024–2025 comparisons, already examined

| model | accuracy | brier | log_loss |
| --- | --- | --- | --- |
| A_raw | 0.664825 | 0.214954 | 0.618001 |
| B_replacement | 0.659300 | 0.217153 | 0.622854 |
| C_isotonic | 0.650092 | 0.217832 | 0.622233 |
| C_raw_adjusted | 0.661142 | 0.216374 | 0.621167 |
| C_sigmoid | 0.653775 | 0.218721 | 0.627158 |
| C_without_adjusted_defense | 0.659300 | 0.216304 | 0.621218 |
| C_without_adjusted_offense | 0.657459 | 0.215264 | 0.618444 |
| C_without_elo | 0.650092 | 0.217516 | 0.623370 |
| D2_overall | 0.664825 | 0.215420 | 0.619357 |
| D_matchups | 0.653775 | 0.216920 | 0.623540 |
| logistic | 0.644567 | 0.220954 | 0.631279 |

Direct Brier differences from M5 A:

| model | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- |
| A_raw | 0.214954 | 0.000000 | 0.000000 | 0.000000 | 543 |
| B_replacement | 0.217153 | 0.002200 | 0.000647 | 0.003977 | 543 |
| C_isotonic | 0.217832 | 0.002879 | -0.001722 | 0.006921 | 543 |
| C_raw_adjusted | 0.216374 | 0.001420 | -0.000008 | 0.003027 | 543 |
| C_sigmoid | 0.218721 | 0.003767 | 0.000240 | 0.007083 | 543 |
| C_without_adjusted_defense | 0.216304 | 0.001350 | 0.000110 | 0.002807 | 543 |
| C_without_adjusted_offense | 0.215264 | 0.000311 | -0.000452 | 0.001167 | 543 |
| C_without_elo | 0.217516 | 0.002563 | 0.000407 | 0.004853 | 543 |
| D2_overall | 0.215420 | 0.000467 | -0.002301 | 0.003045 | 543 |
| D_matchups | 0.216920 | 0.001966 | -0.000593 | 0.004377 | 543 |
| logistic | 0.220954 | 0.006000 | 0.000335 | 0.011661 | 543 |

Complete accuracy/log-loss intervals and each season are in comparison.csv, vs_m5.csv and MODEL_COMPARISON.md. Calibration is diagnostic or fitted in a separate intervening year; no transformation sees evaluation labels during fitting. Reliability, probability/confidence buckets and weeks 1–3 versus later results are exported. Nominal intervals after repeated exploratory comparisons are not independent confirmation or automatic promotion evidence.

## QB historical performance

QB player-game aggregates are derived season-by-season from existing PBP: identified pass/sack/scramble dropbacks, excluding kneels/spikes and missing EPA. GSIS passer IDs are preserved; scramble rusher IDs are used only where the source explicitly identifies a QB scramble. Multiple QBs per game are retained. Team changes do not reset a player’s identity. Player stats/participation/rosters were inspected as source audits; no retrospective row establishes a pregame starter.

The rating pools a player’s eligible current/prior-season dropbacks and shrinks EPA and success toward the corresponding eligible league rates with 80 pseudo-dropbacks. Recent EPA is sample-weighted over the last three eligible player-games. Career dropbacks provide experience context. The reported 1/sqrt(n+80) is a sample-size uncertainty index, not a calibrated probability/confidence interval. No recent sample means unknown performance, not poor performance or an automatic zero. CPOE/optional rates are descriptive where available and are not forced into historical comparison.

A previous starter is the QB observed in the most recent eligible completed schedule entry. The context records player/team/game, eligibility and retrospective quality; it never confirms the next starter. Expected-minus-previous strength can be positive or negative: a replacement is not automatically worse. Only verified designation plus known prior performance may form historical QB predictors.

## Availability, coverage and prospective tracking

The evidence schema stores target game/team/player/position, source name/reference, publication/observation time, declared forecast cutoff, status, verification and quality. Statuses are confirmed starter, evidenced likely starter, questionable, ruled out or unknown. Both times must strictly precede the declared and calculation cutoffs; the declared cutoff cannot be later than the calculation cutoff. Missing timestamps/references are unverified or rejected as malformed verified claims. Equally recent conflicts remain unknown; a newer ruled-out report supersedes an older starter claim. Operator verification records evidence assertions, not software authentication of those sources.

A separate immutable-generation personnel ledger preserves old imports. Prospective context snapshots record actual creation time and can be saved only for genuinely unstarted games; they are context records, not winner predictions, and never alter official SQLite forecasts. Imported old evidence may support a retrospective reconstruction but is never backdated as a genuinely issued forecast.

Position groups OL/WR/RB/TE/DL/LB/DB are supported. Verified unavailable-player counts are descriptive. Zero unavailable starters is allowed only when a verified report explicitly covers that position group and unavailable-player starter roles are known. Otherwise coverage/counts remain unknown; a missing injury report never means healthy. F initially tests OL unavailable starters only if complete matched report scopes exist. Participation rows are prior-performance context only; source schemas or name-based PFR IDs cannot be silently treated as verified GSIS evidence.

| evaluation | experiment | status | kind | training_games | evaluation_games | training_coverage | evaluation_coverage | training_seasons | evaluation_seasons | qb_changes | meaningful_absences | missing_status_fraction | verified_starter_team_fraction | timestamp_rule |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | E_qb | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2022 | F_ol | skipped_insufficient_verified_coverage | player | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2022 | G_adjusted_qb_ol | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2023 | E_qb | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2023 | F_ol | skipped_insufficient_verified_coverage | player | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2023 | G_adjusted_qb_ol | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2024 | E_qb | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2024 | F_ol | skipped_insufficient_verified_coverage | player | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2024 | G_adjusted_qb_ol | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2025 | E_qb | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2025 | F_ol | skipped_insufficient_verified_coverage | player | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |
| 2025 | G_adjusted_qb_ol | skipped_insufficient_verified_coverage | qb | 0 | 0 | 0.000000 | 0.000000 | [] | [] | 0 | 0 | 1.000000 | 0.000000 | publication AND observation before declared and feature cutoffs; verified reference required |

E uses matched verified QB performance/availability, F matched OL coverage, and G fixed B+QB+OL only if both independent studies qualify. Training/evaluation counts, seasons, missing fractions, changes and absences are explicit. Skipped coverage is an acceptable result and does not mean absence of a football effect. No full-sample versus personnel-subset accuracy comparison is allowed.

Personnel source audit summary: `{"evidence_records": 0, "verified_claims": 0, "source_timestamp_classification": {}, "note": "M3 historical depth/roster/injury snapshots are not independently verified pregame evidence. No automatic upgrade or fabricated starter identity."}`. Per-season QB performance availability is recorded in reports/personnel_audit/coverage.json.

## Interpretation and uncertainty

| model | group | brier_increase |
| --- | --- | --- |
| D_matchups | feature:scoring | 0.006262 |
| C_raw_adjusted | feature:scoring | 0.004530 |
| D_matchups | feature:elo_difference | 0.003676 |
| C_raw_adjusted | feature:elo_difference | 0.003145 |
| C_raw_adjusted | elo | 0.002936 |
| C_raw_adjusted | adjusted_offense | 0.002912 |
| D_matchups | elo | 0.002684 |
| D_matchups | adjusted_matchups | 0.001641 |
| C_raw_adjusted | feature:adj_off_epa_diff | 0.001526 |
| D_matchups | feature:off_yards | 0.001390 |
| D_matchups | feature:recent_off_epa | 0.001019 |
| D_matchups | feature:away_matchup_success | 0.000607 |
| C_raw_adjusted | feature:recent_def_epa | 0.000463 |
| C_raw_adjusted | feature:recent_off_epa | 0.000370 |
| D_matchups | feature:away_matchup_epa | 0.000287 |
| C_raw_adjusted | adjusted_defense | 0.000251 |
| D_matchups | feature:win | 0.000243 |
| C_raw_adjusted | feature:off_epa | 0.000239 |
| C_raw_adjusted | raw_success | 0.000238 |
| C_raw_adjusted | feature:adj_off_success_diff | 0.000188 |
| D_matchups | feature:recent_def_epa | 0.000128 |
| C_raw_adjusted | feature:off_yards | 0.000128 |
| C_raw_adjusted | feature:adj_def_success_advantage | 0.000107 |
| C_raw_adjusted | feature:win | 0.000091 |
| C_raw_adjusted | raw_epa | 0.000070 |
| D_matchups | feature:neutral | 0.000057 |
| C_raw_adjusted | feature:off_success | 0.000050 |
| C_raw_adjusted | feature:turnover | 0.000044 |
| C_raw_adjusted | feature:adj_def_epa_advantage | 0.000009 |
| C_raw_adjusted | feature:def_yards | -0.000016 |

These held-out permutation loss changes and fixed group ablations diagnose incremental model use. EPA, adjusted EPA, success, yards and Elo are correlated; individual and group importance is not causation. Future postseason/final-season results, eventual current starters and current-game participation are not model inputs. Paired season-week bootstrap uncertainty is unadjusted and limited by repeated teams, correlated weeks, few independent seasons and prior examination of 2024–2025.

## Performance, registry and preservation

Efficiency configurations: 8; forward fits 32; measured total fit seconds 36.702. Feature/audit preparation seconds: 3.2107802810005523. Peak process RSS bytes where supported: 337223680. Times are machine-specific; CPU-only, no new dependencies or GPU required.

Historical adjustment and player statistics are cached separately by source/configuration/code/cutoff; raw PBP is not rescanned for each candidate. Normal Streamlit rendering reads precomputed snapshots/context only and never trains models. Context lookup can compute a small current cutoff state from compact past team-games, not the full PBP archive.

Registry entries retain adjustment version/parameters, cutoff rules, data fingerprints, personnel coverage, feature sets, fixed window, model version and evaluation reference. Every new model is experimental and activation-blocked. M5/M4 registry loading, rollback and old serialized pipelines remain compatible. No schema migration or official forecast rewrite occurred.

## Verification and Windows status

```json
{
  "checked_at": "2026-11-03T14:23:58.597123+00:00",
  "status": "Implemented and verified on Linux; native M6 Windows acceptance outstanding. Personnel experiments correctly skipped for unavailable verified evidence.",
  "baseline_tests": {
    "passed": 91,
    "note": "Brief counted 86 before five later preflight regressions"
  },
  "complete_suite": {
    "command": "python -m pytest -q",
    "passed": 106,
    "warnings": 7,
    "seconds": 130.55,
    "platform": "Linux Python 3.12.14",
    "log": "docs/m6/PYTEST.txt"
  },
  "post_ui_and_windows_script_checks": {
    "command": "python -m pytest -q tests/test_m6.py tests/test_windows_preflight.py",
    "passed": 20,
    "warnings": 1,
    "seconds": 27.06
  },
  "local_acceptance": {
    "platform": "Linux-6.18.57-x86_64-with-glibc2.41",
    "python": "3.12.14 (main, Aug 25 2026, 14:00:49) [Clang 22.1.3 ]",
    "native_windows": false,
    "checked_at": "2026-11-03T14:19:53.197497+00:00",
    "checks": {
      "champion_load": "passed",
      "upcoming_predictions": "passed",
      "Upcoming Games": "passed",
      "Team Comparison": "passed",
      "Model Performance": "passed",
      "Model Analysis": "passed",
      "Team Power Rankings": "passed",
      "registry_load": "passed",
      "preservation": "passed"
    },
    "champion_version": "20261103T043653-6d77120a",
    "upcoming_count": 151,
    "registered_candidates_loaded": 696,
    "preserved_artifacts": 1402,
    "status": "Review required; no automatic Windows certification. Native Windows, full data/model steps, manual UI startup and RAM behavior must all be verified."
  },
  "additional_ui": {
    "scheduled_matchup": "passed prior to HTTP sandbox restriction",
    "unknown_personnel_display": "passed",
    "native_windows": false,
    "streamlit_http_health": "passed"
  },
  "registry_candidates_loaded_at_final_check": 736,
  "new_m6_registered_artifacts": 40,
  "all_new_m6_candidates_activation_blocked": true,
  "existing_artifacts_preserved": 1509,
  "changed_existing_artifacts": [],
  "cache_reuse": {
    "command": "python -m nfl_predictor.cli report-m6",
    "cache_reused": true,
    "run": "79fbd590dfc512c8",
    "seconds": 5.647426858000472,
    "report_files_unchanged": 17
  },
  "initial_opponent_snapshot_build": {
    "games": 7239,
    "seconds": 26.25
  },
  "actual_player_performance": {
    "seasons": "1999\u20132026",
    "season_count": 28,
    "player_game_team_rows": 17532,
    "classification": "retrospective prior-game performance; not verified future starter evidence"
  },
  "verified_personnel_evidence": {
    "records": 0,
    "E": "skipped",
    "F": "skipped",
    "G": "skipped"
  },
  "limitations": [
    "Native Windows M6 execution not available; M5 acceptance user-reported only.",
    "Cached 2026_08_CHI_SEA lacks eligible PBP metrics; no zero replacement or forecast rewrite.",
    "1999 lacks kickoff clocks; M5 conservative time bounds retained.",
    "No examined adjusted-efficiency variant improved fixed M5 A Brier on 2024\u20132025; no promotion.",
    "2024\u20132025 is repeatedly examined exploratory evidence; nominal intervals unadjusted."
  ]
}
```

M5 native acceptance is user-reported in the brief. M6 native Windows execution remains outstanding when this task runs only on Linux. The PowerShell preflight quoting fix is preserved; tests cover source-ZIP compatibility and cross-platform pure logic without claiming those are genuine Windows runs.

## Reproduction and limitations

From the active environment: `python -m nfl_predictor.cli build-adjusted-efficiency`; `python -m nfl_predictor.cli audit-personnel`; `python -m nfl_predictor.cli compare-m6`; `python -m nfl_predictor.cli report-m6`; `python -m pytest -q`; `python -m streamlit run app.py`. Optional `--cutoff` is timezone-aware. Verified evidence is imported with `import-personnel --evidence-file PATH`; `snapshot-personnel --game-id ID` records genuine future context without changing official forecasts.

Measured run: `reports/m6/79fbd590dfc512c8`. No historical personnel effect is claimed without coverage. Historical EPA/model vintages, publication times, date-only source bounds, incomplete early PBP and unknown extraordinary suspensions remain limitations. Regularized adjustment assumptions are not established causal schedule corrections. Keep the M2 champion and all M6 alternatives experimental.

## M7 recommendations

Collect genuine timestamped prospective personnel evidence, validate current cutoff snapshots on native Windows, assess adjustment stability over future unexamined games and retain provenance before considering ensembles or promotion. M7 was not started.
