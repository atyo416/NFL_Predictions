# M3 exploratory comparisons

| model | metric | estimate | low | high | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_home | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| always_home | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| always_home | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| elo_margin | accuracy | 0.651934 | 0.614522 | 0.688318 | 0.007366 | -0.025936 | 0.039108 | 543 |
| elo_margin | brier | 0.219134 | 0.204053 | 0.235738 | -0.001819 | -0.009637 | 0.006045 | 543 |
| elo_margin | log_loss | 0.627875 | 0.594085 | 0.665523 | -0.003404 | -0.020536 | 0.014756 | 543 |
| elo_only | accuracy | 0.639042 | 0.592633 | 0.681904 | -0.005525 | -0.044447 | 0.032613 | 543 |
| elo_only | brier | 0.224492 | 0.213135 | 0.236575 | 0.003538 | -0.004322 | 0.011979 | 543 |
| elo_only | log_loss | 0.639773 | 0.615410 | 0.665452 | 0.008493 | -0.008243 | 0.026349 | 543 |
| historical_home_rate | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| historical_home_rate | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| historical_home_rate | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| logistic | accuracy | 0.644567 | 0.605503 | 0.681410 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | brier | 0.220954 | 0.207585 | 0.234306 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | log_loss | 0.631279 | 0.602509 | 0.659981 | 0.000000 | 0.000000 | 0.000000 | 543 |
| m2_bye | accuracy | 0.637201 | 0.600733 | 0.671682 | -0.007366 | -0.018183 | 0.001862 | 543 |
| m2_bye | brier | 0.220973 | 0.207855 | 0.234421 | 0.000020 | -0.000614 | 0.000655 | 543 |
| m2_bye | log_loss | 0.631232 | 0.602777 | 0.659845 | -0.000047 | -0.001458 | 0.001335 | 543 |
| m2_elo | accuracy | 0.642726 | 0.605165 | 0.680002 | -0.001842 | -0.018834 | 0.016636 | 543 |
| m2_elo | brier | 0.220227 | 0.205173 | 0.236194 | -0.000727 | -0.004449 | 0.003046 | 543 |
| m2_elo | log_loss | 0.630039 | 0.596933 | 0.665224 | -0.001241 | -0.010101 | 0.007823 | 543 |
| m2_elo_rest | accuracy | 0.639042 | 0.601476 | 0.676473 | -0.005525 | -0.024489 | 0.014870 | 543 |
| m2_elo_rest | brier | 0.220119 | 0.204945 | 0.236022 | -0.000834 | -0.004523 | 0.003026 | 543 |
| m2_elo_rest | log_loss | 0.629768 | 0.596262 | 0.665223 | -0.001511 | -0.010425 | 0.007811 | 543 |
| m2_extended_rest | accuracy | 0.640884 | 0.601851 | 0.678506 | -0.003683 | -0.011070 | 0.001890 | 543 |
| m2_extended_rest | brier | 0.220721 | 0.207487 | 0.234162 | -0.000233 | -0.000814 | 0.000305 | 543 |
| m2_extended_rest | log_loss | 0.630724 | 0.602295 | 0.659524 | -0.000556 | -0.001800 | 0.000596 | 543 |
| m2_rest | accuracy | 0.639042 | 0.599622 | 0.676637 | -0.005525 | -0.016514 | 0.005474 | 543 |
| m2_rest | brier | 0.220845 | 0.207745 | 0.234307 | -0.000108 | -0.000833 | 0.000574 | 543 |
| m2_rest | log_loss | 0.630937 | 0.602813 | 0.659546 | -0.000342 | -0.001901 | 0.001098 | 543 |
| m2_rest_days | accuracy | 0.642726 | 0.604008 | 0.680073 | -0.001842 | -0.005618 | 0.000000 | 543 |
| m2_rest_days | brier | 0.220973 | 0.207602 | 0.234324 | 0.000019 | -0.000008 | 0.000050 | 543 |
| m2_rest_days | log_loss | 0.631315 | 0.602541 | 0.660040 | 0.000035 | -0.000024 | 0.000102 | 543 |
| m2_rest_redundancy_check | accuracy | 0.639042 | 0.599622 | 0.676637 | -0.005525 | -0.016514 | 0.005474 | 543 |
| m2_rest_redundancy_check | brier | 0.220827 | 0.207725 | 0.234290 | -0.000127 | -0.000860 | 0.000578 | 543 |
| m2_rest_redundancy_check | log_loss | 0.630898 | 0.602783 | 0.659503 | -0.000382 | -0.001971 | 0.001103 | 543 |
| m2_short_rest | accuracy | 0.642726 | 0.604008 | 0.680073 | -0.001842 | -0.005618 | 0.000000 | 543 |
| m2_short_rest | brier | 0.220977 | 0.207664 | 0.234291 | 0.000023 | -0.000125 | 0.000167 | 543 |
| m2_short_rest | log_loss | 0.631296 | 0.602650 | 0.659820 | 0.000016 | -0.000310 | 0.000332 | 543 |
| pregame_win_percentage | accuracy | 0.657459 | 0.611600 | 0.702012 | 0.012891 | -0.022141 | 0.053712 | 543 |
| pregame_win_percentage | brier | 0.222769 | 0.213975 | 0.231584 | 0.001815 | -0.007872 | 0.010635 | 543 |
| pregame_win_percentage | log_loss | 0.637090 | 0.618631 | 0.655367 | 0.005810 | -0.014712 | 0.025073 | 543 |

Deltas are candidate minus the original M2 logistic benchmark. Positive accuracy and negative Brier/log-loss favor candidates. Identical evaluation games are required. No automatic promotion; 2024–2025 was previously examined. See calibration, individual season results, missingness, warmup sensitivity and Elo-versus-win-percentage tables before interpreting apparent improvements.

QB: [{"evaluation": 2022, "status": "Skipped: no sufficient matched, verified pregame QB coverage", "training": 0, "evaluation_games": 0}, {"evaluation": 2023, "status": "Skipped: no sufficient matched, verified pregame QB coverage", "training": 0, "evaluation_games": 0}, {"evaluation": 2024, "status": "Skipped: no sufficient matched, verified pregame QB coverage", "training": 0, "evaluation_games": 0}, {"evaluation": 2025, "status": "Skipped: no sufficient matched, verified pregame QB coverage", "training": 0, "evaluation_games": 0}]
