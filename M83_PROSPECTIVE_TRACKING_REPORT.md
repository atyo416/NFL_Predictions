# M8.3 prospective forecast tracking

Default on-time cohort: 25–24 hours before scheduled kickoff (60-minute early tolerance). Late issuance requires --late and stays separate. UTC throughout; actual wall clock controls issuance. Changed kickoff creates a distinct slot; old forecasts remain immutable and are excluded from current-schedule comparisons. Older M7 forecasts retain their original cohort.

Existing M7 forecasts: 151. New checkpoint forecasts: 0; graded: 0; pending: 0; ties: 0. No newly graded games.

Market observations: 0; timestamp-compatible matches: 0. Capture/import, quote and snapshot must precede the feature cutoff; historical imports cannot establish earlier availability.

## Model performance

No eligible graded binary observations; accuracy, Brier and log loss are unavailable. No results or profitability are inferred.

No three-model matched graded sample for paired comparisons.

Calibration requires at least 100 binary games per cohort; smaller samples are withheld. Three-way comparisons require identical games and cohort; repeated forecasts are not independent. No selection or promotion occurs.

## Operational snapshot

```json
{
  "forecasts": 0,
  "graded": 0,
  "pending": 0,
  "ties": 0,
  "schedule_change_exclusions": 0,
  "metrics": [],
  "calibration": [],
  "paired": [],
  "checkpoints": [
    {
      "game_id": "2026_09_JAX_BAL",
      "kickoff": "2026-11-06T01:15:00+00:00",
      "target_checkpoint": "2026-11-05T01:15:00+00:00",
      "state": "on_time",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_CIN_ATL",
      "kickoff": "2026-11-08T14:30:00+00:00",
      "target_checkpoint": "2026-11-07T14:30:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_CLE_NO",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_DAL_IND",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_DEN_CAR",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_DET_MIA",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_LA_WAS",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_NYG_PHI",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_NYJ_KC",
      "kickoff": "2026-11-08T18:00:00+00:00",
      "target_checkpoint": "2026-11-07T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_HOU_LAC",
      "kickoff": "2026-11-08T21:05:00+00:00",
      "target_checkpoint": "2026-11-07T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_LV_SF",
      "kickoff": "2026-11-08T21:05:00+00:00",
      "target_checkpoint": "2026-11-07T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_ARI_SEA",
      "kickoff": "2026-11-08T21:25:00+00:00",
      "target_checkpoint": "2026-11-07T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_GB_NE",
      "kickoff": "2026-11-08T21:25:00+00:00",
      "target_checkpoint": "2026-11-07T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_TB_CHI",
      "kickoff": "2026-11-09T01:20:00+00:00",
      "target_checkpoint": "2026-11-08T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_09_BUF_MIN",
      "kickoff": "2026-11-10T01:15:00+00:00",
      "target_checkpoint": "2026-11-09T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_WAS_NYG",
      "kickoff": "2026-11-13T01:15:00+00:00",
      "target_checkpoint": "2026-11-12T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_NE_DET",
      "kickoff": "2026-11-15T14:30:00+00:00",
      "target_checkpoint": "2026-11-14T14:30:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_BUF_NYJ",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_CAR_NO",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_HOU_CLE",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_JAX_TEN",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_KC_ATL",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_MIA_IND",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_MIN_GB",
      "kickoff": "2026-11-15T18:00:00+00:00",
      "target_checkpoint": "2026-11-14T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_LA_ARI",
      "kickoff": "2026-11-15T21:05:00+00:00",
      "target_checkpoint": "2026-11-14T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_SEA_LV",
      "kickoff": "2026-11-15T21:05:00+00:00",
      "target_checkpoint": "2026-11-14T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_SF_DAL",
      "kickoff": "2026-11-15T21:25:00+00:00",
      "target_checkpoint": "2026-11-14T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_PIT_CIN",
      "kickoff": "2026-11-16T01:20:00+00:00",
      "target_checkpoint": "2026-11-15T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_10_LAC_BAL",
      "kickoff": "2026-11-17T01:15:00+00:00",
      "target_checkpoint": "2026-11-16T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_IND_HOU",
      "kickoff": "2026-11-20T01:15:00+00:00",
      "target_checkpoint": "2026-11-19T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_ARI_KC",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_BAL_CAR",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_JAX_NYG",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_MIA_BUF",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_NO_CHI",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_TB_DET",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_TEN_DAL",
      "kickoff": "2026-11-22T18:00:00+00:00",
      "target_checkpoint": "2026-11-21T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_NYJ_LAC",
      "kickoff": "2026-11-22T21:05:00+00:00",
      "target_checkpoint": "2026-11-21T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_LV_DEN",
      "kickoff": "2026-11-22T21:25:00+00:00",
      "target_checkpoint": "2026-11-21T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_PIT_PHI",
      "kickoff": "2026-11-22T21:25:00+00:00",
      "target_checkpoint": "2026-11-21T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_MIN_SF",
      "kickoff": "2026-11-23T01:20:00+00:00",
      "target_checkpoint": "2026-11-22T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_11_CIN_WAS",
      "kickoff": "2026-11-24T01:15:00+00:00",
      "target_checkpoint": "2026-11-23T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_GB_LA",
      "kickoff": "2026-11-26T01:00:00+00:00",
      "target_checkpoint": "2026-11-25T01:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_CHI_DET",
      "kickoff": "2026-11-26T18:00:00+00:00",
      "target_checkpoint": "2026-11-25T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_PHI_DAL",
      "kickoff": "2026-11-26T21:30:00+00:00",
      "target_checkpoint": "2026-11-25T21:30:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_KC_BUF",
      "kickoff": "2026-11-27T01:20:00+00:00",
      "target_checkpoint": "2026-11-26T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_DEN_PIT",
      "kickoff": "2026-11-27T20:00:00+00:00",
      "target_checkpoint": "2026-11-26T20:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_ATL_MIN",
      "kickoff": "2026-11-29T18:00:00+00:00",
      "target_checkpoint": "2026-11-28T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_BAL_HOU",
      "kickoff": "2026-11-29T18:00:00+00:00",
      "target_checkpoint": "2026-11-28T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_LV_CLE",
      "kickoff": "2026-11-29T18:00:00+00:00",
      "target_checkpoint": "2026-11-28T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_NO_CIN",
      "kickoff": "2026-11-29T18:00:00+00:00",
      "target_checkpoint": "2026-11-28T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_NYG_IND",
      "kickoff": "2026-11-29T18:00:00+00:00",
      "target_checkpoint": "2026-11-28T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_NYJ_MIA",
      "kickoff": "2026-11-29T18:00:00+00:00",
      "target_checkpoint": "2026-11-28T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_TEN_JAX",
      "kickoff": "2026-11-29T21:05:00+00:00",
      "target_checkpoint": "2026-11-28T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_SEA_SF",
      "kickoff": "2026-11-29T21:25:00+00:00",
      "target_checkpoint": "2026-11-28T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_WAS_ARI",
      "kickoff": "2026-11-29T21:25:00+00:00",
      "target_checkpoint": "2026-11-28T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_NE_LAC",
      "kickoff": "2026-11-30T01:20:00+00:00",
      "target_checkpoint": "2026-11-29T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_12_CAR_TB",
      "kickoff": "2026-12-01T01:15:00+00:00",
      "target_checkpoint": "2026-11-30T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_KC_LA",
      "kickoff": "2026-12-04T01:15:00+00:00",
      "target_checkpoint": "2026-12-03T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_CIN_CLE",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_DET_ATL",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_GB_NO",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_JAX_CHI",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_LAC_TB",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_SF_NYG",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_WAS_TEN",
      "kickoff": "2026-12-06T18:00:00+00:00",
      "target_checkpoint": "2026-12-05T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_MIA_DEN",
      "kickoff": "2026-12-06T21:05:00+00:00",
      "target_checkpoint": "2026-12-05T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_PHI_ARI",
      "kickoff": "2026-12-06T21:05:00+00:00",
      "target_checkpoint": "2026-12-05T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_BUF_NE",
      "kickoff": "2026-12-06T21:25:00+00:00",
      "target_checkpoint": "2026-12-05T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_CAR_MIN",
      "kickoff": "2026-12-06T21:25:00+00:00",
      "target_checkpoint": "2026-12-05T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_HOU_PIT",
      "kickoff": "2026-12-07T01:20:00+00:00",
      "target_checkpoint": "2026-12-06T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_13_DAL_SEA",
      "kickoff": "2026-12-08T01:15:00+00:00",
      "target_checkpoint": "2026-12-07T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_MIN_NE",
      "kickoff": "2026-12-11T01:15:00+00:00",
      "target_checkpoint": "2026-12-10T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_ATL_CLE",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_CHI_MIA",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_DEN_NYJ",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_HOU_WAS",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_IND_PHI",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_NO_CAR",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_TB_BAL",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_TEN_DET",
      "kickoff": "2026-12-13T18:00:00+00:00",
      "target_checkpoint": "2026-12-12T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_LAC_LV",
      "kickoff": "2026-12-13T21:05:00+00:00",
      "target_checkpoint": "2026-12-12T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_KC_CIN",
      "kickoff": "2026-12-13T21:25:00+00:00",
      "target_checkpoint": "2026-12-12T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_LA_SF",
      "kickoff": "2026-12-13T21:25:00+00:00",
      "target_checkpoint": "2026-12-12T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_NYG_SEA",
      "kickoff": "2026-12-13T21:25:00+00:00",
      "target_checkpoint": "2026-12-12T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_BUF_GB",
      "kickoff": "2026-12-14T01:20:00+00:00",
      "target_checkpoint": "2026-12-13T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_14_PIT_JAX",
      "kickoff": "2026-12-15T01:15:00+00:00",
      "target_checkpoint": "2026-12-14T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_SF_LAC",
      "kickoff": "2026-12-18T01:15:00+00:00",
      "target_checkpoint": "2026-12-17T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_SEA_PHI",
      "kickoff": "2026-12-19T22:00:00+00:00",
      "target_checkpoint": "2026-12-18T22:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_CHI_BUF",
      "kickoff": "2026-12-20T01:20:00+00:00",
      "target_checkpoint": "2026-12-19T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_ATL_WAS",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_BAL_PIT",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_CIN_CAR",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_CLE_NYG",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_IND_TEN",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_JAX_HOU",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_MIA_GB",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_NO_TB",
      "kickoff": "2026-12-20T18:00:00+00:00",
      "target_checkpoint": "2026-12-19T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_NYJ_ARI",
      "kickoff": "2026-12-20T21:05:00+00:00",
      "target_checkpoint": "2026-12-19T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_DAL_LA",
      "kickoff": "2026-12-20T21:25:00+00:00",
      "target_checkpoint": "2026-12-19T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_DEN_LV",
      "kickoff": "2026-12-20T21:25:00+00:00",
      "target_checkpoint": "2026-12-19T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_DET_MIN",
      "kickoff": "2026-12-21T01:20:00+00:00",
      "target_checkpoint": "2026-12-20T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_15_NE_KC",
      "kickoff": "2026-12-22T01:15:00+00:00",
      "target_checkpoint": "2026-12-21T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_HOU_PHI",
      "kickoff": "2026-12-25T01:15:00+00:00",
      "target_checkpoint": "2026-12-24T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_GB_CHI",
      "kickoff": "2026-12-25T18:00:00+00:00",
      "target_checkpoint": "2026-12-24T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_BUF_DEN",
      "kickoff": "2026-12-25T21:30:00+00:00",
      "target_checkpoint": "2026-12-24T21:30:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_LA_SEA",
      "kickoff": "2026-12-26T01:15:00+00:00",
      "target_checkpoint": "2026-12-25T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_ARI_NO",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_CAR_PIT",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_CIN_IND",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_CLE_BAL",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_LAC_MIA",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_NE_NYJ",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_TB_ATL",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_WAS_MIN",
      "kickoff": "2026-12-27T18:00:00+00:00",
      "target_checkpoint": "2026-12-26T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_TEN_LV",
      "kickoff": "2026-12-27T21:05:00+00:00",
      "target_checkpoint": "2026-12-26T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_SF_KC",
      "kickoff": "2026-12-27T21:25:00+00:00",
      "target_checkpoint": "2026-12-26T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_JAX_DAL",
      "kickoff": "2026-12-28T01:20:00+00:00",
      "target_checkpoint": "2026-12-27T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_16_NYG_DET",
      "kickoff": "2026-12-29T01:15:00+00:00",
      "target_checkpoint": "2026-12-28T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_BAL_CIN",
      "kickoff": "2027-01-01T01:15:00+00:00",
      "target_checkpoint": "2026-12-31T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_BUF_MIA",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_DEN_NE",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_IND_CLE",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_KC_LAC",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_LA_TB",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_MIN_NYJ",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_NO_ATL",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_NYG_DAL",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_PIT_TEN",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_SEA_CAR",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_WAS_JAX",
      "kickoff": "2027-01-03T18:00:00+00:00",
      "target_checkpoint": "2027-01-02T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_LV_ARI",
      "kickoff": "2027-01-03T21:05:00+00:00",
      "target_checkpoint": "2027-01-02T21:05:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_DET_CHI",
      "kickoff": "2027-01-03T21:25:00+00:00",
      "target_checkpoint": "2027-01-02T21:25:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_PHI_SF",
      "kickoff": "2027-01-04T01:20:00+00:00",
      "target_checkpoint": "2027-01-03T01:20:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_17_HOU_GB",
      "kickoff": "2027-01-05T01:15:00+00:00",
      "target_checkpoint": "2027-01-04T01:15:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_ATL_CAR",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_CHI_MIN",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_CLE_CIN",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_DAL_WAS",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_DET_GB",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_JAX_IND",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_LAC_DEN",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_LV_KC",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_MIA_NE",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_NYJ_BUF",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_PHI_NYG",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_PIT_BAL",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_SEA_LA",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_SF_ARI",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_TB_NO",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    },
    {
      "game_id": "2026_18_TEN_HOU",
      "kickoff": "2027-01-10T18:00:00+00:00",
      "target_checkpoint": "2027-01-09T18:00:00+00:00",
      "state": "upcoming",
      "issued_cohorts": "",
      "schedule_changed": false
    }
  ],
  "actions": [],
  "issues": [
    "Football cache is older than 24h; refresh with update before issuing"
  ],
  "market_quotes": 0,
  "timestamp_matches": 0,
  "latest_successful_run": "2026-11-05T00:18:27.422778+00:00",
  "previous_m7_forecasts": 151,
  "data_retrieval": "2026-11-03T04:35:08.725216+00:00",
  "observed_at": "2026-11-05T00:18:29.718111+00:00"
}
```

