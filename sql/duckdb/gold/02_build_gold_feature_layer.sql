create or replace table gold.feature_stop_event as
select
    fact.stop_event_key,
    fact.date_key,
    fact.hour_key,
    fact.station_key,
    fact.train_service_key,
    fact.service_date,
    fact.journey_id,
    fact.stop_sequence,
    station.station_id,
    station.station_name,
    service.train_type,
    service.train_number,
    service.line_number,
    service.service_class,
    date_dim.calendar_date,
    date_dim.year,
    date_dim.month,
    date_dim.week_of_year,
    date_dim.day_of_week,
    date_dim.day_name,
    date_dim.is_weekend,
    hour_dim.hour_of_day,
    hour_dim.time_band,
    fact.provider_delay_in_min,
    fact.arrival_delay_min,
    fact.departure_delay_min,
    fact.delay_change_min,
    fact.is_cancellation,
    fact.is_arrival_cancelled,
    fact.is_departure_cancelled,
    coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) as event_delay_min,
    coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) is not null as has_delay_measurement,
    coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) > 0 as is_delayed,
    coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) >= 15 as is_severe_delay,
    coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) >= 30 as is_extreme_delay,
    fact.departure_delay_min >= 15 as is_departure_severe_delay,
    case
        when coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) is null then 'unknown'
        when coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) <= 0 then 'early_or_on_time'
        when coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) between 1 and 5 then 'minor'
        when coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) between 6 and 14 then 'medium'
        when coalesce(fact.departure_delay_min, fact.arrival_delay_min, fact.provider_delay_in_min) between 15 and 29 then 'severe'
        else 'extreme'
    end as delay_bucket,
    not fact.is_cancellation as is_active_stop,
    fact.planned_arrival_ts is not null or fact.actual_arrival_ts is not null as has_arrival_time_data,
    fact.planned_departure_ts is not null or fact.actual_departure_ts is not null as has_departure_time_data
from silver.fact_stop_event as fact
join silver.dim_station as station
    on fact.station_key = station.station_key
join silver.dim_train_service as service
    on fact.train_service_key = service.train_service_key
join silver.dim_date as date_dim
    on fact.date_key = date_dim.date_key
join silver.dim_hour as hour_dim
    on fact.hour_key = hour_dim.hour_key;

create or replace table gold.fact_station_hour as
with grouped as (
    select
        station_key,
        date_key,
        hour_key,
        min(station_id) as station_id,
        min(station_name) as station_name,
        min(calendar_date) as calendar_date,
        min(year) as year,
        min(month) as month,
        min(week_of_year) as week_of_year,
        min(day_of_week) as day_of_week,
        min(day_name) as day_name,
        min(is_weekend) as is_weekend,
        min(hour_of_day) as hour_of_day,
        min(time_band) as time_band,
        count(*) as stop_event_count,
        sum(case when has_delay_measurement then 1 else 0 end) as measured_delay_event_count,
        sum(case when is_delayed then 1 else 0 end) as delayed_event_count,
        sum(case when is_severe_delay then 1 else 0 end) as severe_delay_event_count,
        sum(case when is_extreme_delay then 1 else 0 end) as extreme_delay_event_count,
        sum(case when is_cancellation then 1 else 0 end) as cancellation_event_count,
        sum(case when has_arrival_time_data then 1 else 0 end) as arrival_time_data_count,
        sum(case when has_departure_time_data then 1 else 0 end) as departure_time_data_count,
        avg(event_delay_min) as avg_event_delay_min,
        max(event_delay_min) as max_event_delay_min
    from gold.feature_stop_event
    group by 1, 2, 3
)
select
    station_key,
    date_key,
    hour_key,
    station_id,
    station_name,
    calendar_date,
    year,
    month,
    week_of_year,
    day_of_week,
    day_name,
    is_weekend,
    hour_of_day,
    time_band,
    stop_event_count,
    measured_delay_event_count,
    delayed_event_count,
    severe_delay_event_count,
    extreme_delay_event_count,
    cancellation_event_count,
    arrival_time_data_count,
    departure_time_data_count,
    avg_event_delay_min,
    max_event_delay_min,
    delayed_event_count::double / nullif(measured_delay_event_count, 0) as pct_delayed,
    cancellation_event_count::double / nullif(stop_event_count, 0) as pct_cancellation,
    severe_delay_event_count::double / nullif(measured_delay_event_count, 0) as pct_severe_delay
from grouped;
