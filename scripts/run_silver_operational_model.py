from __future__ import annotations

import json
from pathlib import Path

import duckdb


REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "scoped" / "local_scope_bronze.duckdb"
SUMMARY_PATH = REPO_ROOT / "data" / "scoped" / "silver_validation_summary.json"
CREATE_SCHEMA_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "silver" / "01_create_silver_schema.sql"
BUILD_MODEL_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "silver" / "02_build_silver_operational_model.sql"
ROW_SAMPLE_LIMIT = 5


def execute_silver_build() -> None:
    connection = duckdb.connect(str(DUCKDB_PATH))
    try:
        connection.execute(CREATE_SCHEMA_SQL_PATH.read_text(encoding="utf-8"))
        connection.execute(BUILD_MODEL_SQL_PATH.read_text(encoding="utf-8"))
    finally:
        connection.close()


def collect_summary() -> dict[str, object]:
    connection = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        bronze_row_count = connection.execute("select count(*) from bronze.raw_stop_events").fetchone()
        silver_row_count = connection.execute("select count(*) from silver.fact_stop_event").fetchone()
        station_count = connection.execute("select count(*) from silver.dim_station").fetchone()
        train_service_count = connection.execute("select count(*) from silver.dim_train_service").fetchone()
        date_count = connection.execute("select count(*) from silver.dim_date").fetchone()
        hour_count = connection.execute("select count(*) from silver.dim_hour").fetchone()
        sample_rows = connection.execute(
            """
            select
                stop_event_key,
                service_date,
                journey_id,
                planned_arrival_ts,
                actual_arrival_ts,
                arrival_delay_min,
                planned_departure_ts,
                actual_departure_ts,
                departure_delay_min,
                is_cancellation
            from silver.fact_stop_event
            limit ?
            """,
            [ROW_SAMPLE_LIMIT],
        ).fetchall()
        service_class_sample = connection.execute(
            """
            select train_type, train_number, line_number, service_class
            from silver.dim_train_service
            limit ?
            """,
            [ROW_SAMPLE_LIMIT],
        ).fetchall()
    finally:
        connection.close()

    if bronze_row_count is None or silver_row_count is None:
        raise RuntimeError("Silver validation counts could not be computed")

    summary = {
        "duckdb_path": str(DUCKDB_PATH),
        "bronze_row_count": bronze_row_count[0],
        "silver_fact_stop_event_row_count": silver_row_count[0],
        "dim_station_row_count": station_count[0] if station_count else None,
        "dim_train_service_row_count": train_service_count[0] if train_service_count else None,
        "dim_date_row_count": date_count[0] if date_count else None,
        "dim_hour_row_count": hour_count[0] if hour_count else None,
        "fact_stop_event_sample": sample_rows,
        "train_service_sample": service_class_sample,
    }
    if summary["bronze_row_count"] != summary["silver_fact_stop_event_row_count"]:
        raise AssertionError("Silver fact row count does not match Bronze raw row count")
    return summary


def write_summary(summary: dict[str, object]) -> None:
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def main() -> None:
    execute_silver_build()
    summary = collect_summary()
    write_summary(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
