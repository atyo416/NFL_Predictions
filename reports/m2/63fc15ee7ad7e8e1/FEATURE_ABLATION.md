# Feature ablation

| group | mean_brier_contribution | positive_seasons | seasons | mean_accuracy_contribution | mean_log_loss_contribution |
| --- | --- | --- | --- | --- | --- |
| offensive_efficiency | 0.000862 | 3 | 4 | 0.001845 | 0.001485 |
| defensive_efficiency | 0.000192 | 2 | 4 | -0.002798 | 0.000302 |
| win_percentage | 0.000173 | 2 | 4 | -0.004657 | 0.000425 |
| turnovers | 0.000163 | 3 | 4 | 0.001842 | 0.000251 |
| scoring | 0.000060 | 3 | 4 | -0.002791 | 0.000152 |
| recent_performance | -0.000258 | 1 | 4 | 0.000919 | -0.000654 |
| rest_venue | -0.000510 | 2 | 4 | -0.003687 | -0.000864 |

Positive Brier contribution means that removing the group worsened Brier score. These are exploratory equal-season means over the configured forward folds. Full and reduced models use identical games and training-only preprocessing. See ablations.csv for each fold and ablation_uncertainty.csv for paired cluster intervals (reduced minus full).

The standardized coefficients are descriptive conditional associations, not causal effects. EPA, success, yards, scoring and win percentage are correlated; removal effects depend on which related features remain. training_feature_correlations.csv records training-period pairwise correlations. No features were deleted and the champion is unchanged.
