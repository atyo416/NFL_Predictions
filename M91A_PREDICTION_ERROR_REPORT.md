# M9.1A historical prediction errors and shared failures

Frozen historical OOS probabilities only; no training, inference, data downloads, personnel collection, new model features or policy changes. 2024–2025 are historically explored evaluation years, not independent prospective confirmation.

## Coverage and exclusions

| measure | value |
| --- | --- |
| source_classification | historical_closing_reference |
| schedule_games | 1871 |
| base_prediction_games | 1865 |
| unmatched_prediction_ids | 0 |
| incomplete_scores | 0 |
| ties_excluded | 6 |
| missing_closing_pair | 0 |
| invalid_closing_pair | 0 |
| usable_closing_pairs | 1865 |
| underround_pairs | 1 |
| missing_or_invalid_model_probabilities | 0 |
| metadata_conflicts | 0 |
| closing_games_without_base_predictions | 0 |
| base_matched_games | 1865 |
| ensemble_metadata_conflicts | 0 |
| ensemble_matched_games | 543 |
| base_games_without_eligible_ensemble | 1322 |
| missing_or_ambiguous_feature_seasons | [] |
| missing_feature_game_rows | 0 |

M8.1 exact-ID/team/kickoff/outcome matching and American-moneyline proportional no-vig conversion are reused. Ties, unfinished games, unavailable/malformed paired odds, invalid probabilities and conflicting metadata are excluded. All models use identical games within each sample; the base and frozen-ensemble samples remain separate. Features come only from checksum-verified cached pregame rows with identical cutoffs; unavailable/ambiguous caches remain missing, never reconstructed.

## all_base_history

| model | games | accuracy | error_rate | expected_error_rate | brier | market_brier | log_loss | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 1865 | 0.633244 | 0.366756 | 0.353187 | 0.224061 | 0.210547 | 0.639396 | 0.013569 | -0.007685 | 0.033563 | 0.013514 |
| logistic_oos | 1865 | 0.616622 | 0.383378 | 0.374928 | 0.229082 | 0.210547 | 0.649626 | 0.008450 | -0.012466 | 0.027819 | 0.018534 |
| margin_elo | 1865 | 0.635925 | 0.364075 | 0.350981 | 0.223899 | 0.210547 | 0.639544 | 0.013094 | -0.005783 | 0.031806 | 0.013352 |

### confidence

| model | confidence_bucket | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 50–55% | 409 | 0.488998 | 0.473398 | 0.250200 | 0.015599 | -0.035765 | 0.061444 | 0.016598 |
| boosting_oos | 55–60% | 350 | 0.414286 | 0.427483 | 0.242559 | -0.013197 | -0.062375 | 0.037626 | 0.016308 |
| boosting_oos | 60–70% | 513 | 0.366472 | 0.352520 | 0.230652 | 0.013951 | -0.021401 | 0.049403 | 0.016427 |
| boosting_oos | 70–80% | 419 | 0.284010 | 0.255638 | 0.205384 | 0.028372 | -0.020845 | 0.079708 | 0.003028 |
| boosting_oos | 80–90% | 166 | 0.186747 | 0.161199 | 0.152962 | 0.025548 | -0.031951 | 0.084497 | 0.018178 |
| boosting_oos | 90–100% | 8 | 0.125000 | 0.092673 | 0.109251 | 0.032327 | -0.094872 | 0.334219 | -0.000927 |
| logistic_oos | 50–55% | 467 | 0.498929 | 0.474536 | 0.250127 | 0.024394 | -0.020154 | 0.069396 | 0.028199 |
| logistic_oos | 55–60% | 407 | 0.390663 | 0.423881 | 0.239702 | -0.033218 | -0.080230 | 0.015343 | 0.011124 |
| logistic_oos | 60–70% | 587 | 0.369676 | 0.355583 | 0.230221 | 0.014094 | -0.020198 | 0.045821 | 0.018345 |
| logistic_oos | 70–80% | 325 | 0.286154 | 0.255570 | 0.206162 | 0.030584 | -0.026076 | 0.084083 | 0.021389 |
| logistic_oos | 80–90% | 78 | 0.166667 | 0.169608 | 0.137406 | -0.002941 | -0.078971 | 0.077677 | -0.010949 |
| logistic_oos | 90–100% | 1 | 0.000000 | 0.096542 | 0.009320 | -0.096542 | nan | nan | 0.003817 |
| margin_elo | 50–55% | 355 | 0.521127 | 0.473439 | 0.252386 | 0.047687 | -0.004599 | 0.100559 | 0.015062 |
| margin_elo | 55–60% | 358 | 0.388268 | 0.425847 | 0.239339 | -0.037579 | -0.081683 | 0.005802 | 0.015641 |
| margin_elo | 60–70% | 579 | 0.359240 | 0.354167 | 0.229161 | 0.005073 | -0.032162 | 0.041676 | 0.014493 |
| margin_elo | 70–80% | 405 | 0.274074 | 0.254748 | 0.199360 | 0.019326 | -0.022263 | 0.060875 | 0.004690 |
| margin_elo | 80–90% | 155 | 0.225806 | 0.159209 | 0.180277 | 0.066598 | 0.006839 | 0.126550 | 0.025137 |
| margin_elo | 90–100% | 13 | 0.076923 | 0.087911 | 0.071006 | -0.010988 | -0.090696 | 0.125683 | -0.017915 |

