# Chronological calibration

Each base estimator is fitted before the calibration year. Sigmoid fits a logistic map of logit probabilities on that year only. Isotonic requires at least the configured calibration game count and ten distinct probabilities. Neither method sees evaluation-period outcomes during fitting.

| period | model | intercept | slope |
| --- | --- | --- | --- |
| examined_2024_2025 | always_home | -0.012868 | nan |
| examined_2024_2025 | historical_home_rate | -0.012868 | nan |
| examined_2024_2025 | isotonic | -0.074153 | 1.071222 |
| examined_2024_2025 | logistic | -0.013924 | 1.086007 |
| examined_2024_2025 | pregame_win_percentage | 0.170654 | 1.729999 |
| examined_2024_2025 | sigmoid | -0.137909 | 1.328909 |

Diagnostic intercept/slope are fitted on evaluation outcomes solely for assessment (ideal 0/1); they are not deployed. They can be unstable in small or separated samples. Buckets and reliability.png use out-of-period predictions. Compare Brier and log-loss intervals in MODEL_COMPARISON.md before considering calibration. No automatic promotion is supported.
