create or replace table silver.dim_station as
select
    row_number() over (order by station_id, station_name, xml_station_name) as station_key,
    station_id,
    station_name,
    xml_station_name
from (
    select distinct
        eva as station_id,
        station_name,
        xml_station_name
    from bronze.raw_stop_events
) station_source;

create or replace table silver.dim_train_service as
select
    row_number() over (order by train_type, train_number, line_number, service_class) as train_service_key,
    train_type,
    train_number,
    line_number,
    service_class
from (
    select distinct
        train_type,
        train_number,
        line_number,
        case
            when train_type in ('ICE', 'IC', 'EC', 'NJ', 'RJ', 'TGV', 'FLX') then 'long_distance'
            when train_type in ('RE', 'RB', 'IRE', 'MEX') then 'regional'
            when train_type in ('S', 'U', 'STR', 'Bus', 'Tram') then 'local_urban'
            else 'other'
        end as service_class
    from bronze.raw_stop_events
) train_service_source;

create or replace table silver.dim_date as
select
    cast(strftime(service_date, '%Y%m%d') as integer) as date_key,
    service_date as calendar_date,
    year(service_date) as year,
    month(service_date) as month,
    weekofyear(service_date) as week_of_year,
    isodow(service_date) as day_of_week,
    dayname(service_date) as day_name,
    isodow(service_date) in (6, 7) as is_weekend
from (
    select distinct cast(time as date) as service_date
    from bronze.raw_stop_events
) date_source;

create or replace table silver.dim_hour as
select
    hour_of_day as hour_key,
    hour_of_day,
    case
        when hour_of_day between 6 and 9 then 'peak'
        when hour_of_day between 16 and 19 then 'peak'
        else 'off_peak'
    end as time_band
from (
    select distinct date_part('hour', time)::integer as hour_of_day
    from bronze.raw_stop_events
) hour_source;

create or replace table silver.fact_stop_event as
with base_rows as (
    select
        id as stop_event_key,
        cast(time as date) as service_date,
        date_part('hour', time)::integer as hour_of_day,
        eva as station_id,
        station_name,
        xml_station_name,
        train_type,
        train_number,
        line_number,
        final_destination_station,
        delay_in_min,
        time as provider_event_ts,
        is_canceled,
        train_line_ride_id as journey_id,
        train_line_station_num as stop_sequence,
        cast(arrival_planned_time as timestamp) as planned_arrival_ts,
        cast(arrival_change_time as timestamp) as actual_arrival_ts,
        cast(departure_planned_time as timestamp) as planned_departure_ts,
        cast(departure_change_time as timestamp) as actual_departure_ts,
        source_file,
        loaded_at_utc
    from bronze.raw_stop_events
),
delay_rows as (
    select
        *,
        case
            when planned_arrival_ts is not null and actual_arrival_ts is not null
            then datediff('minute', planned_arrival_ts, actual_arrival_ts)
            else null
        end as arrival_delay_min,
        case
            when planned_departure_ts is not null and actual_departure_ts is not null
            then datediff('minute', planned_departure_ts, actual_departure_ts)
            else null
        end as departure_delay_min
    from base_rows
)
select
    delay_rows.stop_event_key,
    cast(strftime(delay_rows.service_date, '%Y%m%d') as integer) as date_key,
    delay_rows.hour_of_day as hour_key,
    station_dim.station_key,
    train_service_dim.train_service_key,
    delay_rows.service_date,
    delay_rows.journey_id,
    delay_rows.stop_sequence,
    delay_rows.final_destination_station,
    delay_rows.delay_in_min as provider_delay_in_min,
    delay_rows.provider_event_ts,
    delay_rows.planned_arrival_ts,
    delay_rows.actual_arrival_ts,
    delay_rows.planned_departure_ts,
    delay_rows.actual_departure_ts,
    delay_rows.arrival_delay_min,
    delay_rows.departure_delay_min,
    case
        when delay_rows.arrival_delay_min is not null and delay_rows.departure_delay_min is not null
        then delay_rows.departure_delay_min - delay_rows.arrival_delay_min
        else null
    end as delay_change_min,
    coalesce(delay_rows.is_canceled, false) as is_cancellation,
    case
        when delay_rows.planned_arrival_ts is not null or delay_rows.actual_arrival_ts is not null
        then coalesce(delay_rows.is_canceled, false)
        else false
    end as is_arrival_cancelled,
    case
        when delay_rows.planned_departure_ts is not null or delay_rows.actual_departure_ts is not null
        then coalesce(delay_rows.is_canceled, false)
        else false
    end as is_departure_cancelled,
    delay_rows.source_file,
    delay_rows.loaded_at_utc
from delay_rows
join silver.dim_station as station_dim
    on delay_rows.station_id = station_dim.station_id
   and delay_rows.station_name = station_dim.station_name
   and delay_rows.xml_station_name = station_dim.xml_station_name
join silver.dim_train_service as train_service_dim
    on delay_rows.train_type = train_service_dim.train_type
   and delay_rows.train_number = train_service_dim.train_number
   and coalesce(delay_rows.line_number, '') = coalesce(train_service_dim.line_number, '');