### week_phase

| model | week_phase | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 13+ | 620 | 0.361290 | 0.341788 | 0.219005 | 0.019503 | -0.011192 | 0.051319 | 0.018583 |
| boosting_oos | 1–4 | 442 | 0.389140 | 0.373614 | 0.234393 | 0.015527 | -0.031910 | 0.058217 | 0.015389 |
| boosting_oos | 5–12 | 803 | 0.358655 | 0.350746 | 0.222277 | 0.007910 | -0.025624 | 0.043313 | 0.008568 |
| logistic_oos | 13+ | 620 | 0.359677 | 0.365669 | 0.222812 | -0.005992 | -0.048985 | 0.038006 | 0.022389 |
| logistic_oos | 1–4 | 442 | 0.395928 | 0.392340 | 0.238439 | 0.003588 | -0.029442 | 0.038768 | 0.019434 |
| logistic_oos | 5–12 | 803 | 0.394770 | 0.372493 | 0.228772 | 0.022277 | -0.006380 | 0.050559 | 0.015063 |
| margin_elo | 13+ | 620 | 0.351613 | 0.331889 | 0.220488 | 0.019724 | -0.014658 | 0.056984 | 0.020065 |
| margin_elo | 1–4 | 442 | 0.386878 | 0.370746 | 0.230709 | 0.016132 | -0.019602 | 0.052219 | 0.011704 |
| margin_elo | 5–12 | 803 | 0.361146 | 0.354843 | 0.222784 | 0.006302 | -0.022901 | 0.036695 | 0.009075 |

### market_agreement

| model | favorite_agreement | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | market_pickem | 7 | 0.714286 | 0.460274 | 0.287689 | 0.254012 | -0.054053 | 0.559129 | 0.037689 |
| boosting_oos | opposite_favorite | 297 | 0.595960 | 0.438453 | 0.265944 | 0.157507 | 0.102174 | 0.209057 | 0.033253 |
| boosting_oos | same_favorite | 1561 | 0.321589 | 0.336484 | 0.215807 | -0.014895 | -0.037691 | 0.006450 | 0.009650 |
| logistic_oos | market_pickem | 7 | 0.571429 | 0.451648 | 0.248583 | 0.119781 | -0.291971 | 0.410894 | -0.001417 |
| logistic_oos | opposite_favorite | 371 | 0.619946 | 0.429846 | 0.273293 | 0.190101 | 0.143484 | 0.240437 | 0.048855 |
| logistic_oos | same_favorite | 1487 | 0.323470 | 0.360865 | 0.217959 | -0.037395 | -0.061247 | -0.014867 | 0.011063 |
| margin_elo | market_pickem | 7 | 0.714286 | 0.431074 | 0.293090 | 0.283212 | -0.037931 | 0.584912 | 0.043090 |
| margin_elo | opposite_favorite | 300 | 0.586667 | 0.431290 | 0.266399 | 0.155376 | 0.099203 | 0.208248 | 0.030241 |
| margin_elo | same_favorite | 1558 | 0.319641 | 0.335157 | 0.215404 | -0.015517 | -0.037011 | 0.005096 | 0.009966 |

### divisional

| model | divisional | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | False | 1195 | 0.361506 | 0.358987 | 0.223318 | 0.002519 | -0.024518 | 0.029442 | 0.011292 |
| boosting_oos | True | 670 | 0.376119 | 0.342842 | 0.225386 | 0.033277 | -0.000138 | 0.063891 | 0.017476 |
| logistic_oos | False | 1195 | 0.377406 | 0.380309 | 0.228671 | -0.002903 | -0.029082 | 0.025282 | 0.016645 |
| logistic_oos | True | 670 | 0.394030 | 0.365331 | 0.229814 | 0.028698 | -0.008848 | 0.063682 | 0.021904 |
| margin_elo | False | 1195 | 0.362343 | 0.358788 | 0.222955 | 0.003555 | -0.021730 | 0.029005 | 0.010929 |
| margin_elo | True | 670 | 0.367164 | 0.337057 | 0.225582 | 0.030107 | -0.002643 | 0.061289 | 0.017673 |

### market_disagreement

| model | disagreement_band | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 10–20pp | 417 | 0.402878 | 0.383700 | 0.239901 | 0.019177 | -0.021608 | 0.062778 | 0.028629 |
| boosting_oos | 20pp+ | 87 | 0.586207 | 0.388631 | 0.269884 | 0.197576 | 0.088619 | 0.295796 | 0.099245 |
| boosting_oos | 5–10pp | 580 | 0.346552 | 0.349926 | 0.221222 | -0.003375 | -0.037244 | 0.030454 | 0.006677 |
| boosting_oos | <5pp | 781 | 0.338028 | 0.335369 | 0.212607 | 0.002660 | -0.029871 | 0.033360 | 0.000970 |
| logistic_oos | 10–20pp | 501 | 0.377246 | 0.393234 | 0.227600 | -0.015989 | -0.055823 | 0.023051 | 0.026995 |
| logistic_oos | 20pp+ | 167 | 0.514970 | 0.398037 | 0.272183 | 0.116933 | 0.035600 | 0.198168 | 0.101353 |
| logistic_oos | 5–10pp | 540 | 0.372222 | 0.371578 | 0.226404 | 0.000644 | -0.033390 | 0.036878 | 0.005937 |
| logistic_oos | <5pp | 657 | 0.363775 | 0.357849 | 0.221456 | 0.005926 | -0.031019 | 0.042837 | 0.001385 |
| margin_elo | 10–20pp | 426 | 0.406103 | 0.380810 | 0.235946 | 0.025294 | -0.025495 | 0.071659 | 0.023121 |
| margin_elo | 20pp+ | 97 | 0.536082 | 0.364433 | 0.292982 | 0.171650 | 0.062505 | 0.268354 | 0.077299 |
| margin_elo | 5–10pp | 570 | 0.331579 | 0.353410 | 0.212393 | -0.021831 | -0.056066 | 0.012624 | 0.009871 |
| margin_elo | <5pp | 772 | 0.343264 | 0.331038 | 0.217066 | 0.012226 | -0.017086 | 0.043287 | 0.002496 |

