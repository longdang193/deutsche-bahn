create or replace table bronze.raw_stop_events as
with source_rows as (
    select
        station_name,
        xml_station_name,
        eva,
        train_number,
        line_number,
        final_destination_station,
        delay_in_min,
        time,
        is_canceled,
        train_type,
        train_line_ride_id,
        train_line_station_num,
        arrival_planned_time,
        arrival_change_time,
        departure_planned_time,
        departure_change_time,
        id
    from read_parquet('${source_path}')
),
hub_journeys as (
    select distinct train_line_ride_id
    from source_rows
    where station_name = '${selected_hub}'
),
scoped_rows as (
    select *
    from source_rows
    where train_line_ride_id in (select train_line_ride_id from hub_journeys)
)
select
    *,
    '${source_file_name}' as source_file,
    timestamp '${run_timestamp_utc}' as loaded_at_utc
from scoped_rows;

create or replace table bronze.raw_station_reference as
select distinct
    eva as station_id_raw,
    station_name as station_name_raw,
    xml_station_name as xml_station_name_raw,
    '${source_file_name}' as source_file,
    timestamp '${run_timestamp_utc}' as loaded_at_utc
from bronze.raw_stop_events;

create or replace table bronze.raw_ingestion_manifest as
select
    '${source_file_name}' as source_file,
    '${source_version}' as source_version,
    '${scope_version}' as scope_version,
    '${extraction_query_version}' as extraction_query_version,
    '${selected_month}' as selected_month,
    '${selected_hub}' as selected_hub,
    '${required_columns_json}' as required_columns_json,
    '${complete_journey_rule}' as complete_journey_rule,
    timestamp '${run_timestamp_utc}' as extraction_timestamp_utc,
    count(*) as row_count
from bronze.raw_stop_events;
