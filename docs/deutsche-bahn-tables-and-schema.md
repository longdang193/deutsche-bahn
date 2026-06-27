# Deutsche Bahn Decision Dashboard Tables And Schema

## Schema Strategy

Use three zones plus serving contracts:

1. Bronze
2. Silver
3. Gold
4. Serving

Power BI should read from serving tables, not Bronze or full Silver facts.

## Scope Artifact

### `config.scope`

Purpose:

- declare project subset before Bronze load

Fields:

| Field | Type | Notes |
|---|---|---|
| `selected_months` | array<string> | scoped months |
| `selected_stations` | array<string> | hub subset |
| `selected_train_types` | array<string> | optional filter |
| `required_columns` | array<string> | extract columns |
| `scope_version` | string | config version |

## Bronze Zone

### `bronze.raw_stop_events`

Purpose:

- preserve scoped stop-level operational records unchanged

Columns:

| Column | Type | Notes |
|---|---|---|
| `source_file` | string | parquet or source artifact name |
| `ingested_at_utc` | timestamp | ingestion audit field |
| `service_date` | date | operating date |
| `station_id_raw` | string | raw station identifier |
| `station_name_raw` | string | raw station name |
| `train_type_raw` | string | ICE / IC / RE / etc. |
| `train_number_raw` | string | train number from source |
| `journey_id_raw` | string | source journey identifier |
| `planned_arrival_ts_raw` | timestamp | source planned arrival |
| `changed_arrival_ts_raw` | timestamp | source changed arrival |
| `planned_departure_ts_raw` | timestamp | source planned departure |
| `changed_departure_ts_raw` | timestamp | source changed departure |
| `arrival_cancelled_raw` | boolean | arrival cancellation flag |
| `departure_cancelled_raw` | boolean | departure cancellation flag |
| `payload_hash` | string | dedupe aid |

### `bronze.raw_station_reference`

| Column | Type | Notes |
|---|---|---|
| `station_id_raw` | string | raw station id |
| `station_name_raw` | string | raw name |
| `latitude_raw` | decimal | source coordinate |
| `longitude_raw` | decimal | source coordinate |
| `ingested_at_utc` | timestamp | audit |

### `bronze.raw_ingestion_manifest`

| Column | Type | Notes |
|---|---|---|
| `source_file` | string | source artifact |
| `source_version` | string | source version |
| `scope_version` | string | scope config version |
| `selected_month` | string | extraction month |
| `selected_stations` | string | serialized station list |
| `selected_train_types` | string | serialized train type list |
| `extraction_timestamp` | timestamp | audit |
| `extraction_query_version` | string | extraction logic version |
| `row_count` | bigint | extracted rows |

## Silver Zone

### `silver.dim_station`

| Column | Type | Notes |
|---|---|---|
| `station_key` | int | surrogate key |
| `station_id` | string | normalized station id |
| `station_name` | string | normalized station name |
| `latitude` | decimal | cleaned coordinate |
| `longitude` | decimal | cleaned coordinate |
| `is_major_station` | boolean | top station flag |
| `region_name` | string | optional regional grouping |

### `silver.dim_train_service`

| Column | Type | Notes |
|---|---|---|
| `train_service_key` | int | surrogate key |
| `train_type` | string | normalized type |
| `train_number` | string | normalized number |
| `service_class` | string | long-distance / regional / other |

### `silver.dim_date`

| Column | Type | Notes |
|---|---|---|
| `date_key` | int | `YYYYMMDD` |
| `calendar_date` | date | date |
| `year` | int | year |
| `month` | int | month |
| `week_of_year` | int | ISO week |
| `day_of_week` | int | 1-7 |
| `day_name` | string | weekday name |
| `is_weekend` | boolean | weekend flag |

### `silver.dim_hour`

| Column | Type | Notes |
|---|---|---|
| `hour_key` | int | `HH` |
| `hour_of_day` | int | hour |
| `time_band` | string | peak / off-peak |

### `silver.fact_stop_event`

Grain:

- one row per train-stop event

Columns:

| Column | Type | Notes |
|---|---|---|
| `stop_event_key` | bigint | surrogate key |
| `service_date` | date | operating date |
| `date_key` | int | join to date |
| `hour_key` | int | join to hour |
| `station_key` | int | join to station |
| `train_service_key` | int | join to service |
| `journey_id` | string | normalized journey id |
| `stop_sequence` | int | optional if derivable |
| `planned_arrival_ts` | timestamp | localized |
| `actual_arrival_ts` | timestamp | localized |
| `planned_departure_ts` | timestamp | localized |
| `actual_departure_ts` | timestamp | localized |
| `arrival_delay_min` | int | derived |
| `departure_delay_min` | int | derived |
| `is_arrival_cancelled` | boolean | normalized |
| `is_departure_cancelled` | boolean | normalized |
| `is_cancellation` | boolean | combined flag |
| `delay_change_min` | int | departure minus arrival delay |