### Team diagnostics

Largest absolute observed team residuals (descriptive, not persistent bias):

| model | team | games | signed_residual | error_rate | expected_error_rate |
| --- | --- | --- | --- | --- | --- |
| logistic_oos | PIT | 116 | 0.125983 | 0.500000 | 0.383885 |
| logistic_oos | ARI | 116 | -0.108268 | 0.379310 | 0.376749 |
| logistic_oos | CAR | 117 | -0.095956 | 0.401709 | 0.357871 |
| logistic_oos | SEA | 117 | 0.095219 | 0.410256 | 0.401447 |
| logistic_oos | KC | 117 | 0.091929 | 0.333333 | 0.357357 |
| boosting_oos | PIT | 116 | 0.086622 | 0.456897 | 0.367252 |

### Shared base-model failures (each game counted once)

| category | games | average_confidence | average_brier | market_accuracy | market_favorite_agreement | sample_fraction |
| --- | --- | --- | --- | --- | --- | --- |
| all_correct | 974 | 0.672414 | 0.116688 | 0.936345 | 0.936345 | 0.522252 |
| all_incorrect | 499 | 0.640695 | 0.418606 | 0.168337 | 0.830986 | 0.267560 |
| one_incorrect | 203 | 0.565279 | 0.224520 | 0.738916 | 0.580431 | 0.108847 |
| two_incorrect | 189 | 0.554352 | 0.279248 | 0.486772 | 0.503584 | 0.101340 |

Winner-side disagreements: 392/1865 games. Market accuracy where all three bases missed: 16.834%.

## with_frozen_ensemble

| model | games | accuracy | error_rate | expected_error_rate | brier | market_brier | log_loss | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 543 | 0.661142 | 0.338858 | 0.351106 | 0.216419 | 0.206139 | 0.621503 | -0.012247 | -0.051749 | 0.027087 | 0.010280 |
| frozen_ensemble | 543 | 0.650092 | 0.349908 | 0.359921 | 0.216955 | 0.206139 | 0.622611 | -0.010014 | -0.045261 | 0.028135 | 0.010816 |
| logistic_oos | 543 | 0.637201 | 0.362799 | 0.368261 | 0.220803 | 0.206139 | 0.630879 | -0.005462 | -0.041323 | 0.030747 | 0.014664 |
| margin_elo | 543 | 0.651934 | 0.348066 | 0.348007 | 0.219134 | 0.206139 | 0.627875 | 0.000059 | -0.035071 | 0.036538 | 0.012995 |

### confidence

