from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from string import Template
from urllib.request import urlopen, urlretrieve

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = REPO_ROOT / "config" / "scope.yml"
SOURCE_DIR = REPO_ROOT / "data" / "source"
SCOPED_DIR = REPO_ROOT / "data" / "scoped"
MANIFEST_DIR = SCOPED_DIR / "manifests"
SCOPE_EXPANSION_MANIFEST_PATH = MANIFEST_DIR / "scope_expansion_manifest.json"
DUCKDB_PATH = SCOPED_DIR / "local_scope_bronze.duckdb"
SUMMARY_PATH = SCOPED_DIR / "bronze_validation_summary.json"
CREATE_SCHEMA_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "bronze" / "01_create_bronze_schema.sql"
LOAD_BRONZE_SQL_PATH = REPO_ROOT / "sql" / "duckdb" / "bronze" / "02_load_scoped_bronze.sql"
HF_MONTHLY_TREE_URL = "https://huggingface.co/api/datasets/piebro/deutsche-bahn-data/tree/main/monthly_processed_data"
HF_MONTHLY_FILE_TEMPLATE = "https://huggingface.co/datasets/piebro/deutsche-bahn-data/resolve/main/monthly_processed_data/{file_name}"
ROW_SAMPLE_LIMIT = 3
BASELINE_SCOPE_SLICE = "baseline_month"
ADDED_SCOPE_SLICE = "added_disrupted_week"


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
    added_week_source_file_name: str | None = None
    added_week_source_url: str | None = None
    added_week_source_version: str | None = None
    added_week_start_date: str | None = None
    added_week_end_date: str | None = None
    added_week_selection_metric: str | None = None

    @property
    def local_source_path(self) -> Path:
        return SOURCE_DIR / self.source_file_name


@dataclass(frozen=True)
class AddedWeekSelection:
    source_file_name: str
    source_url: str
    source_version: str
    week_start_date: str
    week_end_date: str
    hub_stop_count: int
    severe_or_cancel_count: int
    severe_or_cancel_share: float
    rank_metric_name: str = "severe_or_cancel_count"


@dataclass(frozen=True)
class SourceSlice:
    scope_slice: str
    source_file_name: str
    source_url: str
    source_version: str
    local_source_path: Path
    scope_label: str
    week_start_date: str | None
    week_end_date: str | None


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
        added_week_source_file_name=config_data.get("added_week_source_file_name"),
        added_week_source_url=config_data.get("added_week_source_url"),
        added_week_source_version=config_data.get("added_week_source_version"),
        added_week_start_date=config_data.get("added_week_start_date"),
        added_week_end_date=config_data.get("added_week_end_date"),
        added_week_selection_metric=config_data.get("added_week_selection_metric"),
    )


def write_scope_config(config: ScopeConfig, path: Path) -> None:
    path.write_text(json.dumps(asdict(config), indent=2, ensure_ascii=False), encoding="utf-8")


def build_month_source_url(file_name: str) -> str:
    return HF_MONTHLY_FILE_TEMPLATE.format(file_name=file_name)


def build_month_source_version(file_name: str) -> str:
    return f"monthly_processed_data/{file_name}@main"


def parse_month_bounds(file_name: str) -> tuple[date, date]:
    month_token = file_name.removeprefix("data-").removesuffix(".parquet")
    month_start = datetime.strptime(month_token, "%Y-%m").date()
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)
    return month_start, next_month_start - timedelta(days=1)


def discover_remote_month_files() -> list[str]:
    with urlopen(HF_MONTHLY_TREE_URL) as response:
        payload = json.load(response)
    return sorted(
        item["path"].split("/")[-1]
        for item in payload
        if item.get("type") == "file" and str(item.get("path", "")).endswith(".parquet")
    )


def prioritize_candidate_month_files(file_names: list[str], baseline_file_name: str) -> list[str]:
    baseline_month_token = baseline_file_name.removeprefix("data-").removesuffix(".parquet")
    baseline_month = datetime.strptime(baseline_month_token, "%Y-%m").date()

    def sort_key(file_name: str) -> tuple[int, str]:
        month_token = file_name.removeprefix("data-").removesuffix(".parquet")
        month_date = datetime.strptime(month_token, "%Y-%m").date()
        month_distance = abs((month_date.year - baseline_month.year) * 12 + (month_date.month - baseline_month.month))
        return (month_distance, file_name)

    return sorted((file_name for file_name in file_names if file_name != baseline_file_name), key=sort_key)


def ensure_source_file(file_name: str, source_url: str) -> Path:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = SOURCE_DIR / file_name
    if not local_path.exists():
        urlretrieve(source_url, local_path)
    return local_path


def reset_duckdb_database(database_path: Path) -> None:
    SCOPED_DIR.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()


def render_sql_template(template_path: Path, values: dict[str, str]) -> str:
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(values)


