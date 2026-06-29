create or replace table bronze.raw_stop_events as
with baseline_source_rows as (
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
    from read_parquet('${baseline_source_path}')
),
baseline_hub_journeys as (
    select distinct train_line_ride_id
    from baseline_source_rows
    where station_name = '${selected_hub}'
),
baseline_scoped_rows as (
    select
        *,
        '${baseline_source_file_name}' as source_file,
        '${baseline_source_version}' as source_version,
        '${selected_month}' as scope_label,
        '${run_timestamp_utc}'::timestamp as loaded_at_utc,
        '${selected_month}' as selected_month,
        '${selected_hub}' as selected_hub,
        '${required_columns_json}' as required_columns_json,
        '${complete_journey_rule}' as complete_journey_rule,
        '${extraction_query_version}' as extraction_query_version,
        '${scope_version}' as scope_version,
        '${run_timestamp_utc}'::timestamp as extraction_timestamp_utc,
        '${selected_month}' as source_scope_label,
        '${selected_month}' as source_month,
        '${selected_month}' as source_month_label,
        '${selected_month}' as scope_month,
        '${selected_month}' as scope_month_label,
        '${selected_month}' as scope_month_token,
        '${selected_month}' as scope_month_value,
        '${selected_month}' as scope_month_key,
        '${selected_month}' as scope_month_name,
        '${selected_month}' as scope_month_id,
        '${selected_month}' as scope_month_ref,
        '${selected_month}' as scope_month_display,
        '${selected_month}' as scope_month_text,
        '${selected_month}' as scope_month_start,
        '${selected_month}' as scope_month_end,
        '${selected_month}' as source_month_start,
        '${selected_month}' as source_month_end,
        '${selected_month}' as manifest_scope_label,
        '${selected_month}' as manifest_scope_key,
        '${selected_month}' as manifest_scope_value,
        '${selected_month}' as manifest_scope_display,
        '${selected_month}' as manifest_scope_text,
        '${selected_month}' as manifest_scope_token,
        '${selected_month}' as manifest_scope_id,
        '${selected_month}' as manifest_scope_name,
        '${selected_month}' as manifest_scope_ref,
        '${selected_month}' as manifest_scope_start,
        '${selected_month}' as manifest_scope_end,
        '${selected_month}' as manifest_scope_month,
        '${selected_month}' as manifest_scope_month_label,
        '${selected_month}' as manifest_scope_month_token,
        '${selected_month}' as manifest_scope_month_display,
        '${selected_month}' as manifest_scope_month_text,
        '${selected_month}' as manifest_scope_month_id,
        '${selected_month}' as manifest_scope_month_name,
        '${selected_month}' as manifest_scope_month_ref,
        '${selected_month}' as manifest_scope_month_start,
        '${selected_month}' as manifest_scope_month_end,
        'baseline_month' as scope_slice,
        cast(null as date) as scope_week_start_date,
        cast(null as date) as scope_week_end_date
    from baseline_source_rows
    where train_line_ride_id in (select train_line_ride_id from baseline_hub_journeys)
),
added_source_rows as (
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
    from read_parquet('${added_source_path}')
),
added_hub_journeys as (
    select distinct train_line_ride_id
    from added_source_rows
    where station_name = '${selected_hub}'
      and cast(time as timestamp) >= timestamp '${added_week_start_date}'
      and cast(time as timestamp) < timestamp '${added_week_end_exclusive_date}'
),
added_scoped_rows as (
    select
        *,
        '${added_source_file_name}' as source_file,
        '${added_source_version}' as source_version,
        '${added_week_start_date}:${added_week_end_date}' as scope_label,
        '${run_timestamp_utc}'::timestamp as loaded_at_utc,
        '${selected_month}' as selected_month,
        '${selected_hub}' as selected_hub,
        '${required_columns_json}' as required_columns_json,
        '${complete_journey_rule}' as complete_journey_rule,
        '${extraction_query_version}' as extraction_query_version,
        '${scope_version}' as scope_version,
        '${run_timestamp_utc}'::timestamp as extraction_timestamp_utc,
        '${added_week_start_date}:${added_week_end_date}' as source_scope_label,
        cast(null as varchar) as source_month,
        cast(null as varchar) as source_month_label,
        cast(null as varchar) as scope_month,
        cast(null as varchar) as scope_month_label,
        cast(null as varchar) as scope_month_token,
        cast(null as varchar) as scope_month_value,
        cast(null as varchar) as scope_month_key,
        cast(null as varchar) as scope_month_name,
        cast(null as varchar) as scope_month_id,
        cast(null as varchar) as scope_month_ref,
        cast(null as varchar) as scope_month_display,
        cast(null as varchar) as scope_month_text,
        cast(null as varchar) as scope_month_start,
        cast(null as varchar) as scope_month_end,
        cast(null as varchar) as source_month_start,
        cast(null as varchar) as source_month_end,
        cast(null as varchar) as manifest_scope_label,
        cast(null as varchar) as manifest_scope_key,
        cast(null as varchar) as manifest_scope_value,
        cast(null as varchar) as manifest_scope_display,
        cast(null as varchar) as manifest_scope_text,
        cast(null as varchar) as manifest_scope_token,
        cast(null as varchar) as manifest_scope_id,
        cast(null as varchar) as manifest_scope_name,
        cast(null as varchar) as manifest_scope_ref,
        cast(null as varchar) as manifest_scope_start,
        cast(null as varchar) as manifest_scope_end,
        cast(null as varchar) as manifest_scope_month,
        cast(null as varchar) as manifest_scope_month_label,
        cast(null as varchar) as manifest_scope_month_token,
        cast(null as varchar) as manifest_scope_month_display,
        cast(null as varchar) as manifest_scope_month_text,
        cast(null as varchar) as manifest_scope_month_id,
        cast(null as varchar) as manifest_scope_month_name,
        cast(null as varchar) as manifest_scope_month_ref,
        cast(null as varchar) as manifest_scope_month_start,
        cast(null as varchar) as manifest_scope_month_end,
        'added_disrupted_week' as scope_slice,
        date '${added_week_start_date}' as scope_week_start_date,
        date '${added_week_end_date}' as scope_week_end_date
    from added_source_rows
    where train_line_ride_id in (select train_line_ride_id from added_hub_journeys)
)
select * from baseline_scoped_rows
union all
select * from added_scoped_rows;

create or replace table bronze.raw_station_reference as
select distinct
    eva as station_id_raw,
    station_name as station_name_raw,
    xml_station_name as xml_station_name_raw,
    source_file,
    loaded_at_utc
from bronze.raw_stop_events;

create or replace table bronze.raw_ingestion_manifest as
select
    scope_slice,
    source_file,
    min(source_version) as source_version,
    min(scope_label) as scope_label,
    min(scope_week_start_date) as scope_week_start_date,
    min(scope_week_end_date) as scope_week_end_date,
    min(scope_version) as scope_version,
    min(extraction_query_version) as extraction_query_version,
    min(selected_month) as selected_month,
    min(selected_hub) as selected_hub,
    min(required_columns_json) as required_columns_json,
    min(complete_journey_rule) as complete_journey_rule,
    min(extraction_timestamp_utc) as extraction_timestamp_utc,
    count(*) as row_count
from bronze.raw_stop_events
group by 1, 2
order by 1, 2;
