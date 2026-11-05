# M9.1 personnel source audit and prospective evidence

No new model, feature, forecast probability, personnel weighting or starter inference was created. M6 evidence is reused for comparison, not silently promoted into this independent additive store.

## Inventory and measured coverage

| source | installed_signature | documented_start |
| --- | --- | --- |
| load_injuries | (seasons: int / list[int] / bool / None = None) -> polars.dataframe.frame.DataFrame | 2009 |
| load_depth_charts | (seasons: int / list[int] / bool / None = None) -> polars.dataframe.frame.DataFrame | 2001 |
| load_rosters_weekly | (seasons: int / list[int] / bool / None = None) -> polars.dataframe.frame.DataFrame | 2002 |
| load_player_stats | (seasons: int / list[int] / bool / None = None, summary_level: Literal['week', 'reg', 'post', 'reg+post'] = 'week') -> polars.dataframe.frame.DataFrame | 1999 |
| load_snap_counts | (seasons: int / list[int] / bool / None = None) -> polars.dataframe.frame.DataFrame | 2012 |

Documented start years describe library support, not verified complete availability. Representative full-season downloads were inspected first (2019, 2026); injury/depth samples extend the 2019–2026 audit. Cached 2024 depth charts and M6 player samples are reused. Unlisted source/seasons are unmeasured; no complete 2019–2026 roster/stat/snap coverage is claimed.

| source | season | rows | exact_duplicate_rows | weeks | teams | players | missing_player_ids | unknown_teams | source_timestamp_rows | missing_game_designation | qb_rows | historical_source_timestamped | retrospective | unknown | roster_pair_match_rate | roster_pair_match_denominator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| load_depth_charts | 2019 | 36308 | 170 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 2092 | 0 | 0 | 0 | 36308 | 1559 | 0 | 36308 | 0 | 1.000000 | 36308.000000 |
| load_depth_charts | 2020 | 36168 | 85 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 2140 | 0 | 0 | 0 | 36168 | 1631 | 0 | 36168 | 0 | nan | nan |
| load_depth_charts | 2021 | 37487 | 145 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 2154 | 0 | 0 | 0 | 37487 | 1591 | 0 | 37487 | 0 | nan | nan |
| load_depth_charts | 2022 | 37780 | 171 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 2073 | 0 | 0 | 0 | 37780 | 1586 | 0 | 37780 | 0 | nan | nan |
| load_depth_charts | 2023 | 37327 | 182 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 2007 | 0 | 0 | 0 | 37327 | 1574 | 0 | 37327 | 0 | nan | nan |
| load_depth_charts | 2024 | 37312 | 207 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 2054 | 0 | 0 | 0 | 37312 | 1551 | 0 | 37312 | 0 | nan | nan |
| load_depth_charts | 2025 | 554215 | 0 | [] | 32 | 2985 | 5577 | 0 | 554215 | 554215 | 21429 | 548638 | 0 | 5577 | nan | nan |
| load_depth_charts | 2026 | 745124 | 0 | [] | 32 | 3062 | 22440 | 0 | 745124 | 745124 | 28889 | 722684 | 0 | 22440 | 0.912425 | 722684.000000 |
| load_injuries | 2019 | 5392 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 1330 | 0 | 0 | 5392 | 2858 | 165 | 5392 | 0 | 0 | 1.000000 | 5392.000000 |
| load_injuries | 2020 | 5661 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 1435 | 0 | 0 | 5661 | 3126 | 166 | 5661 | 0 | 0 | nan | nan |
| load_injuries | 2021 | 5587 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 1446 | 0 | 0 | 5587 | 3020 | 219 | 5587 | 0 | 0 | nan | nan |
| load_injuries | 2022 | 5682 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 1418 | 0 | 0 | 5682 | 2937 | 212 | 5682 | 0 | 0 | nan | nan |
| load_injuries | 2023 | 5599 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19] | 32 | 1413 | 0 | 0 | 5599 | 2878 | 197 | 5599 | 0 | 0 | nan | nan |
| load_injuries | 2024 | 6215 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 1459 | 0 | 0 | 6215 | 3386 | 201 | 6215 | 0 | 0 | nan | nan |
| load_injuries | 2025 | 6068 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 1453 | 0 | 0 | 0 | 3283 | 237 | 0 | 6068 | 0 | nan | nan |
| load_injuries | 2026 | 2487 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9] | 32 | 989 | 0 | 0 | 0 | 1420 | 87 | 0 | 2487 | 0 | 1.000000 | 2487.000000 |
| load_player_stats | 1999 | 16839 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 31 | 1683 | 0 | 1 | 0 | 16839 | 662 | 0 | 16838 | 1 | nan | nan |
| load_player_stats | 2019 | 17362 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 1890 | 21 | 0 | 0 | 17362 | 614 | 0 | 17341 | 21 | 1.000000 | 17341.000000 |
| load_player_stats | 2024 | 18983 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22] | 32 | 2001 | 22 | 0 | 0 | 18983 | 697 | 0 | 18961 | 22 | nan | nan |
| load_player_stats | 2026 | 8428 | 0 | [1, 2, 3, 4, 5, 6, 7, 8] | 32 | 1734 | 8 | 0 | 0 | 8428 | 277 | 0 | 8420 | 8 | 1.000000 | 8420.000000 |
| load_rosters_weekly | 2019 | 51632 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 3112 | 2 | 0 | 0 | 51632 | 2155 | 0 | 51630 | 2 | 1.000000 | 51630.000000 |
| load_rosters_weekly | 2026 | 19865 | 0 | [1, 2, 3, 4, 5, 6, 7, 8] | 32 | 3062 | 9 | 0 | 0 | 19865 | 845 | 0 | 19856 | 9 | 1.000000 | 19856.000000 |
| load_snap_counts | 2012 | 0 | 0 | [] | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | nan | nan |
| load_snap_counts | 2019 | 23862 | 0 | [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21] | 32 | 1205 | 8820 | 0 | 0 | 23862 | 644 | 0 | 15042 | 8820 | 1.000000 | 15042.000000 |
| load_snap_counts | 2026 | 11292 | 0 | [1, 2, 3, 4, 5, 6, 7, 8] | 32 | 1587 | 2109 | 0 | 0 | 11292 | 286 | 0 | 9183 | 2109 | 1.000000 | 9183.000000 |

