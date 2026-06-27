from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from string import Template
from urllib.request import urlretrieve

import duckdb


REPO_ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = REPO_ROOT / "config" / "scope.yml"
SOURCE_DIR = REPO_ROOT / "data" / "source"
SCOPED_DIR = REPO_ROOT / "data" / "scoped"
DUCKDB_PATH = SCOPED_DIR / "local_scope_bronze.duckdb"
SUMMARY_PATH = SCOPED_DIR / "bronze_validation_summary.json"
CREATE_SCHEMA_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "bronze" / "01_create_bronze_schema.sql"
LOAD_BRONZE_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "bronze" / "02_load_scoped_bronze.sql"
ROW_SAMPLE_LIMIT = 3


@dataclass(frozen=True)
class ScopeConfig:
    scope_version: str
    extraction_query_version: str
    selected_month: str
    selected_hub: str
    source_file_name: str
    source_url: str
    source_version: str
    required_columns: tuple[str, ...]
    complete_journey_rule: str

    @property
    def local_source_path(self) -> Path:
        return SOURCE_DIR / self.source_file_name


def load_scope_config(path: Path) -> ScopeConfig:
    config_data = json.loads(path.read_text(encoding="utf-8"))
    return ScopeConfig(
        scope_version=config_data["scope_version"],
        extraction_query_version=config_data["extraction_query_version"],
        selected_month=config_data["selected_month"],
        selected_hub=config_data["selected_hub"],
        source_file_name=config_data["source_file_name"],
        source_url=config_data["source_url"],
        source_version=config_data["source_version"],
        required_columns=tuple(config_data["required_columns"]),
        complete_journey_rule=config_data["complete_journey_rule"],
    )


def ensure_source_file(config: ScopeConfig) -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    if not config.local_source_path.exists():
        urlretrieve(config.source_url, config.local_source_path)
    return config.local_source_path


def reset_duckdb_database(database_path: Path) -> None:
    SCOPED_DIR.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()


def render_sql_template(template_path: Path, values: dict[str, str]) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(values)


def execute_bronze_load(config: ScopeConfig, source_path: Path) -> Path:
    reset_duckdb_database(DUCKDB_PATH)
    run_timestamp_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "")
    substitutions = {
        "source_path": source_path.as_posix(),
        "source_file_name": config.source_file_name,
        "source_version": config.source_version,
        "scope_version": config.scope_version,
        "extraction_query_version": config.extraction_query_version,
        "selected_month": config.selected_month,
        "selected_hub": config.selected_hub.replace("'", "''"),
        "required_columns_json": json.dumps(list(config.required_columns)).replace("'", "''"),
        "complete_journey_rule": config.complete_journey_rule.replace("'", "''"),
        "run_timestamp_utc": run_timestamp_utc,
    }
    create_schema_sql = CREATE_SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    load_sql = render_sql_template(LOAD_BRONZE_SQL_PATH, substitutions)

    connection = duckdb.connect(str(DUCKDB_PATH))
    try:
        connection.execute(create_schema_sql)
        connection.execute(load_sql)
    finally:
        connection.close()
    return DUCKDB_PATH


def collect_validation_summary(config: ScopeConfig) -> dict[str, object]:
    connection = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        manifest_row_count = connection.execute(
            "select row_count from bronze.raw_ingestion_manifest"
        ).fetchone()
        raw_row_count = connection.execute("select count(*) from bronze.raw_stop_events").fetchone()
        hub_row_count = connection.execute(
            "select count(*) from bronze.raw_stop_events where station_name = ?",
            [config.selected_hub],
        ).fetchone()
        journey_count = connection.execute(
            "select count(distinct train_line_ride_id) from bronze.raw_stop_events"
        ).fetchone()
        sample_rows = connection.execute(
            """
            select station_name, train_type, train_number, final_destination_station, train_line_ride_id
            from bronze.raw_stop_events
            where station_name = ?
            limit ?
            """,
            [config.selected_hub, ROW_SAMPLE_LIMIT],
        ).fetchall()
        manifest_row = connection.execute(
            "select * from bronze.raw_ingestion_manifest"
        ).fetchone()
    finally:
        connection.close()

    if manifest_row_count is None or raw_row_count is None or hub_row_count is None or journey_count is None:
        raise RuntimeError("Bronze validation counts could not be computed")

    summary = {
        "scope_version": config.scope_version,
        "selected_month": config.selected_month,
        "selected_hub": config.selected_hub,
        "source_file_name": config.source_file_name,
        "duckdb_path": str(DUCKDB_PATH),
        "raw_stop_events_row_count": raw_row_count[0],
        "manifest_row_count": manifest_row_count[0],
        "hub_row_count": hub_row_count[0],
        "journey_count": journey_count[0],
        "hub_sample_rows": sample_rows,
        "manifest_row": manifest_row,
    }
    if summary["raw_stop_events_row_count"] <= 0:
        raise AssertionError("Bronze extraction returned no rows")
    if summary["hub_row_count"] <= 0:
        raise AssertionError("Selected hub is missing from scoped Bronze rows")
    if summary["raw_stop_events_row_count"] != summary["manifest_row_count"]:
        raise AssertionError("Manifest row_count does not match Bronze row count")
    return summary


def write_summary(summary: dict[str, object]) -> None:
    SCOPED_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def main() -> None:
    config = load_scope_config(SCOPE_PATH)
    source_path = ensure_source_file(config)
    execute_bronze_load(config, source_path)
    summary = collect_validation_summary(config)
    write_summary(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