Refresh first with the existing update command. No scheduler runs. Cache retrieval times establish local observation, not verified original source publication. Historical revisions remain a data-vintage limitation. Missing experimental artifacts are reported without historical substitution; missing odds do not block issuance. Report-only never issues or grades. Dry-run makes no writes, including reports.

Windows / Python 3.12 acceptance: `python -m pytest -q tests/test_m83.py`, then `python -m nfl_predictor.cli weekly-m83 --dry-run`, then `python -m nfl_predictor.cli weekly-m83 --report-only`. Native Windows verification has not been executed.

## Engineering verification and remaining operations

Baseline: `ae5c2fc91e879713d951b0c82752ed9acd617acd`, clean M8.2 branch. Actual starting test collection: **187 tests**. Relevant baseline: **12 passed in 3.24s**. New focused suite: **12 passed in 1.33s**. Real dry-run, weekly operation and report-only commands succeeded using cached data. No new live forecasts were issued because the football cache is stale; new issuance, grading/corrections and matched comparisons were verified with deterministic offline fixtures, not claimed as genuine observations.

Actual prior counts: **151 official SQLite forecasts**, **151 M7 genuinely issued forecasts**; new M8.3 forecasts **0**, graded **0**, market quotes **0**. Refresh football data before using the next checkpoint. Odds collection/import is optional; no configured API key was needed for verification. Model families and calibration/selection/activation remain unchanged.

Before/after SHA-256 verification covers **2383 protected existing files**, including all existing model artifacts (M8.2 included), M7 forecast files, official SQLite, M8 lab and M8.1/M8.2 reports/results. All preserved bytes match. Snapshot SHA-256: `7a4133f579d5445cfeca1ea36a523f77fb2087da7e8120a6700cef92b830051b`. New M8.3 records are separate.

Run the supplied `scripts/windows_m83_acceptance.ps1` locally, inspect the existing Betting Lab expander, and then manually operate near checkpoints after data refresh. No native Windows or live provider certification is claimed; no performance advantage or profitability is claimed. M9 is not started.

Full regression suite executed once: **199 passed, 8 warnings in 159.70s (0:02:39)**. Final post-suite verification again found zero changes across all 2,383 protected files. The eight existing warnings concern Streamlit/pandas deprecations and the synthetic play-count coverage fixture.