All counts include source regular/postseason rows where present. Week lists/weekly counts do not prove all expected games or timely reports. Duplicate counts are exact full-row duplicates; different updates/ranks are preserved, not deduplicated into an invented truth. Missing player IDs and unknown teams stay uncertain.

## Actual schemas

### load_depth_charts / 2019

{"club_code": "String", "depth_position": "String", "depth_team": "String", "elias_id": "String", "first_name": "String", "football_name": "String", "formation": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "jersey_number": "String", "last_name": "String", "position": "String", "season": "Int32", "week": "Int32"}

### load_depth_charts / 2020

{"club_code": "String", "depth_position": "String", "depth_team": "String", "elias_id": "String", "first_name": "String", "football_name": "String", "formation": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "jersey_number": "String", "last_name": "String", "position": "String", "season": "Int32", "week": "Int32"}

### load_depth_charts / 2021

{"club_code": "String", "depth_position": "String", "depth_team": "String", "elias_id": "String", "first_name": "String", "football_name": "String", "formation": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "jersey_number": "String", "last_name": "String", "position": "String", "season": "Int32", "week": "Int32"}

### load_depth_charts / 2022

{"club_code": "String", "depth_position": "String", "depth_team": "String", "elias_id": "String", "first_name": "String", "football_name": "String", "formation": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "jersey_number": "String", "last_name": "String", "position": "String", "season": "Int32", "week": "Int32"}

### load_depth_charts / 2023

{"club_code": "String", "depth_position": "String", "depth_team": "String", "elias_id": "String", "first_name": "String", "football_name": "String", "formation": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "jersey_number": "String", "last_name": "String", "position": "String", "season": "Int32", "week": "Int32"}

### load_depth_charts / 2024

{"club_code": "String", "depth_position": "String", "depth_team": "String", "elias_id": "String", "first_name": "String", "football_name": "String", "formation": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "jersey_number": "String", "last_name": "String", "position": "String", "season": "Int32", "week": "Int32"}

### load_depth_charts / 2025

{"dt": "String", "espn_id": "String", "gsis_id": "String", "player_name": "String", "pos_abb": "String", "pos_grp": "String", "pos_grp_id": "String", "pos_id": "String", "pos_name": "String", "pos_rank": "Int32", "pos_slot": "Int32", "team": "String"}

### load_depth_charts / 2026

{"dt": "String", "espn_id": "String", "gsis_id": "String", "player_name": "String", "pos_abb": "String", "pos_grp": "String", "pos_grp_id": "String", "pos_id": "String", "pos_name": "String", "pos_rank": "Int32", "pos_slot": "Int32", "team": "String"}

### load_injuries / 2019

{"date_modified": "Datetime(time_unit='us', time_zone='UTC')", "first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Float64", "team": "String", "week": "Float64"}

### load_injuries / 2020

{"date_modified": "Datetime(time_unit='us', time_zone='UTC')", "first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Float64", "team": "String", "week": "Float64"}

### load_injuries / 2021

{"date_modified": "Datetime(time_unit='us', time_zone='UTC')", "first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Int32", "team": "String", "week": "Int32"}

### load_injuries / 2022

{"date_modified": "Datetime(time_unit='us', time_zone='UTC')", "first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Int32", "team": "String", "week": "Int32"}

### load_injuries / 2023

{"date_modified": "Datetime(time_unit='us', time_zone='UTC')", "first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Int32", "team": "String", "week": "Int32"}

### load_injuries / 2024

{"date_modified": "Datetime(time_unit='us', time_zone='UTC')", "first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Int32", "team": "String", "week": "Int32"}

### load_injuries / 2025

{"first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Int32", "season_type": "String", "team": "String", "week": "Int32"}

### load_injuries / 2026

