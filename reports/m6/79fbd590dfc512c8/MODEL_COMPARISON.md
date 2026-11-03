# M6 exploratory model comparison

M5 A is fixed shallow HGB, 2008-onward labels, uniform weights and the original M5 common features. B replaces four raw season efficiency measures; C adds those adjusted values; D uses venue-oriented matchup pairs; D2 uses overall differentials instead. Three C ablations test Elo/offense/defense contribution. No feature winner or model is automatically promoted.

| model | metric | estimate | low | high | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_raw | accuracy | 0.664825 | 0.627052 | 0.702207 | 0.020258 | -0.001859 | 0.042514 | 543 |
| A_raw | brier | 0.214954 | 0.200596 | 0.230259 | -0.006000 | -0.011661 | -0.000335 | 543 |
| A_raw | log_loss | 0.618001 | 0.586223 | 0.652410 | -0.013279 | -0.025961 | -0.000038 | 543 |
| B_replacement | accuracy | 0.659300 | 0.613553 | 0.702206 | 0.014733 | -0.011091 | 0.041672 | 543 |
| B_replacement | brier | 0.217153 | 0.202012 | 0.233181 | -0.003801 | -0.009562 | 0.002174 | 543 |
| B_replacement | log_loss | 0.622854 | 0.588781 | 0.659309 | -0.008426 | -0.021571 | 0.005735 | 543 |
| C_isotonic | accuracy | 0.650092 | 0.607664 | 0.692728 | 0.005525 | -0.014815 | 0.027575 | 543 |
| C_isotonic | brier | 0.217832 | 0.204874 | 0.231276 | -0.003121 | -0.008608 | 0.002312 | 543 |
| C_isotonic | log_loss | 0.622233 | 0.593806 | 0.651294 | -0.009047 | -0.021052 | 0.002917 | 543 |
| C_raw_adjusted | accuracy | 0.661142 | 0.615802 | 0.703513 | 0.016575 | -0.009191 | 0.042593 | 543 |
| C_raw_adjusted | brier | 0.216374 | 0.201254 | 0.232292 | -0.004580 | -0.010288 | 0.001346 | 543 |
| C_raw_adjusted | log_loss | 0.621167 | 0.587474 | 0.657317 | -0.010112 | -0.023069 | 0.003887 | 543 |
| C_sigmoid | accuracy | 0.653775 | 0.606340 | 0.697319 | 0.009208 | -0.018282 | 0.036432 | 543 |
| C_sigmoid | brier | 0.218721 | 0.206950 | 0.231215 | -0.002233 | -0.007745 | 0.003226 | 543 |
| C_sigmoid | log_loss | 0.627158 | 0.601891 | 0.653898 | -0.004121 | -0.015981 | 0.007514 | 543 |
| C_without_adjusted_defense | accuracy | 0.659300 | 0.618068 | 0.699448 | 0.014733 | -0.009243 | 0.038747 | 543 |
| C_without_adjusted_defense | brier | 0.216304 | 0.201344 | 0.232363 | -0.004650 | -0.010100 | 0.001063 | 543 |
| C_without_adjusted_defense | log_loss | 0.621218 | 0.587845 | 0.657237 | -0.010061 | -0.022401 | 0.003738 | 543 |
| C_without_adjusted_offense | accuracy | 0.657459 | 0.616077 | 0.696629 | 0.012891 | -0.013037 | 0.037396 | 543 |
| C_without_adjusted_offense | brier | 0.215264 | 0.200729 | 0.230702 | -0.005689 | -0.011562 | 0.000262 | 543 |
| C_without_adjusted_offense | log_loss | 0.618444 | 0.586297 | 0.652919 | -0.012835 | -0.025851 | 0.001010 | 543 |
| C_without_elo | accuracy | 0.650092 | 0.604436 | 0.693589 | 0.005525 | -0.014547 | 0.024393 | 543 |
| C_without_elo | brier | 0.217516 | 0.203120 | 0.233405 | -0.003437 | -0.008588 | 0.001968 | 543 |
| C_without_elo | log_loss | 0.623370 | 0.590737 | 0.659131 | -0.007910 | -0.019883 | 0.004823 | 543 |
| D2_overall | accuracy | 0.664825 | 0.622705 | 0.702172 | 0.020258 | -0.009368 | 0.049275 | 543 |
| D2_overall | brier | 0.215420 | 0.201174 | 0.230668 | -0.005533 | -0.012287 | 0.000890 | 543 |
| D2_overall | log_loss | 0.619357 | 0.587604 | 0.654249 | -0.011923 | -0.026811 | 0.002700 | 543 |
| D_matchups | accuracy | 0.653775 | 0.611615 | 0.695173 | 0.009208 | -0.012915 | 0.034926 | 543 |
| D_matchups | brier | 0.216920 | 0.202567 | 0.232366 | -0.004034 | -0.010069 | 0.001966 | 543 |
| D_matchups | log_loss | 0.623540 | 0.591111 | 0.658629 | -0.007740 | -0.021657 | 0.006267 | 543 |
| logistic | accuracy | 0.644567 | 0.605503 | 0.681410 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | brier | 0.220954 | 0.207585 | 0.234306 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | log_loss | 0.631279 | 0.602509 | 0.659981 | 0.000000 | 0.000000 | 0.000000 | 543 |