| model | confidence_bucket | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 50–55% | 108 | 0.472222 | 0.475654 | 0.250197 | -0.003432 | -0.094940 | 0.095455 | 0.022459 |
| boosting_oos | 55–60% | 98 | 0.346939 | 0.428025 | 0.232523 | -0.081086 | -0.156655 | -0.000060 | 0.002974 |
| boosting_oos | 60–70% | 162 | 0.358025 | 0.354921 | 0.228865 | 0.003103 | -0.059094 | 0.069894 | 0.016226 |
| boosting_oos | 70–80% | 125 | 0.288000 | 0.254442 | 0.208258 | 0.033558 | -0.058120 | 0.125758 | 0.005462 |
| boosting_oos | 80–90% | 48 | 0.104167 | 0.163329 | 0.095424 | -0.059163 | -0.142959 | 0.044455 | -0.008707 |
| boosting_oos | 90–100% | 2 | 0.000000 | 0.095474 | 0.009118 | -0.095474 | nan | nan | -0.014263 |
| frozen_ensemble | 50–55% | 109 | 0.495413 | 0.477477 | 0.249789 | 0.017936 | -0.073999 | 0.120836 | 0.023399 |
| frozen_ensemble | 55–60% | 129 | 0.410853 | 0.422578 | 0.240777 | -0.011725 | -0.100713 | 0.073704 | 0.008305 |
| frozen_ensemble | 60–70% | 148 | 0.304054 | 0.353607 | 0.213790 | -0.049553 | -0.121635 | 0.027318 | 0.012792 |
| frozen_ensemble | 70–80% | 120 | 0.300000 | 0.254505 | 0.213741 | 0.045495 | -0.042560 | 0.143127 | 0.004154 |
| frozen_ensemble | 80–90% | 37 | 0.054054 | 0.162304 | 0.060258 | -0.108250 | -0.166829 | -0.031125 | -0.003793 |
| logistic_oos | 50–55% | 130 | 0.492308 | 0.474931 | 0.248969 | 0.017377 | -0.055700 | 0.092625 | 0.019322 |
| logistic_oos | 55–60% | 115 | 0.391304 | 0.423997 | 0.240141 | -0.032692 | -0.112543 | 0.043180 | 0.019299 |
| logistic_oos | 60–70% | 162 | 0.358025 | 0.356243 | 0.228527 | 0.001782 | -0.064098 | 0.075273 | 0.018935 |
| logistic_oos | 70–80% | 103 | 0.262136 | 0.252604 | 0.194804 | 0.009532 | -0.093844 | 0.128127 | 0.004150 |
| logistic_oos | 80–90% | 32 | 0.093750 | 0.176217 | 0.088078 | -0.082467 | -0.172825 | 0.021464 | -0.008351 |
| logistic_oos | 90–100% | 1 | 0.000000 | 0.096542 | 0.009320 | -0.096542 | nan | nan | 0.003817 |
| margin_elo | 50–55% | 103 | 0.514563 | 0.473625 | 0.253707 | 0.040938 | -0.068921 | 0.143594 | 0.018371 |
| margin_elo | 55–60% | 105 | 0.352381 | 0.426265 | 0.233482 | -0.073884 | -0.156623 | 0.008956 | 0.016890 |
| margin_elo | 60–70% | 155 | 0.335484 | 0.356125 | 0.221826 | -0.020641 | -0.076464 | 0.036651 | 0.012821 |
| margin_elo | 70–80% | 126 | 0.301587 | 0.255178 | 0.211235 | 0.046410 | -0.029177 | 0.131420 | 0.004436 |
| margin_elo | 80–90% | 49 | 0.183673 | 0.156082 | 0.149123 | 0.027592 | -0.077936 | 0.142608 | 0.021237 |
| margin_elo | 90–100% | 5 | 0.000000 | 0.085400 | 0.007365 | -0.085400 | -0.091843 | -0.075736 | -0.039248 |

### week_phase

| model | week_phase | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 13+ | 187 | 0.363636 | 0.339945 | 0.211827 | 0.023691 | -0.048411 | 0.088165 | 0.013976 |
| boosting_oos | 1–4 | 127 | 0.338583 | 0.371583 | 0.233747 | -0.033000 | -0.122424 | 0.047656 | 0.008045 |
| boosting_oos | 5–12 | 229 | 0.318777 | 0.348863 | 0.210559 | -0.030086 | -0.085966 | 0.030152 | 0.008501 |
| frozen_ensemble | 13+ | 187 | 0.363636 | 0.346265 | 0.211570 | 0.017372 | -0.058550 | 0.086113 | 0.013719 |
| frozen_ensemble | 1–4 | 127 | 0.362205 | 0.377628 | 0.230145 | -0.015423 | -0.087055 | 0.051315 | 0.004444 |
| frozen_ensemble | 5–12 | 229 | 0.331878 | 0.361254 | 0.214038 | -0.029376 | -0.079294 | 0.025145 | 0.011980 |
| logistic_oos | 13+ | 187 | 0.368984 | 0.359472 | 0.217438 | 0.009512 | -0.080346 | 0.089149 | 0.019587 |
| logistic_oos | 1–4 | 127 | 0.385827 | 0.383961 | 0.232024 | 0.001866 | -0.049668 | 0.049672 | 0.006323 |
| logistic_oos | 5–12 | 229 | 0.344978 | 0.366730 | 0.217329 | -0.021752 | -0.063203 | 0.018999 | 0.015270 |
| margin_elo | 13+ | 187 | 0.342246 | 0.324563 | 0.211350 | 0.017683 | -0.061816 | 0.094563 | 0.013499 |
| margin_elo | 1–4 | 127 | 0.385827 | 0.367259 | 0.229117 | 0.018567 | -0.027579 | 0.075325 | 0.003416 |
| margin_elo | 5–12 | 229 | 0.331878 | 0.356475 | 0.219954 | -0.024597 | -0.065494 | 0.027078 | 0.017896 |

### market_agreement

| model | favorite_agreement | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | market_pickem | 2 | 0.500000 | 0.440870 | 0.301452 | 0.059130 | -0.486723 | 0.604983 | 0.051452 |
| boosting_oos | opposite_favorite | 91 | 0.571429 | 0.434356 | 0.266163 | 0.137073 | 0.038163 | 0.225971 | 0.040114 |
| boosting_oos | same_favorite | 450 | 0.291111 | 0.333872 | 0.205982 | -0.042760 | -0.087727 | 0.002470 | 0.004064 |
| frozen_ensemble | market_pickem | 2 | 0.500000 | 0.447675 | 0.273582 | 0.052325 | -0.468103 | 0.572752 | 0.023582 |
| frozen_ensemble | opposite_favorite | 89 | 0.606742 | 0.442855 | 0.267220 | 0.163887 | 0.075778 | 0.246770 | 0.043311 |
| frozen_ensemble | same_favorite | 452 | 0.298673 | 0.343203 | 0.206807 | -0.044531 | -0.088129 | -0.000248 | 0.004361 |
| logistic_oos | market_pickem | 2 | 1.000000 | 0.449556 | 0.303583 | 0.550444 | 0.526079 | 0.574810 | 0.053583 |
| logistic_oos | opposite_favorite | 103 | 0.621359 | 0.437662 | 0.274466 | 0.183697 | 0.104885 | 0.264647 | 0.049382 |
| logistic_oos | same_favorite | 438 | 0.299087 | 0.351569 | 0.207806 | -0.052482 | -0.097788 | -0.008362 | 0.006322 |
| margin_elo | market_pickem | 2 | 0.500000 | 0.426522 | 0.221609 | 0.073478 | -0.391506 | 0.538462 | -0.028391 |
| margin_elo | opposite_favorite | 92 | 0.597826 | 0.432595 | 0.270238 | 0.165231 | 0.062124 | 0.258208 | 0.043529 |
| margin_elo | same_favorite | 449 | 0.296214 | 0.330326 | 0.208652 | -0.034112 | -0.075645 | 0.008801 | 0.006923 |

