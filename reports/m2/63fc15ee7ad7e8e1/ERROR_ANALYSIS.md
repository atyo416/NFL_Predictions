# Historical error analysis

| season | games | accuracy | mean_home_probability | observed_home_wins |
| --- | --- | --- | --- | --- |
| 2022 | 269 | 0.639405 | 0.536654 | 0.561338 |
| 2023 | 272 | 0.628676 | 0.534274 | 0.555147 |
| 2024 | 272 | 0.683824 | 0.539497 | 0.533088 |
| 2025 | 271 | 0.605166 | 0.533607 | 0.538745 |

2024 minus 2025 accuracy, with independent week resampling: {"accuracy_2024": 0.6838235294117647, "accuracy_2025": 0.6051660516605166, "difference_2024_minus_2025": 0.0786574777512481, "low": 0.006147880214335709, "high": 0.15075649704964988, "method": "Independent within-season week-block percentile bootstrap; descriptive 95% interval, two seasons only"}.

The observed seasonal difference alone does not identify a cause. Sampling variation, changing schedule composition, strength volatility and calibration can all contribute. Only two recent seasons are available. Intervals are descriptive and do not establish a football mechanism. Inspect season calibration and error_slices.csv before advancing a hypothesis.

Slices cover season, week, actual home/away winner, model favorite/underdog outcome, probability, division matchup (documented current franchise mapping), recent offensive EPA difference and weeks 1–4 versus 5+. These overlapping post-hoc groups do not constitute independent significance tests.

Download incorrect_predictions.csv from Model Analysis. It includes original pregame features, predicted probability and standardized feature × coefficient contributions to home-win log odds, plus the intercept. Contributions explain the linear score, not causal responsibility for an error.
