# M4 exploratory model comparison

Selected configuration using development Brier through 2021: **shallow**. Previously inspected 2024–2025 never selects hyperparameters. All comparison deltas below are candidate minus M2 logistic; positive accuracy and negative Brier/log-loss favor the candidate. Intervals are paired week-block percentiles, unadjusted for exploratory multiplicity. No model is automatically promoted.

## Development selection

| configuration | validation_brier | validation_log_loss | validation_accuracy |
| --- | --- | --- | --- |
| shallow | 0.229965 | 0.652613 | 0.615947 |
| conservative | 0.233505 | 0.661823 | 0.618252 |
| larger | 0.238834 | 0.675358 | 0.611716 |
| faster | 0.241455 | 0.684646 | 0.612257 |

## Aligned forward comparison

| model | metric | estimate | low | high | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| elo_margin | accuracy | 0.651934 | 0.614522 | 0.688318 | 0.007366 | -0.025936 | 0.039108 | 543 |
| elo_margin | brier | 0.219134 | 0.204053 | 0.235738 | -0.001819 | -0.009637 | 0.006045 | 543 |
| elo_margin | log_loss | 0.627875 | 0.594085 | 0.665523 | -0.003404 | -0.020536 | 0.014756 | 543 |
| elo_only | accuracy | 0.639042 | 0.592633 | 0.681904 | -0.005525 | -0.044447 | 0.032613 | 543 |
| elo_only | brier | 0.224492 | 0.213135 | 0.236575 | 0.003538 | -0.004322 | 0.011979 | 543 |
| elo_only | log_loss | 0.639773 | 0.615410 | 0.665452 | 0.008493 | -0.008243 | 0.026349 | 543 |
| hgb_config_conservative | accuracy | 0.650092 | 0.607266 | 0.693772 | 0.005525 | -0.020295 | 0.030965 | 543 |
| hgb_config_conservative | brier | 0.220177 | 0.204281 | 0.236446 | -0.000776 | -0.007345 | 0.006239 | 543 |
| hgb_config_conservative | log_loss | 0.630451 | 0.595770 | 0.666891 | -0.000828 | -0.015081 | 0.015061 | 543 |
| hgb_config_faster | accuracy | 0.626151 | 0.578172 | 0.672253 | -0.018416 | -0.052349 | 0.012895 | 543 |
| hgb_config_faster | brier | 0.226551 | 0.210345 | 0.243366 | 0.005597 | -0.001931 | 0.013327 | 543 |
| hgb_config_faster | log_loss | 0.645176 | 0.607594 | 0.684394 | 0.013896 | -0.003071 | 0.032096 | 543 |
| hgb_config_larger | accuracy | 0.657459 | 0.611418 | 0.701308 | 0.012891 | -0.016855 | 0.043798 | 543 |
| hgb_config_larger | brier | 0.222335 | 0.205737 | 0.239435 | 0.001381 | -0.006417 | 0.009379 | 543 |
| hgb_config_larger | log_loss | 0.636630 | 0.599227 | 0.676435 | 0.005351 | -0.012572 | 0.024197 | 543 |
| hgb_config_shallow | accuracy | 0.661142 | 0.617054 | 0.706971 | 0.016575 | -0.003677 | 0.036902 | 543 |
| hgb_config_shallow | brier | 0.217426 | 0.201857 | 0.233059 | -0.003528 | -0.009152 | 0.002531 | 543 |
| hgb_config_shallow | log_loss | 0.624715 | 0.591094 | 0.659367 | -0.006564 | -0.019219 | 0.007074 | 543 |
| hgb_interactions | accuracy | 0.650092 | 0.605605 | 0.693164 | 0.005525 | -0.012844 | 0.023723 | 543 |
| hgb_interactions | brier | 0.218354 | 0.204008 | 0.233929 | -0.002600 | -0.007936 | 0.002960 | 543 |
| hgb_interactions | log_loss | 0.626884 | 0.596133 | 0.660902 | -0.004395 | -0.016106 | 0.007592 | 543 |
| hgb_isotonic | accuracy | 0.661142 | 0.617054 | 0.706971 | 0.016575 | -0.003677 | 0.036902 | 543 |
| hgb_isotonic | brier | 0.221302 | 0.206822 | 0.236314 | 0.000348 | -0.005527 | 0.006823 | 543 |
| hgb_isotonic | log_loss | 0.656650 | 0.608728 | 0.719358 | 0.025371 | -0.008619 | 0.075964 | 543 |
| hgb_m2_only | accuracy | 0.659300 | 0.614542 | 0.704509 | 0.014733 | -0.009193 | 0.038397 | 543 |
| hgb_m2_only | brier | 0.219418 | 0.205149 | 0.234009 | -0.001536 | -0.006603 | 0.004057 | 543 |
| hgb_m2_only | log_loss | 0.628963 | 0.598200 | 0.660884 | -0.002316 | -0.013868 | 0.010288 | 543 |
| hgb_margin_elo | accuracy | 0.664825 | 0.625692 | 0.702807 | 0.020258 | 0.000000 | 0.042049 | 543 |
| hgb_margin_elo | brier | 0.218380 | 0.202648 | 0.235243 | -0.002574 | -0.009218 | 0.004242 | 543 |
| hgb_margin_elo | log_loss | 0.626795 | 0.592141 | 0.663986 | -0.004485 | -0.019250 | 0.010724 | 543 |
| hgb_relative_strength | accuracy | 0.664825 | 0.622711 | 0.707962 | 0.020258 | -0.001845 | 0.042672 | 543 |
| hgb_relative_strength | brier | 0.217715 | 0.202386 | 0.233262 | -0.003239 | -0.008793 | 0.002631 | 543 |
| hgb_relative_strength | log_loss | 0.625594 | 0.592565 | 0.659837 | -0.005685 | -0.017897 | 0.007103 | 543 |
| hgb_rest | accuracy | 0.662983 | 0.617213 | 0.709680 | 0.018416 | -0.001855 | 0.040665 | 543 |
| hgb_rest | brier | 0.217501 | 0.202075 | 0.233164 | -0.003453 | -0.009239 | 0.002748 | 543 |
| hgb_rest | log_loss | 0.624989 | 0.591411 | 0.659583 | -0.006291 | -0.019165 | 0.007615 | 543 |
| hgb_selected | accuracy | 0.661142 | 0.617054 | 0.706971 | 0.016575 | -0.003677 | 0.036902 | 543 |
| hgb_selected | brier | 0.217426 | 0.201857 | 0.233059 | -0.003528 | -0.009152 | 0.002531 | 543 |
| hgb_selected | log_loss | 0.624715 | 0.591094 | 0.659367 | -0.006564 | -0.019219 | 0.007074 | 543 |
| hgb_sigmoid | accuracy | 0.646409 | 0.602221 | 0.686822 | 0.001842 | -0.023944 | 0.025643 | 543 |
| hgb_sigmoid | brier | 0.219496 | 0.206609 | 0.233063 | -0.001457 | -0.006334 | 0.003783 | 543 |
| hgb_sigmoid | log_loss | 0.629086 | 0.601698 | 0.657982 | -0.002193 | -0.012894 | 0.009193 | 543 |
| historical_home_rate | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| historical_home_rate | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| historical_home_rate | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| logistic | accuracy | 0.644567 | 0.605503 | 0.681410 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | brier | 0.220954 | 0.207585 | 0.234306 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | log_loss | 0.631279 | 0.602509 | 0.659981 | 0.000000 | 0.000000 | 0.000000 | 543 |
| m2_elo | accuracy | 0.642726 | 0.605165 | 0.680002 | -0.001842 | -0.018834 | 0.016636 | 543 |
| m2_elo | brier | 0.220227 | 0.205173 | 0.236194 | -0.000727 | -0.004449 | 0.003046 | 543 |
| m2_elo | log_loss | 0.630039 | 0.596933 | 0.665224 | -0.001241 | -0.010101 | 0.007823 | 543 |
| pregame_win_percentage | accuracy | 0.657459 | 0.611600 | 0.702012 | 0.012891 | -0.022141 | 0.053712 | 543 |
| pregame_win_percentage | brier | 0.222769 | 0.213975 | 0.231584 | 0.001815 | -0.007872 | 0.010635 | 543 |
| pregame_win_percentage | log_loss | 0.637090 | 0.618631 | 0.655367 | 0.005810 | -0.014712 | 0.025073 | 543 |

