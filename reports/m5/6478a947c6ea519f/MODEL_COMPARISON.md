# M5 exploratory historical-training comparison

Window selection uses development validation through 2021 only. Each common-feature window sees identical pregame state and evaluation games. W1 is the earliest *training-label* policy; it is not a reinitialization of priors/Elo. Original full-feature M2/M4 references use their original 2018-onward feature history and are exported separately.

## Development window ranking

| algorithm | window | brier | log_loss |
| --- | --- | --- | --- |
| hgb | W3 | 0.224189 | 0.639990 |
| hgb | W4 | 0.224899 | 0.640953 |
| hgb | W2 | 0.226324 | 0.645778 |
| hgb | W1 | 0.232017 | 0.658572 |
| logistic | W3 | 0.224593 | 0.640373 |
| logistic | W4 | 0.225116 | 0.641238 |
| logistic | W2 | 0.226167 | 0.644582 |
| logistic | W1 | 0.230397 | 0.655211 |

## Development decay ranking

| algorithm | window | half_life | brier | log_loss |
| --- | --- | --- | --- | --- |
| hgb | W3 | 0 | 0.224189 | 0.639990 |
| hgb | W3 | 8 | 0.224689 | 0.641375 |
| hgb | W4 | 0 | 0.224899 | 0.640953 |
| hgb | W3 | 5 | 0.225488 | 0.642896 |
| hgb | W4 | 5 | 0.225711 | 0.643188 |
| hgb | W4 | 3 | 0.225724 | 0.643355 |
| hgb | W4 | 8 | 0.225971 | 0.643467 |
| hgb | W3 | 3 | 0.226382 | 0.645075 |
| logistic | W3 | 0 | 0.224593 | 0.640373 |
| logistic | W4 | 5 | 0.224643 | 0.640701 |
| logistic | W4 | 8 | 0.224665 | 0.640549 |
| logistic | W3 | 8 | 0.224689 | 0.640834 |
| logistic | W3 | 5 | 0.224762 | 0.641151 |
| logistic | W4 | 3 | 0.224827 | 0.641465 |
| logistic | W3 | 3 | 0.224936 | 0.641804 |
| logistic | W4 | 0 | 0.225116 | 0.641238 |

Selected windows: `{"logistic": ["W3", "W4"], "hgb": ["W3", "W4"]}`; selected policies: `{"logistic": {"window": "W3", "half_life": 0.0}, "hgb": {"window": "W3", "half_life": 0.0}}`. All candidates remain experimental.

## Uniform windows and references

