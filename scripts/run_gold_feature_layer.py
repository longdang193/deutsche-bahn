from __future__ import annotations

import json
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "scoped" / "local_scope_bronze.duckdb"
SUMMARY_PATH = REPO_ROOT / "data" / "scoped" / "gold_validation_summary.json"
CREATE_SCHEMA_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "gold" / "01_create_gold_schema.sql"
BUILD_MODEL_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "gold" / "02_build_gold_feature_layer.sql"
ROW_SAMPLE_LIMIT = 5


def execute_gold_build() -> None:
    connection = duckdb.connect(str(DUCKDB_PATH))
    try:
        connection.execute(CREATE_SCHEMA_SQL_PATH.read_text(encoding="utf-8"))
        connection.execute(BUILD_MODEL_SQL_PATH.read_text(encoding="utf-8"))
    finally:
        connection.close()


def collect_summary() -> dict[str, object]:
    connection = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        silver_row_count = connection.execute("select count(*) from silver.fact_stop_event").fetchone()
        gold_event_row_count = connection.execute("select count(*) from gold.feature_stop_event").fetchone()
        distinct_station_hour_count = connection.execute(
            "select count(*) from (select distinct station_key, date_key, hour_key from gold.feature_stop_event)",
        ).fetchone()
        gold_station_hour_row_count = connection.execute("select count(*) from gold.fact_station_hour").fetchone()
        station_hour_stop_event_sum = connection.execute(
            "select sum(stop_event_count) from gold.fact_station_hour",
        ).fetchone()
        aggregate_mismatch_count = connection.execute(
            """
            with recomputed as (
                select
                    station_key,
                    date_key,
                    hour_key,
                    count(*) as stop_event_count,
                    sum(case when has_delay_measurement then 1 else 0 end) as measured_delay_event_count,
                    sum(case when is_delayed then 1 else 0 end) as delayed_event_count,
                    sum(case when is_heavy_delay then 1 else 0 end) as heavy_delay_event_count,
                    sum(case when is_extreme_delay then 1 else 0 end) as extreme_delay_event_count,
                    sum(case when is_cancellation then 1 else 0 end) as cancellation_event_count,
                    sum(case when has_arrival_time_data then 1 else 0 end) as arrival_time_data_count,
                    sum(case when has_departure_time_data then 1 else 0 end) as departure_time_data_count,
                    avg(event_delay_min) as avg_event_delay_min,
                    max(event_delay_min) as max_event_delay_min,
                    sum(case when is_delayed then 1 else 0 end)::double
                        / nullif(sum(case when has_delay_measurement then 1 else 0 end), 0) as pct_delayed,
                    sum(case when is_cancellation then 1 else 0 end)::double
                        / nullif(count(*), 0) as pct_cancellation,
                    sum(case when is_heavy_delay then 1 else 0 end)::double
                        / nullif(sum(case when has_delay_measurement then 1 else 0 end), 0) as pct_heavy_delay
                from gold.feature_stop_event
                group by 1, 2, 3
            )
            select count(*)
            from recomputed
            join gold.fact_station_hour using (station_key, date_key, hour_key)
            where recomputed.stop_event_count is distinct from gold.fact_station_hour.stop_event_count
               or recomputed.measured_delay_event_count is distinct from gold.fact_station_hour.measured_delay_event_count
               or recomputed.delayed_event_count is distinct from gold.fact_station_hour.delayed_event_count
               or recomputed.heavy_delay_event_count is distinct from gold.fact_station_hour.heavy_delay_event_count
               or recomputed.extreme_delay_event_count is distinct from gold.fact_station_hour.extreme_delay_event_count
               or recomputed.cancellation_event_count is distinct from gold.fact_station_hour.cancellation_event_count
               or recomputed.arrival_time_data_count is distinct from gold.fact_station_hour.arrival_time_data_count
               or recomputed.departure_time_data_count is distinct from gold.fact_station_hour.departure_time_data_count
               or recomputed.avg_event_delay_min is distinct from gold.fact_station_hour.avg_event_delay_min
               or recomputed.max_event_delay_min is distinct from gold.fact_station_hour.max_event_delay_min
               or recomputed.pct_delayed is distinct from gold.fact_station_hour.pct_delayed
               or recomputed.pct_cancellation is distinct from gold.fact_station_hour.pct_cancellation
               or recomputed.pct_heavy_delay is distinct from gold.fact_station_hour.pct_heavy_delay
            """,
        ).fetchone()
        feature_sample = connection.execute(
            """
            select
                stop_event_key,
                station_name,
                service_class,
                event_delay_min,
                has_delay_measurement,
                is_delayed,
                is_heavy_delay,
                is_extreme_delay,
                is_departure_severe_delay,
                delay_bucket
            from gold.feature_stop_event
            limit ?
            """,
            [ROW_SAMPLE_LIMIT],
        ).fetchall()
        station_hour_sample = connection.execute(
            """
            select
                station_name,
                calendar_date,
                hour_of_day,
                stop_event_count,
                arrival_time_data_count,
                departure_time_data_count,
                delayed_event_count,
                avg_event_delay_min,
                pct_delayed,
                pct_cancellation
            from gold.fact_station_hour
            limit ?
            """,
            [ROW_SAMPLE_LIMIT],
        ).fetchall()
    finally:
        connection.close()

    if silver_row_count is None or gold_event_row_count is None:
        raise RuntimeError("Gold validation counts could not be computed")

    summary = {
        "duckdb_path": str(DUCKDB_PATH),
        "silver_fact_stop_event_row_count": silver_row_count[0],
        "gold_feature_stop_event_row_count": gold_event_row_count[0],
        "distinct_station_hour_row_count": distinct_station_hour_count[0] if distinct_station_hour_count else None,
        "gold_fact_station_hour_row_count": gold_station_hour_row_count[0] if gold_station_hour_row_count else None,
        "station_hour_stop_event_sum": station_hour_stop_event_sum[0] if station_hour_stop_event_sum else None,
        "aggregate_mismatch_row_count": aggregate_mismatch_count[0] if aggregate_mismatch_count else None,
        "feature_stop_event_sample": feature_sample,
        "fact_station_hour_sample": station_hour_sample,
    }
    if summary["silver_fact_stop_event_row_count"] != summary["gold_feature_stop_event_row_count"]:
        raise AssertionError("Gold feature row count does not match Silver fact row count")
    if summary["distinct_station_hour_row_count"] != summary["gold_fact_station_hour_row_count"]:
        raise AssertionError("Gold station-hour row count does not match distinct Gold event station-hour combinations")
    if summary["station_hour_stop_event_sum"] != summary["gold_feature_stop_event_row_count"]:
        raise AssertionError("Gold station-hour stop-event sum does not match Gold event row count")
    if summary["aggregate_mismatch_row_count"] != 0:
        raise AssertionError("Gold station-hour aggregate rows do not match recomputed event-level aggregates")
    return summary


def write_summary(summary: dict[str, object]) -> None:
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def main() -> None:
    execute_gold_build()
    summary = collect_summary()
    write_summary(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