## Overfitting

| model | evaluation | calibration_diagnostic | forward_evaluation | training | evaluation_minus_train_brier |
| --- | --- | --- | --- | --- | --- |
| hgb_config_conservative | 2022 | 0.239733 | 0.244808 | 0.170486 | 0.074322 |
| hgb_config_conservative | 2023 | 0.234485 | 0.237818 | 0.177792 | 0.060026 |
| hgb_config_conservative | 2024 | 0.233574 | 0.208044 | 0.185299 | 0.022745 |
| hgb_config_conservative | 2025 | 0.233574 | 0.232355 | 0.185299 | 0.047056 |
| hgb_config_faster | 2022 | 0.249797 | 0.252950 | 0.143060 | 0.109890 |
| hgb_config_faster | 2023 | 0.235822 | 0.240318 | 0.153756 | 0.086563 |
| hgb_config_faster | 2024 | 0.238040 | 0.214746 | 0.164772 | 0.049974 |
| hgb_config_faster | 2025 | 0.238040 | 0.238400 | 0.164772 | 0.073628 |
| hgb_config_larger | 2022 | 0.244307 | 0.248358 | 0.148674 | 0.099684 |
| hgb_config_larger | 2023 | 0.235597 | 0.240736 | 0.158302 | 0.082434 |
| hgb_config_larger | 2024 | 0.236997 | 0.211136 | 0.165395 | 0.045740 |
| hgb_config_larger | 2025 | 0.236997 | 0.233575 | 0.165395 | 0.068180 |
| hgb_config_shallow | 2022 | 0.237233 | 0.240781 | 0.188913 | 0.051868 |
| hgb_config_shallow | 2023 | 0.232228 | 0.232505 | 0.196445 | 0.036060 |
| hgb_config_shallow | 2024 | 0.230910 | 0.206462 | 0.201870 | 0.004592 |
| hgb_config_shallow | 2025 | 0.230910 | 0.228431 | 0.201870 | 0.026560 |
| hgb_interactions | 2022 | 0.237094 | 0.242176 | 0.185039 | 0.057137 |
| hgb_interactions | 2023 | 0.231746 | 0.231440 | 0.194445 | 0.036994 |
| hgb_interactions | 2024 | 0.229072 | 0.208138 | 0.199917 | 0.008221 |
| hgb_interactions | 2025 | 0.229072 | 0.228607 | 0.199917 | 0.028690 |
| hgb_m2_only | 2022 | 0.233277 | 0.236588 | 0.189639 | 0.046949 |
| hgb_m2_only | 2023 | 0.231076 | 0.230795 | 0.196751 | 0.034043 |
| hgb_m2_only | 2024 | 0.230882 | 0.208973 | 0.202464 | 0.006509 |
| hgb_m2_only | 2025 | 0.230882 | 0.229901 | 0.202464 | 0.027437 |
| hgb_margin_elo | 2022 | 0.231871 | 0.237143 | 0.187080 | 0.050063 |
| hgb_margin_elo | 2023 | 0.228150 | 0.232765 | 0.194652 | 0.038113 |
| hgb_margin_elo | 2024 | 0.229405 | 0.207166 | 0.201691 | 0.005475 |
| hgb_margin_elo | 2025 | 0.229405 | 0.229635 | 0.201691 | 0.027944 |
| hgb_relative_strength | 2022 | 0.237004 | 0.240370 | 0.188063 | 0.052307 |
| hgb_relative_strength | 2023 | 0.231350 | 0.233279 | 0.195646 | 0.037633 |
| hgb_relative_strength | 2024 | 0.230232 | 0.207747 | 0.201930 | 0.005817 |
| hgb_relative_strength | 2025 | 0.230232 | 0.227719 | 0.201930 | 0.025788 |
| hgb_rest | 2022 | 0.237639 | 0.240259 | 0.188980 | 0.051278 |
| hgb_rest | 2023 | 0.232479 | 0.233169 | 0.196045 | 0.037124 |
| hgb_rest | 2024 | 0.230528 | 0.206775 | 0.201515 | 0.005260 |
| hgb_rest | 2025 | 0.230528 | 0.228266 | 0.201515 | 0.026751 |
| hgb_selected | 2022 | 0.237233 | 0.240781 | 0.188913 | 0.051868 |
| hgb_selected | 2023 | 0.232228 | 0.232505 | 0.196445 | 0.036060 |
| hgb_selected | 2024 | 0.230910 | 0.206462 | 0.201870 | 0.004592 |
| hgb_selected | 2025 | 0.230910 | 0.228431 | 0.201870 | 0.026560 |