def ensure_httpfs(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("INSTALL httpfs")
    connection.execute("LOAD httpfs")


def query_candidate_weeks(connection: duckdb.DuckDBPyConnection, *, source_url: str, selected_hub: str, month_start: date, month_end: date) -> list[AddedWeekSelection]:
    query = """
        with station_rows as (
            select
                cast(time as timestamp) as event_ts,
                coalesce(delay_in_min, 0) as delay_in_min,
                coalesce(is_canceled, false) as is_canceled
            from read_parquet(?)
            where station_name = ?
              and time is not null
        ),
        weekly as (
            select
                cast(date_trunc('week', event_ts) as date) as week_start_date,
                count(*) as hub_stop_count,
                sum(case when delay_in_min >= 15 or is_canceled then 1 else 0 end) as severe_or_cancel_count,
                avg(case when delay_in_min >= 15 or is_canceled then 1.0 else 0.0 end) as severe_or_cancel_share
            from station_rows
            group by 1
        )
        select
            week_start_date,
            hub_stop_count,
            severe_or_cancel_count,
            severe_or_cancel_share
        from weekly
        where week_start_date >= ?
          and week_start_date + 6 <= ?
    """
    rows = connection.execute(query, [source_url, selected_hub, month_start.isoformat(), month_end.isoformat()]).fetchall()
    results: list[AddedWeekSelection] = []
    file_name = Path(source_url).name
    for week_start, hub_stop_count, severe_or_cancel_count, severe_or_cancel_share in rows:
        week_start_date = week_start if isinstance(week_start, date) else datetime.strptime(str(week_start), "%Y-%m-%d").date()
        week_end_date = week_start_date + timedelta(days=6)
        results.append(
            AddedWeekSelection(
                source_file_name=file_name,
                source_url=source_url,
                source_version=build_month_source_version(file_name),
                week_start_date=week_start_date.isoformat(),
                week_end_date=week_end_date.isoformat(),
                hub_stop_count=int(hub_stop_count),
                severe_or_cancel_count=int(severe_or_cancel_count),
                severe_or_cancel_share=float(severe_or_cancel_share),
            )
        )
    return results


def select_added_week(config: ScopeConfig) -> AddedWeekSelection:
    if all(
        [
            config.added_week_source_file_name,
            config.added_week_source_url,
            config.added_week_source_version,
            config.added_week_start_date,
            config.added_week_end_date,
        ]
    ):
        return AddedWeekSelection(
            source_file_name=str(config.added_week_source_file_name),
            source_url=str(config.added_week_source_url),
            source_version=str(config.added_week_source_version),
            week_start_date=str(config.added_week_start_date),
            week_end_date=str(config.added_week_end_date),
            hub_stop_count=0,
            severe_or_cancel_count=0,
            severe_or_cancel_share=0.0,
            rank_metric_name=str(config.added_week_selection_metric or "manual_or_cached_selection"),
        )

    candidates: list[AddedWeekSelection] = []
    connection = duckdb.connect()
    try:
        ensure_httpfs(connection)
        candidate_files = prioritize_candidate_month_files(discover_remote_month_files(), config.source_file_name)
        for file_name in candidate_files[:4]:
            month_start, month_end = parse_month_bounds(file_name)
            source_url = build_month_source_url(file_name)
            candidates.extend(
                query_candidate_weeks(
                    connection,
                    source_url=source_url,
                    selected_hub=config.selected_hub,
                    month_start=month_start,
                    month_end=month_end,
                )
            )
    finally:
        connection.close()

    if not candidates:
        raise RuntimeError("no complete candidate weeks found for same-hub scope expansion")

    return sorted(
        candidates,
        key=lambda item: (
            -item.severe_or_cancel_count,
            -item.severe_or_cancel_share,
            -item.hub_stop_count,
            item.source_file_name,
            item.week_start_date,
        ),
    )[0]


def build_scope_slices(config: ScopeConfig, added_week: AddedWeekSelection) -> list[SourceSlice]:
    baseline_path = ensure_source_file(config.source_file_name, config.source_url)
    added_path = ensure_source_file(added_week.source_file_name, added_week.source_url)
    return [
        SourceSlice(
            scope_slice=BASELINE_SCOPE_SLICE,
            source_file_name=config.source_file_name,
            source_url=config.source_url,
            source_version=config.source_version,
            local_source_path=baseline_path,
            scope_label=config.selected_month,
            week_start_date=None,
            week_end_date=None,
        ),
        SourceSlice(
            scope_slice=ADDED_SCOPE_SLICE,
            source_file_name=added_week.source_file_name,
            source_url=added_week.source_url,
            source_version=added_week.source_version,
            local_source_path=added_path,
            scope_label=f"{added_week.week_start_date}:{added_week.week_end_date}",
            week_start_date=added_week.week_start_date,
            week_end_date=added_week.week_end_date,
        ),
    ]


def write_scope_expansion_manifest(config: ScopeConfig, added_week: AddedWeekSelection, source_slices: list[SourceSlice]) -> dict[str, object]:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scope_version": config.scope_version,
        "extraction_query_version": config.extraction_query_version,
        "selected_hub": config.selected_hub,
        "baseline_source_file_name": config.source_file_name,
        "baseline_selected_month": config.selected_month,
        "added_week_source_file_name": added_week.source_file_name,
        "added_week_source_version": added_week.source_version,
        "added_week_start_date": added_week.week_start_date,
        "added_week_end_date": added_week.week_end_date,
        "added_week_selection_metric": added_week.rank_metric_name,
        "added_week_metric_values": {
            "hub_stop_count": added_week.hub_stop_count,
            "severe_or_cancel_count": added_week.severe_or_cancel_count,
            "severe_or_cancel_share": added_week.severe_or_cancel_share,
        },
        "source_slices": [
            {
                "scope_slice": source_slice.scope_slice,
                "source_file_name": source_slice.source_file_name,
                "source_url": source_slice.source_url,
                "source_version": source_slice.source_version,
                "scope_label": source_slice.scope_label,
                "week_start_date": source_slice.week_start_date,
                "week_end_date": source_slice.week_end_date,
            }
            for source_slice in source_slices
        ],
    }
    SCOPE_EXPANSION_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def execute_bronze_load(config: ScopeConfig, source_slices: list[SourceSlice], added_week: AddedWeekSelection) -> Path:
    reset_duckdb_database(DUCKDB_PATH)
    baseline_slice = next(item for item in source_slices if item.scope_slice == BASELINE_SCOPE_SLICE)
    added_slice = next(item for item in source_slices if item.scope_slice == ADDED_SCOPE_SLICE)
    run_timestamp_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "")
    substitutions = {
        "baseline_source_path": baseline_slice.local_source_path.as_posix(),
        "baseline_source_file_name": baseline_slice.source_file_name,
        "baseline_source_version": baseline_slice.source_version,
        "added_source_path": added_slice.local_source_path.as_posix(),
        "added_source_file_name": added_slice.source_file_name,
        "added_source_version": added_slice.source_version,
        "scope_version": config.scope_version,
        "extraction_query_version": config.extraction_query_version,
        "selected_month": config.selected_month,
        "selected_hub": config.selected_hub.replace("'", "''"),
        "required_columns_json": json.dumps(list(config.required_columns)).replace("'", "''"),
        "complete_journey_rule": config.complete_journey_rule.replace("'", "''"),
        "added_week_start_date": added_week.week_start_date,
        "added_week_end_date": added_week.week_end_date,
        "added_week_end_exclusive_date": (datetime.strptime(added_week.week_end_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat(),
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
        manifest_rows = connection.execute(
            "select scope_slice, source_file, source_version, scope_label, scope_week_start_date, scope_week_end_date, row_count from bronze.raw_ingestion_manifest order by scope_slice"
        ).fetchall()
        manifest_row_count = connection.execute("select sum(row_count) from bronze.raw_ingestion_manifest").fetchone()
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
        scope_rows = connection.execute(
            """
            select
                scope_slice,
                source_file,
                min(cast(time as date)) as min_service_date,
                max(cast(time as date)) as max_service_date,
                count(*) as row_count,
                count(distinct train_line_ride_id) as journey_count
            from bronze.raw_stop_events
            group by 1, 2
            order by 1
            """
        ).fetchall()
    finally:
        connection.close()

    if manifest_row_count is None or raw_row_count is None or hub_row_count is None or journey_count is None:
        raise RuntimeError("Bronze validation counts could not be computed")

    summary = {
        "scope_version": config.scope_version,
        "selected_month": config.selected_month,
        "selected_hub": config.selected_hub,
        "source_file_name": config.source_file_name,
        "added_week_source_file_name": config.added_week_source_file_name,
        "added_week_start_date": config.added_week_start_date,
        "added_week_end_date": config.added_week_end_date,
        "duckdb_path": str(DUCKDB_PATH),
        "scope_expansion_manifest_path": str(SCOPE_EXPANSION_MANIFEST_PATH),
        "raw_stop_events_row_count": raw_row_count[0],
        "manifest_row_count": manifest_row_count[0],
        "hub_row_count": hub_row_count[0],
        "journey_count": journey_count[0],
        "hub_sample_rows": sample_rows,
        "manifest_rows": manifest_rows,
        "scope_rows": scope_rows,
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
    added_week = select_added_week(config)
    config = ScopeConfig(
        **{
            **asdict(config),
            "added_week_source_file_name": added_week.source_file_name,
            "added_week_source_url": added_week.source_url,
            "added_week_source_version": added_week.source_version,
            "added_week_start_date": added_week.week_start_date,
            "added_week_end_date": added_week.week_end_date,
            "added_week_selection_metric": added_week.rank_metric_name,
        }
    )
    write_scope_config(config, SCOPE_PATH)
    source_slices = build_scope_slices(config, added_week)
    write_scope_expansion_manifest(config, added_week, source_slices)
    execute_bronze_load(config, source_slices, added_week)
    summary = collect_validation_summary(config)
    write_summary(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