| model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- |
| elo_extended | accuracy | 0.639042 | -0.005525 | -0.044447 | 0.032613 | 543 |
| elo_extended | brier | 0.224453 | 0.003499 | -0.004344 | 0.011930 | 543 |
| elo_extended | log_loss | 0.639687 | 0.008408 | -0.008260 | 0.026283 | 543 |
| elo_original | accuracy | 0.639042 | -0.005525 | -0.044447 | 0.032613 | 543 |
| elo_original | brier | 0.224492 | 0.003538 | -0.004322 | 0.011979 | 543 |
| elo_original | log_loss | 0.639773 | 0.008493 | -0.008243 | 0.026349 | 543 |
| hgb_W1_uniform | accuracy | 0.648250 | 0.003683 | -0.025880 | 0.031425 | 543 |
| hgb_W1_uniform | brier | 0.219158 | -0.001796 | -0.008091 | 0.004740 | 543 |
| hgb_W1_uniform | log_loss | 0.628583 | -0.002696 | -0.016679 | 0.012119 | 543 |
| hgb_W2_uniform | accuracy | 0.651934 | 0.007366 | -0.020074 | 0.034423 | 543 |
| hgb_W2_uniform | brier | 0.216486 | -0.004468 | -0.010973 | 0.002132 | 543 |
| hgb_W2_uniform | log_loss | 0.622496 | -0.008784 | -0.023255 | 0.005719 | 543 |
| hgb_W3_uniform | accuracy | 0.664825 | 0.020258 | -0.001859 | 0.042514 | 543 |
| hgb_W3_uniform | brier | 0.214954 | -0.006000 | -0.011661 | -0.000335 | 543 |
| hgb_W3_uniform | log_loss | 0.618001 | -0.013279 | -0.025961 | -0.000038 | 543 |
| hgb_W4_uniform | accuracy | 0.662983 | 0.018416 | -0.003683 | 0.040441 | 543 |
| hgb_W4_uniform | brier | 0.216392 | -0.004562 | -0.010243 | 0.001302 | 543 |
| hgb_W4_uniform | log_loss | 0.620886 | -0.010393 | -0.023430 | 0.003397 | 543 |
| logistic | accuracy | 0.644567 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | brier | 0.220954 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic | log_loss | 0.631279 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W1_uniform | accuracy | 0.657459 | 0.012891 | -0.003697 | 0.031080 | 543 |
| logistic_W1_uniform | brier | 0.218871 | -0.002083 | -0.004483 | 0.000475 | 543 |
| logistic_W1_uniform | log_loss | 0.627051 | -0.004229 | -0.010027 | 0.002096 | 543 |
| logistic_W2_uniform | accuracy | 0.642726 | -0.001842 | -0.021087 | 0.018685 | 543 |
| logistic_W2_uniform | brier | 0.218664 | -0.002289 | -0.006296 | 0.001915 | 543 |
| logistic_W2_uniform | log_loss | 0.625938 | -0.005341 | -0.014336 | 0.004506 | 543 |
| logistic_W3_uniform | accuracy | 0.644567 | 0.000000 | -0.024074 | 0.024255 | 543 |
| logistic_W3_uniform | brier | 0.219166 | -0.001787 | -0.005189 | 0.001841 | 543 |
| logistic_W3_uniform | log_loss | 0.626949 | -0.004330 | -0.012286 | 0.004235 | 543 |
| logistic_W4_uniform | accuracy | 0.651934 | 0.007366 | -0.020000 | 0.034930 | 543 |
| logistic_W4_uniform | brier | 0.219417 | -0.001537 | -0.005106 | 0.002357 | 543 |
| logistic_W4_uniform | log_loss | 0.627308 | -0.003972 | -0.011996 | 0.004841 | 543 |
| margin_elo_extended | accuracy | 0.651934 | 0.007366 | -0.025936 | 0.039108 | 543 |
| margin_elo_extended | brier | 0.219131 | -0.001823 | -0.009639 | 0.006041 | 543 |
| margin_elo_extended | log_loss | 0.627868 | -0.003412 | -0.020545 | 0.014747 | 543 |
| margin_elo_original | accuracy | 0.651934 | 0.007366 | -0.025936 | 0.039108 | 543 |
| margin_elo_original | brier | 0.219134 | -0.001819 | -0.009637 | 0.006045 | 543 |
| margin_elo_original | log_loss | 0.627875 | -0.003404 | -0.020536 | 0.014756 | 543 |
| original_hgb | accuracy | 0.661142 | 0.016575 | -0.003677 | 0.036902 | 543 |
| original_hgb | brier | 0.217426 | -0.003528 | -0.009152 | 0.002531 | 543 |
| original_hgb | log_loss | 0.624715 | -0.006564 | -0.019219 | 0.007074 | 543 |
| pregame_win_percentage | accuracy | 0.657459 | 0.012891 | -0.022141 | 0.053712 | 543 |
| pregame_win_percentage | brier | 0.222769 | 0.001815 | -0.007872 | 0.010635 | 543 |
| pregame_win_percentage | log_loss | 0.637090 | 0.005810 | -0.014712 | 0.025073 | 543 |

## Recency differences from the same window uniform model