Training/forward gaps describe sample fit versus later performance, not a generalization guarantee. learning-rate and depth/leaf sensitivity are predefined configurations; they are not tuned on the reported later years. Individual years and early/late-season results are in comparison.csv and season_phase.csv.

## Exploratory permutation importance

| model | group | mean_brier_increase | mean_log_loss_increase |
| --- | --- | --- | --- |
| hgb_selected | group:offense | 0.007632 | 0.016440 |
| hgb_selected | feature:off_success | 0.006944 | 0.014672 |
| hgb_selected | feature:elo_difference | 0.005588 | 0.010877 |
| hgb_interactions | group:elo | 0.005580 | 0.010969 |
| hgb_interactions | feature:off_success | 0.005150 | 0.010967 |
| hgb_selected | group:elo | 0.005084 | 0.009723 |
| hgb_interactions | feature:elo_difference | 0.005007 | 0.009745 |
| hgb_interactions | group:offense | 0.004316 | 0.009190 |
| hgb_selected | group:scoring_turnovers | 0.003825 | 0.007686 |
| hgb_interactions | feature:away_success_defense | 0.002317 | 0.004347 |
| hgb_interactions | group:scoring_turnovers | 0.002188 | 0.004231 |
| hgb_interactions | group:interactions | 0.002089 | 0.003981 |
| hgb_selected | feature:recent_off_epa | 0.001640 | 0.003577 |
| hgb_selected | feature:scoring | 0.001520 | 0.002812 |
| hgb_selected | group:recent | 0.001390 | 0.003386 |
| hgb_interactions | feature:scoring | 0.001329 | 0.002356 |
| hgb_interactions | feature:recent_off_epa | 0.001232 | 0.002458 |
| hgb_interactions | group:recent | 0.000939 | 0.002044 |
| hgb_selected | group:defense | 0.000617 | 0.001244 |
| hgb_interactions | feature:home_success_defense | 0.000566 | 0.001143 |
| hgb_selected | feature:def_yards | 0.000423 | 0.000852 |
| hgb_interactions | feature:turnover | 0.000404 | 0.000634 |
| hgb_selected | feature:turnover | 0.000402 | 0.000434 |
| hgb_selected | feature:win | 0.000373 | 0.000649 |
| hgb_interactions | group:defense | 0.000272 | 0.000644 |
| hgb_selected | feature:recent_def_epa | 0.000201 | 0.000696 |
| hgb_interactions | feature:def_success | 0.000076 | 0.000149 |
| hgb_interactions | feature:recent_def_epa | 0.000065 | 0.000263 |
| hgb_selected | feature:def_epa | 0.000024 | -0.000079 |
| hgb_selected | feature:neutral | 0.000000 | 0.000000 |

Importance is the loss increase after jointly permuting a feature/group in chronological evaluation games. Related football statistics are correlated: marginal permutations can create unrealistic combinations or hide redundant information. These are noncausal diagnostics, not evidence for post-hoc feature selection on 2024–2025.

## Calibration and limitations

Uncalibrated, sigmoid and sufficiently supported isotonic forecasts have separate chronological base/calibration/evaluation periods. Development validation and the first calibration year both include 2021; this can overfit calibration choices, but evaluation starts strictly later. No calibration method becomes a default. Reliability diagrams, identifiable intercept/slope and confidence buckets are included. Native Windows testing, historical publication/vintage reconstruction and prospective independent confirmation remain outstanding. QB context is excluded because verified historical coverage is insufficient. Optional XGBoost status: Deferred optional comparison: not installed; no native Windows verification. M4 uses sklearn without adding a second native dependency.