### divisional

| model | divisional | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | False | 351 | 0.316239 | 0.357072 | 0.211108 | -0.040833 | -0.092345 | 0.009837 | 0.008911 |
| boosting_oos | True | 192 | 0.380208 | 0.340198 | 0.226128 | 0.040011 | -0.014370 | 0.092844 | 0.012783 |
| frozen_ensemble | False | 351 | 0.324786 | 0.367039 | 0.212157 | -0.042253 | -0.087952 | 0.004848 | 0.009960 |
| frozen_ensemble | True | 192 | 0.395833 | 0.346910 | 0.225726 | 0.048924 | -0.004642 | 0.098363 | 0.012382 |
| logistic_oos | False | 351 | 0.341880 | 0.373656 | 0.216634 | -0.031776 | -0.077435 | 0.013787 | 0.014436 |
| logistic_oos | True | 192 | 0.401042 | 0.358398 | 0.228426 | 0.042644 | -0.020317 | 0.104113 | 0.015081 |
| margin_elo | False | 351 | 0.327635 | 0.356728 | 0.214292 | -0.029093 | -0.070296 | 0.013135 | 0.012095 |
| margin_elo | True | 192 | 0.385417 | 0.332064 | 0.227986 | 0.053352 | -0.005428 | 0.114383 | 0.014641 |

### market_disagreement

| model | disagreement_band | games | error_rate | expected_error_rate | brier | excess_error | excess_error_low | excess_error_high | brier_minus_market |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boosting_oos | 10–20pp | 122 | 0.401639 | 0.378374 | 0.232419 | 0.023265 | -0.058110 | 0.097313 | 0.012921 |
| boosting_oos | 20pp+ | 31 | 0.612903 | 0.369462 | 0.268596 | 0.243442 | 0.103505 | 0.379217 | 0.130656 |
| boosting_oos | 5–10pp | 160 | 0.281250 | 0.345005 | 0.192933 | -0.063755 | -0.130275 | 0.006976 | -0.001348 |
| boosting_oos | <5pp | 230 | 0.308696 | 0.338412 | 0.217237 | -0.029716 | -0.085649 | 0.032477 | 0.000743 |
| frozen_ensemble | 10–20pp | 114 | 0.377193 | 0.385259 | 0.221245 | -0.008066 | -0.085771 | 0.069007 | 0.030802 |
| frozen_ensemble | 20pp+ | 17 | 0.588235 | 0.382538 | 0.289287 | 0.205697 | -0.043627 | 0.407026 | 0.177471 |
| frozen_ensemble | 5–10pp | 142 | 0.359155 | 0.374954 | 0.221179 | -0.015799 | -0.087621 | 0.063048 | -0.002986 |
| frozen_ensemble | <5pp | 270 | 0.318519 | 0.339893 | 0.208368 | -0.021374 | -0.073967 | 0.035012 | -0.000857 |
| logistic_oos | 10–20pp | 162 | 0.388889 | 0.394093 | 0.225217 | -0.005204 | -0.074768 | 0.060235 | 0.024607 |
| logistic_oos | 20pp+ | 26 | 0.538462 | 0.388144 | 0.273011 | 0.150318 | -0.020752 | 0.323184 | 0.150608 |
| logistic_oos | 5–10pp | 143 | 0.349650 | 0.368042 | 0.215518 | -0.018392 | -0.080416 | 0.054322 | -0.003110 |
| logistic_oos | <5pp | 212 | 0.330189 | 0.346230 | 0.214593 | -0.016041 | -0.080435 | 0.052286 | 0.002383 |
| margin_elo | 10–20pp | 101 | 0.425743 | 0.371283 | 0.238804 | 0.054460 | -0.030953 | 0.135743 | 0.016915 |
| margin_elo | 20pp+ | 37 | 0.594595 | 0.376227 | 0.295089 | 0.218367 | 0.075184 | 0.354317 | 0.095212 |
| margin_elo | 5–10pp | 162 | 0.283951 | 0.348852 | 0.203659 | -0.064901 | -0.124215 | 0.000016 | 0.009872 |
| margin_elo | <5pp | 243 | 0.320988 | 0.333473 | 0.209711 | -0.012485 | -0.067504 | 0.044263 | 0.000929 |

### Team diagnostics

Largest absolute observed team residuals (descriptive, not persistent bias):

