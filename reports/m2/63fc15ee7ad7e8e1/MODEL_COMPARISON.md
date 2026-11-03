# Exploratory model comparison

examined_2024_2025

| model | metric | estimate | low | high | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_home | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| always_home | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| always_home | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| historical_home_rate | accuracy | 0.535912 | 0.487035 | 0.581822 | -0.108656 | -0.159633 | -0.061483 | 543 |
| historical_home_rate | brier | 0.248721 | 0.245129 | 0.252544 | 0.027767 | 0.014659 | 0.040714 | 543 |
| historical_home_rate | log_loss | 0.690586 | 0.683389 | 0.698248 | 0.059307 | 0.031388 | 0.086765 | 543 |
| isotonic | accuracy | 0.655617 | 0.617807 | 0.693582 | 0.011050 | -0.001869 | 0.027627 | 543 |
| isotonic | brier | 0.218940 | 0.205337 | 0.232599 | -0.002013 | -0.004789 | 0.001012 | 543 |
| isotonic | log_loss | 0.624336 | 0.594947 | 0.653455 | -0.006943 | -0.013758 | 0.000435 | 543 |
| logistic | accuracy | 0.644567 | 0.605503 | 0.681410 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | brier | 0.220954 | 0.207585 | 0.234306 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | log_loss | 0.631279 | 0.602509 | 0.659981 | 0.000000 | 0.000000 | 0.000000 | 543 |
| pregame_win_percentage | accuracy | 0.657459 | 0.611600 | 0.702012 | 0.012891 | -0.022141 | 0.053712 | 543 |
| pregame_win_percentage | brier | 0.222769 | 0.213975 | 0.231584 | 0.001815 | -0.007872 | 0.010635 | 543 |
| pregame_win_percentage | log_loss | 0.637090 | 0.618631 | 0.655367 | 0.005810 | -0.014712 | 0.025073 | 543 |
| sigmoid | accuracy | 0.629834 | 0.593282 | 0.665448 | -0.014733 | -0.029631 | 0.000000 | 543 |
| sigmoid | brier | 0.222519 | 0.210746 | 0.234591 | 0.001565 | -0.000852 | 0.004177 | 543 |
| sigmoid | log_loss | 0.634794 | 0.609787 | 0.659914 | 0.003515 | -0.001980 | 0.009296 | 543 |

Differences are model minus uncalibrated logistic. Positive accuracy and negative Brier/log-loss favor the candidate. Intervals use identical resampled season-week clusters for each model. They are unadjusted for multiplicity, rely on independence across weeks, and do not capture all repeated-team dependence. No superiority claim or champion promotion is made. The 2024–2025 results were already inspected in M1 and are not an untouched confirmation set.