| model | metric | estimate | difference | difference_low | difference_high | games |
| --- | --- | --- | --- | --- | --- | --- |
| logistic_W3_half3 | accuracy | 0.653775 | 0.009208 | -0.011029 | 0.030190 | 543 |
| logistic_W3_half3 | brier | 0.217940 | -0.001226 | -0.003556 | 0.001009 | 543 |
| logistic_W3_half3 | log_loss | 0.624836 | -0.002113 | -0.007418 | 0.003096 | 543 |
| logistic_W3_half5 | accuracy | 0.648250 | 0.003683 | -0.010949 | 0.018519 | 543 |
| logistic_W3_half5 | brier | 0.218171 | -0.000995 | -0.002487 | 0.000474 | 543 |
| logistic_W3_half5 | log_loss | 0.625116 | -0.001834 | -0.005203 | 0.001553 | 543 |
| logistic_W3_half8 | accuracy | 0.646409 | 0.001842 | -0.008962 | 0.012939 | 543 |
| logistic_W3_half8 | brier | 0.218460 | -0.000707 | -0.001681 | 0.000264 | 543 |
| logistic_W3_half8 | log_loss | 0.625613 | -0.001336 | -0.003555 | 0.000811 | 543 |
| logistic_W3_uniform | accuracy | 0.644567 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W3_uniform | brier | 0.219166 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W3_uniform | log_loss | 0.626949 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W3_uniform_isotonic | accuracy | 0.653775 | 0.009208 | -0.014788 | 0.033212 | 543 |
| logistic_W3_uniform_isotonic | brier | 0.217167 | -0.001999 | -0.006412 | 0.002320 | 543 |
| logistic_W3_uniform_isotonic | log_loss | 0.619195 | -0.007754 | -0.018899 | 0.002736 | 543 |
| logistic_W3_uniform_sigmoid | accuracy | 0.633517 | -0.011050 | -0.023811 | 0.001822 | 543 |
| logistic_W3_uniform_sigmoid | brier | 0.221636 | 0.002470 | -0.001894 | 0.006555 | 543 |
| logistic_W3_uniform_sigmoid | log_loss | 0.633368 | 0.006419 | -0.004383 | 0.016573 | 543 |
| logistic_W4_half3 | accuracy | 0.659300 | 0.007366 | -0.018519 | 0.034289 | 543 |
| logistic_W4_half3 | brier | 0.217939 | -0.001478 | -0.005262 | 0.002245 | 543 |
| logistic_W4_half3 | log_loss | 0.624784 | -0.002524 | -0.011039 | 0.005848 | 543 |
| logistic_W4_half5 | accuracy | 0.644567 | -0.007366 | -0.025831 | 0.009522 | 543 |
| logistic_W4_half5 | brier | 0.218159 | -0.001258 | -0.003947 | 0.001464 | 543 |
| logistic_W4_half5 | log_loss | 0.624959 | -0.002349 | -0.008380 | 0.003676 | 543 |
| logistic_W4_half8 | accuracy | 0.642726 | -0.009208 | -0.024030 | 0.003774 | 543 |
| logistic_W4_half8 | brier | 0.218497 | -0.000919 | -0.002762 | 0.000911 | 543 |
| logistic_W4_half8 | log_loss | 0.625510 | -0.001798 | -0.005891 | 0.002277 | 543 |
| logistic_W4_uniform | accuracy | 0.651934 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W4_uniform | brier | 0.219417 | 0.000000 | 0.000000 | 0.000000 | 543 |
| logistic_W4_uniform | log_loss | 0.627308 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W3_half3 | accuracy | 0.655617 | -0.009208 | -0.029978 | 0.010969 | 543 |
| hgb_W3_half3 | brier | 0.216696 | 0.001742 | -0.002428 | 0.005984 | 543 |
| hgb_W3_half3 | log_loss | 0.622341 | 0.004340 | -0.004803 | 0.014112 | 543 |
| hgb_W3_half5 | accuracy | 0.655617 | -0.009208 | -0.027424 | 0.007449 | 543 |
| hgb_W3_half5 | brier | 0.216140 | 0.001186 | -0.001751 | 0.004275 | 543 |
| hgb_W3_half5 | log_loss | 0.621593 | 0.003592 | -0.003239 | 0.010770 | 543 |
| hgb_W3_half8 | accuracy | 0.651934 | -0.012891 | -0.026372 | 0.000000 | 543 |
| hgb_W3_half8 | brier | 0.215390 | 0.000437 | -0.001734 | 0.002761 | 543 |
| hgb_W3_half8 | log_loss | 0.619438 | 0.001437 | -0.003609 | 0.006745 | 543 |
| hgb_W3_uniform | accuracy | 0.664825 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W3_uniform | brier | 0.214954 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W3_uniform | log_loss | 0.618001 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W3_uniform_isotonic | accuracy | 0.664825 | 0.000000 | -0.022061 | 0.022398 | 543 |
| hgb_W3_uniform_isotonic | brier | 0.218542 | 0.003589 | -0.002252 | 0.009104 | 543 |
| hgb_W3_uniform_isotonic | log_loss | 0.624896 | 0.006895 | -0.006766 | 0.019718 | 543 |
| hgb_W3_uniform_sigmoid | accuracy | 0.657459 | -0.007366 | -0.018315 | 0.003690 | 543 |
| hgb_W3_uniform_sigmoid | brier | 0.218241 | 0.003287 | -0.000706 | 0.007123 | 543 |
| hgb_W3_uniform_sigmoid | log_loss | 0.626259 | 0.008258 | -0.002024 | 0.017767 | 543 |
| hgb_W4_half3 | accuracy | 0.661142 | -0.001842 | -0.022311 | 0.018823 | 543 |
| hgb_W4_half3 | brier | 0.216344 | -0.000048 | -0.004905 | 0.005038 | 543 |
| hgb_W4_half3 | log_loss | 0.622013 | 0.001127 | -0.009861 | 0.012536 | 543 |
| hgb_W4_half5 | accuracy | 0.657459 | -0.005525 | -0.025594 | 0.014679 | 543 |
| hgb_W4_half5 | brier | 0.215657 | -0.000735 | -0.004192 | 0.002814 | 543 |
| hgb_W4_half5 | log_loss | 0.620225 | -0.000661 | -0.008750 | 0.007693 | 543 |
| hgb_W4_half8 | accuracy | 0.662983 | 0.000000 | -0.016698 | 0.016854 | 543 |
| hgb_W4_half8 | brier | 0.215473 | -0.000919 | -0.003584 | 0.001728 | 543 |
| hgb_W4_half8 | log_loss | 0.620015 | -0.000871 | -0.006981 | 0.005311 | 543 |
| hgb_W4_uniform | accuracy | 0.662983 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W4_uniform | brier | 0.216392 | 0.000000 | 0.000000 | 0.000000 | 543 |
| hgb_W4_uniform | log_loss | 0.620886 | 0.000000 | 0.000000 | 0.000000 | 543 |

Positive accuracy and negative Brier/log-loss differences favor the candidate. comparison.csv references the original M2 logistic; within_algorithm.csv references same-algorithm common-feature W1; decay_effects.csv references the identical-window uniform policy. These distinct references must not be conflated. All intervals are unadjusted exploratory paired season-week bootstrap intervals. An interval excluding zero after many comparisons is not independent confirmation.

## Source and calibration limits

Date-only games use local day start as feature lower bound and next day 08:00 Eastern as availability upper proxy; no actual clock fabricated. Rest excluded from every common-feature window.

1999–2000 PBP has some missing game coverage. Source and pregame feature completeness are reported separately; missing values remain missing until training-only preprocessing/native handling. EPA is a contemporary nflverse retrospective estimate and original source vintages are not reconstructed. Sigmoid/eligible isotonic variants are fit only on the intervening calibration season for the development-selected policy, never using evaluation outcomes. The first calibration year was also used for development; subsequent evaluation is separate but not a new untouched historical test.