| model | team | games | signed_residual | error_rate | expected_error_rate |
| --- | --- | --- | --- | --- | --- |
| logistic_oos | NYJ | 34 | -0.193125 | 0.323529 | 0.380447 |
| logistic_oos | DEN | 34 | 0.189591 | 0.352941 | 0.374135 |
| logistic_oos | HOU | 34 | 0.184775 | 0.294118 | 0.386268 |
| logistic_oos | SEA | 34 | 0.181611 | 0.411765 | 0.407937 |
| boosting_oos | SEA | 34 | 0.169572 | 0.323529 | 0.388160 |
| boosting_oos | DEN | 34 | 0.165843 | 0.323529 | 0.351621 |

## Measured findings

- All three base models missed 499/1865 games (26.76%); the market picked correctly in 84/499 of those. This is a descriptive same-game comparison, not an explanation of losses or an executable market opportunity.
- Weeks 1–4 observed base-model error rates range from 38.69% to 39.59%; confidence-adjusted excess error ranges from 0.36% to 1.61%. All early-season excess-error intervals contain zero: True. Raw early-season difficulty alone does not establish a special calibration failure.
- The predefined 80–90% margin-Elo band has 155 games, observed losses 22.58% versus expected 15.92%; excess-error interval 0.68% to 12.65%. This is an exploratory calibration candidate among many slices, not a validated general effect or an instruction to recalibrate.
- The twenty most confident misses contain 16 distinct games; 19/20 agree with the closing favorite. 1/20 have absolute recent offensive EPA advantage ≥0.25. These outcome-selected examples have no control group and cannot establish why a game was lost.
- On their corresponding samples, 7/7 model comparisons have higher mean Brier than closing; 7/7 aggregate excess-error intervals contain zero. These descriptive results must not be used to select a model or a winning story.

## Twenty most confident incorrect observations

| season | week | game_id | home_team | away_team | home_score | away_score | model | probability | confidence | actual_winner | market_probability | market_probability_difference | off_epa | def_epa | recent_off_epa | recent_def_epa | elo_difference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 15 | 2020_15_NYJ_LA | LA | NYJ | 20 | 23 | margin_elo | 0.910995 | 0.910995 | NYJ | 0.908664 | 0.002331 | 0.168651 | 0.247959 | 0.084436 | 0.180861 | 205.529463 |
| 2019 | 10 | 2019_10_ATL_NO | NO | ATL | 9 | 26 | boosting_oos | 0.902509 | 0.902509 | ATL | 0.839356 | 0.063153 | 0.038877 | 0.191805 | 0.062298 | 0.234143 | 158.795544 |
| 2022 | 10 | 2022_10_WAS_PHI | PHI | WAS | 21 | 32 | boosting_oos | 0.896749 | 0.896749 | WAS | 0.808052 | 0.088697 | 0.197750 | 0.040510 | 0.165167 | -0.000635 | 93.643200 |
| 2020 | 17 | 2020_17_LAC_KC | KC | LAC | 21 | 38 | margin_elo | 0.896015 | 0.896015 | LAC | 0.282528 | 0.613488 | 0.145027 | -0.001125 | 0.001598 | 0.046926 | 198.532642 |
| 2024 | 18 | 2024_18_BUF_NE | NE | BUF | 23 | 16 | margin_elo | 0.108922 | 0.891078 | NE | 0.400361 | -0.291439 | -0.278832 | -0.075578 | -0.261601 | -0.077566 | -241.126843 |
| 2021 | 10 | 2021_10_CAR_ARI | ARI | CAR | 10 | 34 | boosting_oos | 0.890627 | 0.890627 | CAR | 0.744521 | 0.146106 | 0.198413 | 0.004139 | 0.185026 | 0.036944 | 100.544385 |
| 2019 | 4 | 2019_04_CLE_BAL | BAL | CLE | 25 | 40 | boosting_oos | 0.890521 | 0.890521 | CLE | 0.743748 | 0.146773 | 0.236188 | -0.013804 | 0.236188 | -0.013804 | 99.421347 |
| 2021 | 11 | 2021_11_HOU_TEN | TEN | HOU | 13 | 22 | margin_elo | 0.890336 | 0.890336 | HOU | 0.796799 | 0.093537 | 0.182782 | 0.077177 | 0.137962 | 0.078105 | 176.225240 |
| 2019 | 17 | 2019_17_MIA_NE | NE | MIA | 24 | 27 | boosting_oos | 0.887397 | 0.887397 | MIA | 0.889942 | -0.002545 | 0.108659 | 0.329643 | 0.020674 | 0.073871 | 193.840095 |
| 2019 | 17 | 2019_17_MIA_NE | NE | MIA | 24 | 27 | margin_elo | 0.884445 | 0.884445 | MIA | 0.889942 | -0.005496 | 0.108659 | 0.329643 | 0.020674 | 0.073871 | 193.840095 |
| 2021 | 18 | 2021_18_IND_JAX | JAX | IND | 26 | 11 | margin_elo | 0.122434 | 0.877566 | JAX | 0.127907 | -0.005473 | -0.162631 | -0.138123 | -0.082893 | -0.124459 | -203.978358 |
| 2021 | 11 | 2021_11_HOU_TEN | TEN | HOU | 13 | 22 | boosting_oos | 0.876774 | 0.876774 | HOU | 0.796799 | 0.079975 | 0.182782 | 0.077177 | 0.137962 | 0.078105 | 176.225240 |
| 2021 | 18 | 2021_18_GB_DET | DET | GB | 37 | 30 | margin_elo | 0.125335 | 0.874665 | DET | 0.363412 | -0.238077 | -0.201718 | -0.114181 | -0.148611 | -0.078688 | -258.188611 |
| 2019 | 10 | 2019_10_MIA_IND | IND | MIA | 12 | 16 | boosting_oos | 0.871870 | 0.871870 | MIA | 0.802240 | 0.069631 | 0.201635 | 0.125231 | 0.051711 | 0.106202 | 98.074263 |
| 2019 | 4 | 2019_04_CLE_BAL | BAL | CLE | 25 | 40 | logistic_oos | 0.870145 | 0.870145 | CLE | 0.743748 | 0.126397 | 0.236188 | -0.013804 | 0.236188 | -0.013804 | 99.421347 |
| 2021 | 9 | 2021_09_BUF_JAX | JAX | BUF | 9 | 6 | margin_elo | 0.130259 | 0.869741 | JAX | 0.110735 | 0.019524 | -0.162057 | -0.283770 | -0.157026 | -0.105607 | -205.020464 |
| 2019 | 10 | 2019_10_ATL_NO | NO | ATL | 9 | 26 | margin_elo | 0.866058 | 0.866058 | ATL | 0.839356 | 0.026702 | 0.038877 | 0.191805 | 0.062298 | 0.234143 | 158.795544 |
| 2024 | 18 | 2024_18_CHI_GB | GB | CHI | 22 | 24 | margin_elo | 0.864520 | 0.864520 | CHI | 0.771505 | 0.093015 | 0.150125 | 0.066060 | 0.134067 | 0.098638 | 164.718500 |
| 2023 | 17 | 2023_17_ARI_PHI | PHI | ARI | 31 | 35 | margin_elo | 0.860376 | 0.860376 | ARI | 0.846501 | 0.013875 | 0.169417 | 0.058435 | 0.081353 | 0.084044 | 194.002934 |
| 2020 | 13 | 2020_13_WAS_PIT | PIT | WAS | 17 | 23 | margin_elo | 0.859982 | 0.859982 | WAS | 0.706155 | 0.153828 | 0.080836 | 0.123504 | -0.030428 | 0.145943 | 187.049040 |