{"first_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "last_name": "String", "position": "String", "practice_primary_injury": "String", "practice_secondary_injury": "String", "practice_status": "String", "report_primary_injury": "String", "report_secondary_injury": "String", "report_status": "String", "season": "Int32", "season_type": "String", "team": "String", "week": "Int32"}

### load_player_stats / 1999

{"air_yards_share": "Float64", "attempts": "Int32", "carries": "Int32", "completions": "Int32", "def_2pt_atts": "Int32", "def_2pt_made": "Int32", "def_fg_blocks": "Int32", "def_fumbles": "Int32", "def_fumbles_forced": "Int32", "def_interception_yards": "Int32", "def_interceptions": "Int32", "def_pass_defended": "Int32", "def_pat_blocks": "Int32", "def_punt_blocks": "Int32", "def_qb_hits": "Int32", "def_sack_yards": "Float64", "def_sacks": "Float64", "def_safeties": "Int32", "def_tackle_assists": "Int32", "def_tackles_for_loss": "Int32", "def_tackles_for_loss_yards": "Int32", "def_tackles_solo": "Int32", "def_tackles_with_assist": "Int32", "def_tds": "Int32", "fantasy_points": "Float64", "fantasy_points_ppr": "Float64", "fg_att": "Int32", "fg_blocked": "Int32", "fg_blocked_distance": "Int32", "fg_blocked_list": "String", "fg_long": "Int32", "fg_made": "Int32", "fg_made_0_19": "Int32", "fg_made_20_29": "Int32", "fg_made_30_39": "Int32", "fg_made_40_49": "Int32", "fg_made_50_59": "Int32", "fg_made_60_": "Int32", "fg_made_distance": "Int32", "fg_made_list": "String", "fg_missed": "Int32", "fg_missed_0_19": "Int32", "fg_missed_20_29": "Int32", "fg_missed_30_39": "Int32", "fg_missed_40_49": "Int32", "fg_missed_50_59": "Int32", "fg_missed_60_": "Int32", "fg_missed_distance": "Int32", "fg_missed_list": "String", "fg_pct": "Float64", "fumble_recovery_opp": "Int32", "fumble_recovery_own": "Int32", "fumble_recovery_tds": "Int32", "fumble_recovery_yards_opp": "Int32", "fumble_recovery_yards_own": "Int32", "fumbles_forced_by_opp": "Int32", "fumbles_lost_total": "Int32", "fumbles_not_forced": "Int32", "fumbles_out_of_bounds": "Int32", "fumbles_total": "Int32", "game_id": "String", "gwfg_att": "Int32", "gwfg_blocked": "Int32", "gwfg_distance": "Int32", "gwfg_made": "Int32", "gwfg_missed": "Int32", "headshot_url": "String", "kickoff_return_yards": "Int32", "kickoff_returns": "Int32", "misc_yards": "Int32", "opponent_team": "String", "pacr": "Float64", "passing_10": "Int32", "passing_16": "Int32", "passing_20": "Int32", "passing_2pt_conversions": "Int32", "passing_40": "Int32", "passing_air_yards": "Int32", "passing_cpoe": "Float64", "passing_epa": "Float64", "passing_first_downs": "Int32", "passing_interceptions": "Int32", "passing_tds": "Int32", "passing_yards": "Int32", "passing_yards_after_catch": "Int32", "pat_att": "Int32", "pat_blocked": "Int32", "pat_made": "Int32", "pat_missed": "Int32", "pat_pct": "Float64", "penalties": "Int32", "penalty_yards": "Int32", "player_display_name": "String", "player_id": "String", "player_name": "String", "position": "String", "position_group": "String", "pt_att": "Int32", "pt_blocked": "Int32", "pt_downed": "Int32", "pt_fair_caught": "Int32", "pt_inside_20": "Int32", "pt_long": "Int32", "pt_net_yards": "Int32", "pt_out_of_bounds": "Int32", "pt_return_tds": "Int32", "pt_return_yards": "Int32", "pt_returned": "Int32", "pt_touchback": "Int32", "pt_yards": "Int32", "punt_return_yards": "Int32", "punt_returns": "Int32", "racr": "Float64", "receiving_10": "Int32", "receiving_16": "Int32", "receiving_20": "Int32", "receiving_2pt_conversions": "Int32", "receiving_40": "Int32", "receiving_air_yards": "Int32", "receiving_epa": "Float64", "receiving_first_downs": "Int32", "receiving_fumbles": "Int32", "receiving_fumbles_lost": "Int32", "receiving_tds": "Int32", "receiving_yards": "Int32", "receiving_yards_after_catch": "Int32", "receptions": "Int32", "rushing_10": "Int32", "rushing_12": "Int32", "rushing_20": "Int32", "rushing_2pt_conversions": "Int32", "rushing_40": "Int32", "rushing_epa": "Float64", "rushing_first_downs": "Int32", "rushing_fumbles": "Int32", "rushing_fumbles_lost": "Int32", "rushing_tds": "Int32", "rushing_yards": "Int32", "sack_fumbles": "Int32", "sack_fumbles_lost": "Int32", "sack_yards_lost": "Int32", "sacks_suffered": "Int32", "season": "Int32", "season_type": "String", "special_teams_tds": "Int32", "target_share": "Float64", "targets": "Int32", "team": "String", "week": "Int32", "wopr": "Float64"}

### load_player_stats / 2019

{"air_yards_share": "Float64", "attempts": "Int32", "carries": "Int32", "completions": "Int32", "def_2pt_atts": "Int32", "def_2pt_made": "Int32", "def_fg_blocks": "Int32", "def_fumbles": "Int32", "def_fumbles_forced": "Int32", "def_interception_yards": "Int32", "def_interceptions": "Int32", "def_pass_defended": "Int32", "def_pat_blocks": "Int32", "def_punt_blocks": "Int32", "def_qb_hits": "Int32", "def_sack_yards": "Float64", "def_sacks": "Float64", "def_safeties": "Int32", "def_tackle_assists": "Int32", "def_tackles_for_loss": "Int32", "def_tackles_for_loss_yards": "Int32", "def_tackles_solo": "Int32", "def_tackles_with_assist": "Int32", "def_tds": "Int32", "fantasy_points": "Float64", "fantasy_points_ppr": "Float64", "fg_att": "Int32", "fg_blocked": "Int32", "fg_blocked_distance": "Int32", "fg_blocked_list": "String", "fg_long": "Int32", "fg_made": "Int32", "fg_made_0_19": "Int32", "fg_made_20_29": "Int32", "fg_made_30_39": "Int32", "fg_made_40_49": "Int32", "fg_made_50_59": "Int32", "fg_made_60_": "Int32", "fg_made_distance": "Int32", "fg_made_list": "String", "fg_missed": "Int32", "fg_missed_0_19": "Int32", "fg_missed_20_29": "Int32", "fg_missed_30_39": "Int32", "fg_missed_40_49": "Int32", "fg_missed_50_59": "Int32", "fg_missed_60_": "Int32", "fg_missed_distance": "Int32", "fg_missed_list": "String", "fg_pct": "Float64", "fumble_recovery_opp": "Int32", "fumble_recovery_own": "Int32", "fumble_recovery_tds": "Int32", "fumble_recovery_yards_opp": "Int32", "fumble_recovery_yards_own": "Int32", "fumbles_forced_by_opp": "Int32", "fumbles_lost_total": "Int32", "fumbles_not_forced": "Int32", "fumbles_out_of_bounds": "Int32", "fumbles_total": "Int32", "game_id": "String", "gwfg_att": "Int32", "gwfg_blocked": "Int32", "gwfg_distance": "Int32", "gwfg_made": "Int32", "gwfg_missed": "Int32", "headshot_url": "String", "kickoff_return_yards": "Int32", "kickoff_returns": "Int32", "misc_yards": "Int32", "opponent_team": "String", "pacr": "Float64", "passing_10": "Int32", "passing_16": "Int32", "passing_20": "Int32", "passing_2pt_conversions": "Int32", "passing_40": "Int32", "passing_air_yards": "Int32", "passing_cpoe": "Float64", "passing_epa": "Float64", "passing_first_downs": "Int32", "passing_interceptions": "Int32", "passing_tds": "Int32", "passing_yards": "Int32", "passing_yards_after_catch": "Int32", "pat_att": "Int32", "pat_blocked": "Int32", "pat_made": "Int32", "pat_missed": "Int32", "pat_pct": "Float64", "penalties": "Int32", "penalty_yards": "Int32", "player_display_name": "String", "player_id": "String", "player_name": "String", "position": "String", "position_group": "String", "pt_att": "Int32", "pt_blocked": "Int32", "pt_downed": "Int32", "pt_fair_caught": "Int32", "pt_inside_20": "Int32", "pt_long": "Int32", "pt_net_yards": "Int32", "pt_out_of_bounds": "Int32", "pt_return_tds": "Int32", "pt_return_yards": "Int32", "pt_returned": "Int32", "pt_touchback": "Int32", "pt_yards": "Int32", "punt_return_yards": "Int32", "punt_returns": "Int32", "racr": "Float64", "receiving_10": "Int32", "receiving_16": "Int32", "receiving_20": "Int32", "receiving_2pt_conversions": "Int32", "receiving_40": "Int32", "receiving_air_yards": "Int32", "receiving_epa": "Float64", "receiving_first_downs": "Int32", "receiving_fumbles": "Int32", "receiving_fumbles_lost": "Int32", "receiving_tds": "Int32", "receiving_yards": "Int32", "receiving_yards_after_catch": "Int32", "receptions": "Int32", "rushing_10": "Int32", "rushing_12": "Int32", "rushing_20": "Int32", "rushing_2pt_conversions": "Int32", "rushing_40": "Int32", "rushing_epa": "Float64", "rushing_first_downs": "Int32", "rushing_fumbles": "Int32", "rushing_fumbles_lost": "Int32", "rushing_tds": "Int32", "rushing_yards": "Int32", "sack_fumbles": "Int32", "sack_fumbles_lost": "Int32", "sack_yards_lost": "Int32", "sacks_suffered": "Int32", "season": "Int32", "season_type": "String", "special_teams_tds": "Int32", "target_share": "Float64", "targets": "Int32", "team": "String", "week": "Int32", "wopr": "Float64"}

### load_player_stats / 2024

{"air_yards_share": "Float64", "attempts": "Int32", "carries": "Int32", "completions": "Int32", "def_2pt_atts": "Int32", "def_2pt_made": "Int32", "def_fg_blocks": "Int32", "def_fumbles": "Int32", "def_fumbles_forced": "Int32", "def_interception_yards": "Int32", "def_interceptions": "Int32", "def_pass_defended": "Int32", "def_pat_blocks": "Int32", "def_punt_blocks": "Int32", "def_qb_hits": "Int32", "def_sack_yards": "Float64", "def_sacks": "Float64", "def_safeties": "Int32", "def_tackle_assists": "Int32", "def_tackles_for_loss": "Int32", "def_tackles_for_loss_yards": "Int32", "def_tackles_solo": "Int32", "def_tackles_with_assist": "Int32", "def_tds": "Int32", "fantasy_points": "Float64", "fantasy_points_ppr": "Float64", "fg_att": "Int32", "fg_blocked": "Int32", "fg_blocked_distance": "Int32", "fg_blocked_list": "String", "fg_long": "Int32", "fg_made": "Int32", "fg_made_0_19": "Int32", "fg_made_20_29": "Int32", "fg_made_30_39": "Int32", "fg_made_40_49": "Int32", "fg_made_50_59": "Int32", "fg_made_60_": "Int32", "fg_made_distance": "Int32", "fg_made_list": "String", "fg_missed": "Int32", "fg_missed_0_19": "Int32", "fg_missed_20_29": "Int32", "fg_missed_30_39": "Int32", "fg_missed_40_49": "Int32", "fg_missed_50_59": "Int32", "fg_missed_60_": "Int32", "fg_missed_distance": "Int32", "fg_missed_list": "String", "fg_pct": "Float64", "fumble_recovery_opp": "Int32", "fumble_recovery_own": "Int32", "fumble_recovery_tds": "Int32", "fumble_recovery_yards_opp": "Int32", "fumble_recovery_yards_own": "Int32", "fumbles_forced_by_opp": "Int32", "fumbles_lost_total": "Int32", "fumbles_not_forced": "Int32", "fumbles_out_of_bounds": "Int32", "fumbles_total": "Int32", "game_id": "String", "gwfg_att": "Int32", "gwfg_blocked": "Int32", "gwfg_distance": "Int32", "gwfg_made": "Int32", "gwfg_missed": "Int32", "headshot_url": "String", "kickoff_return_yards": "Int32", "kickoff_returns": "Int32", "misc_yards": "Int32", "opponent_team": "String", "pacr": "Float64", "passing_10": "Int32", "passing_16": "Int32", "passing_20": "Int32", "passing_2pt_conversions": "Int32", "passing_40": "Int32", "passing_air_yards": "Int32", "passing_cpoe": "Float64", "passing_epa": "Float64", "passing_first_downs": "Int32", "passing_interceptions": "Int32", "passing_tds": "Int32", "passing_yards": "Int32", "passing_yards_after_catch": "Int32", "pat_att": "Int32", "pat_blocked": "Int32", "pat_made": "Int32", "pat_missed": "Int32", "pat_pct": "Float64", "penalties": "Int32", "penalty_yards": "Int32", "player_display_name": "String", "player_id": "String", "player_name": "String", "position": "String", "position_group": "String", "pt_att": "Int32", "pt_blocked": "Int32", "pt_downed": "Int32", "pt_fair_caught": "Int32", "pt_inside_20": "Int32", "pt_long": "Int32", "pt_net_yards": "Int32", "pt_out_of_bounds": "Int32", "pt_return_tds": "Int32", "pt_return_yards": "Int32", "pt_returned": "Int32", "pt_touchback": "Int32", "pt_yards": "Int32", "punt_return_yards": "Int32", "punt_returns": "Int32", "racr": "Float64", "receiving_10": "Int32", "receiving_16": "Int32", "receiving_20": "Int32", "receiving_2pt_conversions": "Int32", "receiving_40": "Int32", "receiving_air_yards": "Int32", "receiving_epa": "Float64", "receiving_first_downs": "Int32", "receiving_fumbles": "Int32", "receiving_fumbles_lost": "Int32", "receiving_tds": "Int32", "receiving_yards": "Int32", "receiving_yards_after_catch": "Int32", "receptions": "Int32", "rushing_10": "Int32", "rushing_12": "Int32", "rushing_20": "Int32", "rushing_2pt_conversions": "Int32", "rushing_40": "Int32", "rushing_epa": "Float64", "rushing_first_downs": "Int32", "rushing_fumbles": "Int32", "rushing_fumbles_lost": "Int32", "rushing_tds": "Int32", "rushing_yards": "Int32", "sack_fumbles": "Int32", "sack_fumbles_lost": "Int32", "sack_yards_lost": "Int32", "sacks_suffered": "Int32", "season": "Int32", "season_type": "String", "special_teams_tds": "Int32", "target_share": "Float64", "targets": "Int32", "team": "String", "week": "Int32", "wopr": "Float64"}

### load_player_stats / 2026

{"air_yards_share": "Float64", "attempts": "Int32", "carries": "Int32", "completions": "Int32", "def_2pt_atts": "Int32", "def_2pt_made": "Int32", "def_fg_blocks": "Int32", "def_fumbles": "Int32", "def_fumbles_forced": "Int32", "def_interception_yards": "Int32", "def_interceptions": "Int32", "def_pass_defended": "Int32", "def_pat_blocks": "Int32", "def_punt_blocks": "Int32", "def_qb_hits": "Int32", "def_sack_yards": "Float64", "def_sacks": "Float64", "def_safeties": "Int32", "def_tackle_assists": "Int32", "def_tackles_for_loss": "Int32", "def_tackles_for_loss_yards": "Int32", "def_tackles_solo": "Int32", "def_tackles_with_assist": "Int32", "def_tds": "Int32", "fantasy_points": "Float64", "fantasy_points_ppr": "Float64", "fg_att": "Int32", "fg_blocked": "Int32", "fg_blocked_distance": "Int32", "fg_blocked_list": "String", "fg_long": "Int32", "fg_made": "Int32", "fg_made_0_19": "Int32", "fg_made_20_29": "Int32", "fg_made_30_39": "Int32", "fg_made_40_49": "Int32", "fg_made_50_59": "Int32", "fg_made_60_": "Int32", "fg_made_distance": "Int32", "fg_made_list": "String", "fg_missed": "Int32", "fg_missed_0_19": "Int32", "fg_missed_20_29": "Int32", "fg_missed_30_39": "Int32", "fg_missed_40_49": "Int32", "fg_missed_50_59": "Int32", "fg_missed_60_": "Int32", "fg_missed_distance": "Int32", "fg_missed_list": "String", "fg_pct": "Float64", "fumble_recovery_opp": "Int32", "fumble_recovery_own": "Int32", "fumble_recovery_tds": "Int32", "fumble_recovery_yards_opp": "Int32", "fumble_recovery_yards_own": "Int32", "fumbles_forced_by_opp": "Int32", "fumbles_lost_total": "Int32", "fumbles_not_forced": "Int32", "fumbles_out_of_bounds": "Int32", "fumbles_total": "Int32", "game_id": "String", "gwfg_att": "Int32", "gwfg_blocked": "Int32", "gwfg_distance": "Int32", "gwfg_made": "Int32", "gwfg_missed": "Int32", "headshot_url": "String", "kickoff_return_yards": "Int32", "kickoff_returns": "Int32", "misc_yards": "Int32", "opponent_team": "String", "pacr": "Float64", "passing_10": "Int32", "passing_16": "Int32", "passing_20": "Int32", "passing_2pt_conversions": "Int32", "passing_40": "Int32", "passing_air_yards": "Int32", "passing_cpoe": "Float64", "passing_epa": "Float64", "passing_first_downs": "Int32", "passing_interceptions": "Int32", "passing_tds": "Int32", "passing_yards": "Int32", "passing_yards_after_catch": "Int32", "pat_att": "Int32", "pat_blocked": "Int32", "pat_made": "Int32", "pat_missed": "Int32", "pat_pct": "Float64", "penalties": "Int32", "penalty_yards": "Int32", "player_display_name": "String", "player_id": "String", "player_name": "String", "position": "String", "position_group": "String", "pt_att": "Int32", "pt_blocked": "Int32", "pt_downed": "Int32", "pt_fair_caught": "Int32", "pt_inside_20": "Int32", "pt_long": "Int32", "pt_net_yards": "Int32", "pt_out_of_bounds": "Int32", "pt_return_tds": "Int32", "pt_return_yards": "Int32", "pt_returned": "Int32", "pt_touchback": "Int32", "pt_yards": "Int32", "punt_return_yards": "Int32", "punt_returns": "Int32", "racr": "Float64", "receiving_10": "Int32", "receiving_16": "Int32", "receiving_20": "Int32", "receiving_2pt_conversions": "Int32", "receiving_40": "Int32", "receiving_air_yards": "Int32", "receiving_epa": "Float64", "receiving_first_downs": "Int32", "receiving_fumbles": "Int32", "receiving_fumbles_lost": "Int32", "receiving_tds": "Int32", "receiving_yards": "Int32", "receiving_yards_after_catch": "Int32", "receptions": "Int32", "rushing_10": "Int32", "rushing_12": "Int32", "rushing_20": "Int32", "rushing_2pt_conversions": "Int32", "rushing_40": "Int32", "rushing_epa": "Float64", "rushing_first_downs": "Int32", "rushing_fumbles": "Int32", "rushing_fumbles_lost": "Int32", "rushing_tds": "Int32", "rushing_yards": "Int32", "sack_fumbles": "Int32", "sack_fumbles_lost": "Int32", "sack_yards_lost": "Int32", "sacks_suffered": "Int32", "season": "Int32", "season_type": "String", "special_teams_tds": "Int32", "target_share": "Float64", "targets": "Int32", "team": "String", "week": "Int32", "wopr": "Float64"}

### load_rosters_weekly / 2019

{"birth_date": "Date", "college": "String", "depth_chart_position": "String", "draft_club": "String", "draft_number": "Int32", "entry_year": "Int32", "esb_id": "String", "espn_id": "String", "fantasy_data_id": "String", "first_name": "String", "football_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "gsis_it_id": "String", "headshot_url": "String", "height": "Float64", "jersey_number": "Int32", "last_name": "String", "ngs_position": "String", "pff_id": "String", "pfr_id": "String", "position": "String", "rookie_year": "Int32", "rotowire_id": "String", "season": "Int32", "sleeper_id": "String", "smart_id": "String", "sportradar_id": "String", "status": "String", "status_description_abbr": "String", "team": "String", "week": "Int32", "weight": "Int32", "yahoo_id": "String", "years_exp": "Int32"}

### load_rosters_weekly / 2026

{"birth_date": "Date", "college": "String", "depth_chart_position": "String", "draft_club": "String", "draft_number": "Int32", "entry_year": "Int32", "esb_id": "String", "espn_id": "String", "fantasy_data_id": "String", "first_name": "String", "football_name": "String", "full_name": "String", "game_type": "String", "gsis_id": "String", "gsis_it_id": "String", "headshot_url": "String", "height": "Int32", "jersey_number": "Int32", "last_name": "String", "ngs_position": "String", "pff_id": "String", "pfr_id": "String", "position": "String", "rookie_year": "Int32", "rotowire_id": "String", "season": "Int32", "sleeper_id": "String", "smart_id": "String", "sportradar_id": "String", "status": "String", "status_description_abbr": "String", "team": "String", "week": "Int32", "weight": "Int32", "yahoo_id": "String", "years_exp": "Int32"}

### load_snap_counts / 2012

{"defense_pct": "Float64", "defense_snaps": "Float64", "game_id": "String", "game_type": "String", "offense_pct": "Float64", "offense_snaps": "Float64", "opponent": "String", "pfr_game_id": "String", "pfr_player_id": "String", "player": "String", "position": "String", "season": "Int32", "st_pct": "Float64", "st_snaps": "Float64", "team": "String", "week": "Int32"}

### load_snap_counts / 2019

{"defense_pct": "Float64", "defense_snaps": "Float64", "game_id": "String", "game_type": "String", "offense_pct": "Float64", "offense_snaps": "Float64", "opponent": "String", "pfr_game_id": "String", "pfr_player_id": "String", "player": "String", "position": "String", "season": "Int32", "st_pct": "Float64", "st_snaps": "Float64", "team": "String", "week": "Int32"}

### load_snap_counts / 2026

{"defense_pct": "Float64", "defense_snaps": "Float64", "game_id": "String", "game_type": "String", "offense_pct": "Float64", "offense_snaps": "Float64", "opponent": "String", "pfr_game_id": "String", "pfr_player_id": "String", "player": "String", "position": "String", "season": "Int32", "st_pct": "Float64", "st_snaps": "Float64", "team": "String", "week": "Int32"}

## Temporal integrity and prospective capture

Source event/update times (`date_modified`, `dt`), original publication time (unknown), actual capture time, local receipt time, forecast cutoff and kickoff remain distinct. Naive/date-only source times are retained verbatim but are not assigned an invented timezone. `dt` and `date_modified` never prove original public availability. Historic source-timestamped rows remain historical; actual participation/stats/snaps are retrospective performance, not pregame starter evidence.

Actual collector observations: **5**; linked upcoming games: **151**; diagnostic linked rows: **21932**. Evidence classes within those game/observation links: `{"unknown": 67, "verified_prospective": 21865}`. Rows may link to multiple future games and observations; these are not independent games or unique reports.

Verified prospective means the source contents were directly captured and locally preserved before the diagnostic cutoff and kickoff, with identified player/team and no future source timestamp. It verifies possession of that evidence, not truth of a listed starter or availability. Week-bearing sources match season/week/team and REG. Timestamped charts use the latest whole team chart inside each observation; absent week/effective-date proof remains a relevance/staleness limitation. Historical source audits are never automatically imported into the prospective store.

## Quarterback and injury interpretation

Rank 1 means listed QB1, never confirmed starter. All backups and missing ranks are retained. Equal-scope multiple QB1 identities and missing IDs/ranks are uncertain. No actual participation is used to choose a starter. GSIS keys are matched exactly; ESPN/PFR bridging requires unique roster mappings. Name similarity is never used. Roster-pair match rates above measure exact player/team overlap across the sampled season, not labeled identity accuracy or pregame roster membership. Week-specific reconciliation and transfers can remain unresolved.

Questionable, Doubtful, Out and null statuses stay distinct, with original practice, primary/secondary injury and roster status fields. Missing status is not healthy, active or absent. Rosters are not injury reports. A source may have no current-week report; no missing source rows are synthesized. Revisions are distinct immutable source observations, and earlier statuses remain queryable.

Current ambiguous QB examples (if observed):

| game_id | team | player_id | rank | role | uncertain |
| --- | --- | --- | --- | --- | --- |
| 2026_09_JAX_BAL | BAL | 00-0034796 | nan | listed_backup_or_unknown | True |
| 2026_09_JAX_BAL | BAL | 00-0035993 | nan | listed_backup_or_unknown | True |
| 2026_09_JAX_BAL | BAL | 00-0040981 | nan | listed_backup_or_unknown | True |

## Suitability and limitations

The observed sources do not establish a meaningful verified historical pregame QB/injury experiment. Historical timestamps lack independently verified original publication/capture evidence; current captures cannot be backdated to old games. Continue evidence collection for future M9.2 assessment; no modeling decision or adjustment is implemented. Missing IDs, changing schemas, delayed/stale charts, absent current injury weeks and source revisions limit even prospective use.

Actual exact-ID cross-check against checksum-verified existing M6 compact QB performance (no PBP reads/rebuild): {"m6_cached_qb_ids": 894, "depth_qb_ids": 218, "matched_ids": 170, "unmatched_ids": 48}. This is career/sample identity overlap, not current availability or starter accuracy. Performance is retrospective; only prior eligible games could support future historical-statistics work, and no strength formula is used here.

## Operation and verification

`python -m nfl_predictor.cli collect-personnel` captures the five available current-season sources using bounded explicit nflreadpy calls, preserving lossless Polars Parquet plus SHA-256 receipts under data/m91. It does not refresh football schedules, train models, issue predictions or touch old ledgers. Partial failures are appended separately; previous snapshots survive. Exact observation reprocessing is idempotent; a later capture of unchanged bytes is a new observation with its own real timestamp.

`python -m nfl_predictor.cli report-m91` is offline and reads source audits/captures plus cached schedules. `as_of(directory, game, cutoff)` is read-only and requires capture AND local receipt by the nonfuture pregame cutoff; late imports cannot establish earlier availability. Source hashes and metadata are checked on every read. Source publication is left null rather than invented.

Detailed schemas and per-week counts: reports/m91/schemas_and_weekly_counts.json; coverage: reports/m91/coverage.csv. Raw datasets remain gitignored.

Windows / Python 3.12 acceptance: `python -m pytest -q tests/test_m91.py`; `python -m nfl_predictor.cli collect-personnel`; `python -m nfl_predictor.cli report-m91`. No native Windows verification is claimed. Test results and preservation measurements follow after execution.

## Measured execution evidence

Baseline commit: `c7f9e1b58c86b262be90242654d3eaf36823bb8b`, clean M8.3 starting tree. Collection confirmed **199 baseline tests**. Relevant existing M6/M8.3 checks: **27 passed, one existing warning in 21.99s**. New focused checks: **11 passed in 1.92s**, no warnings. The focused suite covers exact identity bridges/conflicts, QB ordering/ambiguity, null status preservation, source-clock parsing, evidence classes, duplicate/revised snapshots, future rejection, late-receipt cutoff exclusion, object integrity, partial source failures and prior-ledger preservation.

The real `collect-personnel` command succeeded for all five current-season sources; no source failure was reported. These are actual capture/local-receipt timestamps and source hashes, not historical reconstructed claims:

| source | season | rows | captured_at | created_at | sha256 |
| --- | --- | --- | --- | --- | --- |
| load_rosters_weekly | 2026 | 19865 | 2026-11-05T00:31:07.431368+00:00 | 2026-11-05T00:31:07.431424+00:00 | 967abc84d1d84c2aa00a1fce0b494132b18ff2ae3a2280f43dd42e4edd212e8f |
| load_injuries | 2026 | 2487 | 2026-11-05T00:31:06.355045+00:00 | 2026-11-05T00:31:06.355110+00:00 | d06750ae17ad7959c1d8638f595ed99751863ac93c60a6ffe95ba19c94ed2654 |
| load_player_stats | 2026 | 8428 | 2026-11-05T00:31:07.758414+00:00 | 2026-11-05T00:31:07.758467+00:00 | 9147f97cd5ef884562974e8ebc3cb7bbf2b3cf11d70076665865344b6eedbfec |
| load_depth_charts | 2026 | 745124 | 2026-11-05T00:31:06.817230+00:00 | 2026-11-05T00:31:06.817280+00:00 | 81681238233d0fdfa0fce4aeefd53e3ba707fb89462e4b3180b5dfc7f48e0f54 |
| load_snap_counts | 2026 | 11292 | 2026-11-05T00:31:08.176838+00:00 | 2026-11-05T00:31:08.177030+00:00 | dde95ac13f10601d00c09a4a148f1c6bd17ee9924c76dccd0e52e34f8b35ed25 |

The additive store retains distinctions that M6’s fixed availability/status schema cannot losslessly represent (Doubtful versus Out, practice reports, chart ranks, missing publication time and whole multi-game source snapshots). M6 ledgers and feature gates remain unchanged; no M9.1 record is imported into existing models.

Pre/post SHA-256 snapshot currently confirms **2612 protected existing files unchanged**, including models, M6 compact history, M7 genuine forecasts, official SQLite, M8 odds/wagers, M8.3 records and historical benchmark reports. Manifest SHA-256: `be76cfe2cdf6134a2a7b87684d507e14cc69d850b1bf845a6dc0885cb5e38f89`.


Full regression suite executed once: **210 passed, 8 warnings in 165.32s (0:02:45)**. Eight existing warnings concern Streamlit/pandas deprecations and the synthetic play-count coverage fixture. Final SHA-256 verification again confirmed all **2,612 protected files unchanged**; `git diff --check` passed. Native Windows testing remains unexecuted.

Delivered and verified: five-source API/schema audit, 2019–2026 injury/depth coverage measurements, exact identifier reconciliation and M6 identity cross-check, real immutable current captures, cutoff querying, revision/failure handling, focused/full offline tests and this report. Original public availability of historical records remains unverified; that limitation prevents a confirmed historical pregame QB/injury experiment and is not treated as a successful modeling dataset. M9.2/M9.3 are not implemented.