## Gold Zone

### `gold.feature_stop_event`

Grain:

- one row per train-stop event for ML training and scoring

Columns:

| Column | Type | Notes |
|---|---|---|
| `stop_event_key` | bigint | join key |
| `station_key` | int | station |
| `train_service_key` | int | service |
| `service_date` | date | date |
| `hour_of_day` | int | time feature |
| `day_of_week` | int | calendar feature |
| `is_peak_hour` | boolean | peak indicator |
| `arrival_delay_min` | int | current delay |
| `departure_delay_min` | int | current delay |
| `rolling_station_delay_count_30m` | int | congestion proxy |
| `rolling_station_cancel_count_60m` | int | disruption proxy |
| `station_avg_delay_last_7d` | decimal | baseline |
| `train_type_avg_delay_last_30d` | decimal | baseline |
| `delay_change_min` | int | propagation proxy |
| `label_severe_departure_delay_15plus` | boolean | MVP label |

### `gold.fact_station_hour`

Grain:

- one row per station per hour

Columns:

| Column | Type | Notes |
|---|---|---|
| `station_hour_key` | string | composite surrogate |
| `station_key` | int | station |
| `service_date` | date | date |
| `hour_of_day` | int | hour |
| `total_trains` | int | traffic volume |
| `avg_arrival_delay_min` | decimal | aggregate |
| `avg_departure_delay_min` | decimal | aggregate |
| `severe_delay_count` | int | aggregate |
| `cancellation_count` | int | aggregate |
| `rolling_delay_pressure` | decimal | station stress score |

### `gold.fact_ml_prediction`

Grain:

- one row per scored decision object

Columns:

| Column | Type | Notes |
|---|---|---|
| `prediction_id` | string | prediction key |
| `stop_event_key` | bigint | optional stop-level link |
| `station_hour_key` | string | optional station-hour link |
| `predicted_severe_delay_risk` | decimal | main model output |
| `risk_band` | string | low / medium / high |
| `model_version` | string | model artifact version |
| `feature_version` | string | feature contract version |
| `training_period_start` | date | model training start |
| `training_period_end` | date | model training end |
| `prediction_timestamp` | timestamp | scoring timestamp |

### `gold.fact_intervention_candidate`

Grain:

- one row per candidate action for optimization

MVP action family:

- `connection_holding`

Columns:

| Column | Type | Notes |
|---|---|---|
| `candidate_id` | string | candidate key |
| `decision_window_ts` | timestamp | optimization horizon |
| `station_key` | int | target station |
| `train_service_key` | int | outgoing train |
| `journey_id` | string | target journey |
| `incoming_journey_id` | string | feeder journey if applicable |
| `action_family` | string | `connection_holding` |
| `action_code` | string | `depart_normally` / `hold_2_min` / `hold_5_min` |
| `hold_minutes` | int | 0 / 2 / 5 |
| `predicted_severe_delay_risk` | decimal | ML output |
| `expected_saved_minutes` | decimal | business estimate |
| `expected_connection_value` | decimal | proxy benefit |
| `expected_downstream_delay_penalty` | decimal | proxy cost |
| `feasible_flag` | boolean | rule-screened candidate |

### `gold.fact_optimization_result`

Grain:

- one row per candidate after optimization run

Columns:

| Column | Type | Notes |
|---|---|---|
| `optimization_run_id` | string | run identifier |
| `candidate_id` | string | candidate |
| `selected_flag` | boolean | chosen or not |
| `objective_contribution` | decimal | contribution |
| `model_version` | string | optimization logic version |
| `run_created_at_utc` | timestamp | audit |

## Serving Layer

Recommended Power BI tables:

- `dim_station`
- `dim_train_service`
- `dim_date`
- `dim_hour`
- `fact_station_hour`
- `fact_ml_prediction`
- `fact_intervention_candidate`
- `fact_optimization_result`

Keep out of initial Power BI import:

- full `silver.fact_stop_event`

Use detailed stop events only for:

- drill-through
- validation
- small scoped extracts

## Local / Cloud Contract

Use same logical grains and column meanings in:

- DuckDB local prototype
- BigQuery cloud pipeline

Only physical SQL implementation should differ.

## Minimal MVP Tables

1. `silver.dim_station`
2. `silver.dim_train_service`
3. `silver.dim_date`
4. `silver.dim_hour`
5. `silver.fact_stop_event`
6. `gold.feature_stop_event`
7. `gold.fact_station_hour`
8. `gold.fact_ml_prediction`
9. `gold.fact_intervention_candidate`
10. `gold.fact_optimization_result`

## Minimal MVP Label

Use this first:

- `label_severe_departure_delay_15plus`

## Minimal MVP Measures For Power BI

- `% on time`
- `avg departure delay`
- `% severe delay`
- `% cancellations`
- `predicted severe risk`
- `expected saved minutes`
- `selected hold actions`
- `total hold minutes used`