Rows are unique model/game forecasts; several can describe the same game and are not independent examples. They were selected by confidence after seeing outcomes, so shared characteristics here cannot establish an explanatory mechanism. EPA/Elo/scoring values are pregame cache values, not postgame recalculations.

## Interpretation, uncertainty and candidate research

Probabilities exactly 50% use a deterministic home pick; market pick’em is labeled separately, not a favorite. Shared-failure groups are defined by observed outcomes, so their average confidence is descriptive rather than a conditional calibration test. Winner error is distinct from probabilistic loss: a 51% favorite is expected to lose 49% of games, while a high-confidence miss contributes far more Brier/log loss. Confidence buckets show expected versus observed win rates; calibration gap is actual minus expected win frequency. Excess error is observed minus predicted favorite-loss rate. Positive excess error may suggest overconfidence; its interval and reference must be inspected before calling a pattern systematic.

Every detailed slice reports count, expected error, error rate, Brier/log loss, reference model-wide error/Brier, confidence-adjusted excess error, and descriptive 95% season-week cluster intervals (2,000 resamples, seed 42). Matched Brier-minus-market intervals use identical games inside each slice. Model-wide references include the slice. Difference from that reference is descriptive; its own interval is not estimated. Compare phase_confidence and divisional_confidence within the same confidence band before interpreting raw group errors. Absolute EPA bands (<0.10, 0.10–0.25, ≥0.25), confidence and market bands were predefined, not selected to maximize an outcome.

Team tables count a game once for each participating team; they must not be summed into independent observations. Signed residual is actual minus probability in the named team perspective. Categories overlap, teams recur across weeks, and seasons are few. Week bootstrap assumes independent week clusters, misses longer dependence, and does not adjust for the many exploratory comparisons. Small samples (<50) are flagged; intervals are withheld when fewer than two week clusters are available, and small-sample bootstrap intervals remain unreliable. Correlations, extreme examples and category differences are noncausal and are not significance-selected discoveries.

Detailed feature diagnostics compare Elo versus offensive efficiency direction, recent versus season EPA direction, offense/defense advantage directions, and neutral/home venue. Zero directions are grouped with disagreement; missing values remain explicit. These are analysis labels, never new model inputs. Existing M2 production coefficient/contribution reports are not applied to the M7 annual-refit forecasts: they describe different fitted artifacts and would not justify per-game attribution here.

Hypotheses for future prespecified research: check whether any early-season excess error persists within confidence bands across seasons; examine whether recent/season efficiency conflicts repeat prospectively; collect timestamp-aligned market observations to distinguish later market information from model disagreement. None establishes an injury, QB, weather or football-causal explanation. Negative/inconclusive strata and confidence intervals are retained in the CSVs; no model, feature, threshold or team adjustment is selected.

Closing prices can include later information than model cutoffs. Bookmaker, original quote time and executable prices are unknown. Historical data/model vintages and previously explored evaluation years limit inference. The analysis does not identify executable betting opportunities or profitability.