## Direct incremental comparison against M5

| model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- |
| A_raw | accuracy | 0.664825 | 0.000000 | 0.000000 | 0.000000 | 543 |
| A_raw | brier | 0.214954 | 0.000000 | 0.000000 | 0.000000 | 543 |
| A_raw | log_loss | 0.618001 | 0.000000 | 0.000000 | 0.000000 | 543 |
| B_replacement | accuracy | 0.659300 | -0.005525 | -0.018416 | 0.007339 | 543 |
| B_replacement | brier | 0.217153 | 0.002200 | 0.000647 | 0.003977 | 543 |
| B_replacement | log_loss | 0.622854 | 0.004853 | 0.001275 | 0.008872 | 543 |
| C_isotonic | accuracy | 0.650092 | -0.014733 | -0.032668 | 0.001862 | 543 |
| C_isotonic | brier | 0.217832 | 0.002879 | -0.001722 | 0.006921 | 543 |
| C_isotonic | log_loss | 0.622233 | 0.004232 | -0.006394 | 0.013722 | 543 |
| C_raw_adjusted | accuracy | 0.661142 | -0.003683 | -0.016275 | 0.009158 | 543 |
| C_raw_adjusted | brier | 0.216374 | 0.001420 | -0.000008 | 0.003027 | 543 |
| C_raw_adjusted | log_loss | 0.621167 | 0.003166 | 0.000029 | 0.006725 | 543 |
| C_sigmoid | accuracy | 0.653775 | -0.011050 | -0.026742 | 0.003717 | 543 |
| C_sigmoid | brier | 0.218721 | 0.003767 | 0.000240 | 0.007083 | 543 |
| C_sigmoid | log_loss | 0.627158 | 0.009158 | 0.000101 | 0.017552 | 543 |
| C_without_adjusted_defense | accuracy | 0.659300 | -0.005525 | -0.016423 | 0.005505 | 543 |
| C_without_adjusted_defense | brier | 0.216304 | 0.001350 | 0.000110 | 0.002807 | 543 |
| C_without_adjusted_defense | log_loss | 0.621218 | 0.003217 | 0.000504 | 0.006411 | 543 |
| C_without_adjusted_offense | accuracy | 0.657459 | -0.007366 | -0.016544 | 0.000000 | 543 |
| C_without_adjusted_offense | brier | 0.215264 | 0.000311 | -0.000452 | 0.001167 | 543 |
| C_without_adjusted_offense | log_loss | 0.618444 | 0.000443 | -0.001279 | 0.002506 | 543 |
| C_without_elo | accuracy | 0.650092 | -0.014733 | -0.040371 | 0.009277 | 543 |
| C_without_elo | brier | 0.217516 | 0.002563 | 0.000407 | 0.004853 | 543 |
| C_without_elo | log_loss | 0.623370 | 0.005369 | 0.000615 | 0.010252 | 543 |
| D2_overall | accuracy | 0.664825 | 0.000000 | -0.016249 | 0.014844 | 543 |
| D2_overall | brier | 0.215420 | 0.000467 | -0.002301 | 0.003045 | 543 |
| D2_overall | log_loss | 0.619357 | 0.001356 | -0.004968 | 0.007326 | 543 |
| D_matchups | accuracy | 0.653775 | -0.011050 | -0.033149 | 0.011009 | 543 |
| D_matchups | brier | 0.216920 | 0.001966 | -0.000593 | 0.004377 | 543 |
| D_matchups | log_loss | 0.623540 | 0.005539 | -0.000178 | 0.010936 | 543 |
| logistic | accuracy | 0.644567 | -0.020258 | -0.042514 | 0.001859 | 543 |
| logistic | brier | 0.220954 | 0.006000 | 0.000335 | 0.011661 | 543 |
| logistic | log_loss | 0.631279 | 0.013279 | 0.000038 | 0.025961 | 543 |

Intervals are exploratory paired season-week bootstrap percentiles, unadjusted for multiple comparisons. Repeated teams and interweek dependence remain limitations. The repeatedly inspected 2024–2025 years are not a new independent test.

## Personnel eligibility

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

QB/OL experiments use only matched qualifying games. Missing observations/references/coverage cannot be healthy or zero-absence assumptions. A skipped experiment is an honest coverage result, not zero effect. G uses fixed B+personnel only if both independent E/F comparisons qualify; no later-period efficiency winner is selected to construct G.

## Noncausal permutation diagnostics

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

Raw and adjusted measures and Elo are correlated. Marginal/group permutations can hide redundant signals or create unrealistic combinations. They diagnose model use, not football causation. See complete repeats and ablations before interpreting a single estimate.