Recommended next research: preserve the existing models and M8.3 checkpoint policy, collect genuinely aligned prospective forecasts/markets, and preregister any proposed confidence/season-phase contrast before further evaluation. No M9.2 modeling is started.

## Reproduction and audit

`python -m nfl_predictor.cli report-m91a` reads only existing M7 outputs, schedule Parquets and compact pregame caches. Detailed tables: reports/m91a; game/model errors: M91A_CLASSIFIED_ERRORS.csv. Duplicate sample labels identify repeated base rows in the narrower comparison; do not pool samples.

| input | sha256 |
| --- | --- |
| schedules/2019 | 490ae0ba90099fc099ab6177b573d177f45c4c26c4a38c78e747184f89c70ab2 |
| pregame_features/2019 | fa77d3fb45fe420c2f5d29ca2e8409f23ea84ccc3f206c035b94b639ae738216 |
| schedules/2020 | a585db1c876ba699c9e02f07ed22a2dda37526b25b6924e1b6ae94a6e02b3400 |
| pregame_features/2020 | de8ef8bfe1fb76eed3aa33ba8003edb6eb2b54da1dc85d44dc1f085aaa5ff8da |
| schedules/2021 | 8273e3b50d26a010b83927dc1273f6eb2f8e13031065428770d92bfcfc41149f |
| pregame_features/2021 | 7803cb8abe685f8470642ca75eafc4948fa0245665e09ad4c561da84fb8a6626 |
| schedules/2022 | 1e80b33dae054fb5e35e958d58ce62084e0232efd40a1e2082fed618a62a1404 |
| pregame_features/2022 | 64e2954b50f71270c936f00902b513e998e6dd9025826f16dabc5d1f039e78ec |
| schedules/2023 | 16432451e901643d9521d703c377c93202e3ba3bb369bc4265bb6fbeed38812f |
| pregame_features/2023 | 36dff27597c0bd9e59cef9d61f089605bbf253ab2c0a428b23106096957a84b8 |
| schedules/2024 | 3c9b4ac76f93e7b62673ddf220df9e3574fdf02694d18ab7f7f121f15a202a5a |
| pregame_features/2024 | e785bc448e69f27fc6fe4567e1beecc716d118c84b3f091fb5efbd0c5a7e8e89 |
| schedules/2025 | da34c7753becfa89be45efa321a1e27c5ba5065eb332680b01f224e9ca5ad83f |
| pregame_features/2025 | cdf643769d1c67a1b68861772e81ba7b6468da159de88f5440b299794f7d19a9 |
| base_predictions.parquet | a3ca327bda1879b35e71d45993602884e7ce05f3fedb0ab47ae1f20cefe4f0ae |
| predictions.parquet | c8c8cd8e4fda45df1832052dd97cac2f8551d0d5cc026074d27c920ff680e743 |
| selection.json | b37d2128803cc9f1aaf75545290c4c456ae1dad4ec883811c411b7fc4b8310ac |
| metadata.json | 9c1f7c48b6daa451244219177ceb0780a044cf402d1d87088bf2caeedce6fac3 |

Native Windows testing has not been executed. Focused/full test and preservation results are appended after actual verification.

## Execution verification

Starting baseline: `c063c6a7af040f1e91875500583cd184f178e21e`, clean M9.1 tree. Actual collection confirmed **210 starting tests**. Relevant M8.1/M9.1 baseline tests: **16 passed in 1.97s**. New targeted suite: **6 passed in 3.07s**, no warnings. The real offline report command succeeded using unchanged saved predictions; no network, inference, retraining or personnel collection was invoked.

Actual sample sizes: **1,865** matched 2019–2025 games for all three bases; **543** eligible matched 2024–2025 games for all four predictors including the frozen ensemble. The classified CSV has **7,767** model/game/sample observations because base predictions also appear in the narrower comparison; sample labels must be respected. The report includes the top 20 incorrect model/game observations spanning **16 distinct games**.

Confidence-, favorite- and model/market-disagreement-defined slices are model-specific descriptive groups, not direct head-to-head rankings between models on different subsets. Overall, season/phase, shared-failure and feature-defined comparisons use the common game universe; each model-versus-market Brier difference always uses that model’s identical selected games. The full confidence-conditioned phase/divisional tables are included in the detailed CSVs.

Pre/post SHA-256 verification currently confirms **2723 protected existing files unchanged**, covering original models, M7 predictions/forecasts, M8 odds/wagers, historical benchmarks, M8.3 records, M9.1 source evidence and snapshots, and compact pregame caches. Preservation manifest SHA-256: `263128fbaef0913ea6ef0f67d7f20049f0cb4cf07ce6f4c5498a33fd7778df3c`.


Full regression suite executed once after focused checks: **216 passed, 8 warnings in 170.12s (0:02:50)**. The eight existing warnings concern Streamlit/pandas deprecations and the synthetic play-count coverage fixture. Final verification again found **zero changes across all 2,723 protected files**. Native Windows verification remains unexecuted. `git diff --check` passed.

Delivered: cached OOS reuse, winner/probability-loss classifications, confidence/phase/favorite/division/team/feature diagnostics, unique-game shared failures, exact-game closing comparisons, top-20 incorrect observations, research hypotheses and limitations, focused/full tests, classified-error CSV and compact summary CSVs. No models, policies, production records or source data were changed; M9.2 was not started.
