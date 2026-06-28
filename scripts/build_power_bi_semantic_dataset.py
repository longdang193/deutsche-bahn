"""# @meta
# type: script
# distribution_tier: starter_kit
# scope: local
# domain: analytics
# tags:
# - power-bi
# - semantic-export
# - duckdb
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import duckdb
import pandas as pd

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
OPTIMIZATION_FINAL_DIR: Final[Path] = REPO_ROOT / 'data' / 'scoped' / 'optimization' / 'final'
FROZEN_POLICY_PATH: Final[Path] = REPO_ROOT / 'data' / 'scoped' / 'optimization' / 'frozen_policy.json'
POWER_BI_DIR: Final[Path] = REPO_ROOT / 'data' / 'scoped' / 'power_bi'
EVENT_SOURCE_PATH: Final[Path] = OPTIMIZATION_FINAL_DIR / 'event_decision.parquet'
HORIZON_SOURCE_PATH: Final[Path] = OPTIMIZATION_FINAL_DIR / 'horizon_summary.parquet'
EVALUATION_SOURCE_PATH: Final[Path] = OPTIMIZATION_FINAL_DIR / 'evaluation.json'
SEMANTIC_CONTRACT_PATH: Final[Path] = POWER_BI_DIR / 'semantic_contract.json'
DASHBOARD_MANIFEST_PATH: Final[Path] = POWER_BI_DIR / 'dashboard_mvp_manifest.json'
UNKNOWN_STATION_LABEL: Final[str] = 'Unknown station'
UNKNOWN_LABEL: Final[str] = 'Unknown'
FINAL_MODE: Final[str] = 'final'
TEST_SPLIT: Final[str] = 'test'


@dataclass(frozen=True)
class ExportArtifacts:
    event_fact: pd.DataFrame
    horizon_fact: pd.DataFrame
    dim_date_hour: pd.DataFrame
    dim_station: pd.DataFrame
    dim_train_service: pd.DataFrame
    dim_scenario: pd.DataFrame


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding='utf-8'))


def read_parquet(path: Path) -> pd.DataFrame:
    connection = duckdb.connect()
    try:
        return connection.execute(f"select * from read_parquet('{path.as_posix()}')").fetch_df()
    finally:
        connection.close()


def write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    try:
        connection.register('frame_view', frame)
        connection.execute(f"copy frame_view to '{path.as_posix()}' (format parquet)")
    finally:
        connection.close()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_columns(frame: pd.DataFrame, required_columns: list[str], frame_name: str) -> None:
    missing = [column for column in required_columns if column not in frame.columns]
    ensure(not missing, f'{frame_name} missing required columns: {missing}')


def unique_value(frame: pd.DataFrame, column: str, frame_name: str) -> object:
    non_null = frame[column].dropna().unique().tolist()
    ensure(len(non_null) == 1, f'{frame_name} must contain exactly one non-null {column}')
    return non_null[0]


def validate_non_null(frame: pd.DataFrame, column: str, frame_name: str) -> None:
    ensure(not frame[column].isna().any(), f'{frame_name} contains null {column}')


def validate_unique(frame: pd.DataFrame, column: str, frame_name: str) -> None:
    ensure(not frame[column].duplicated().any(), f'{frame_name} contains duplicate {column}')


def validate_horizon_mapping(event_frame: pd.DataFrame) -> None:
    grouped = event_frame.groupby('horizon_id').agg(
        calendar_date_count=('calendar_date', 'nunique'),
        hour_of_day_count=('hour_of_day', 'nunique'),
    )
    ensure(
        bool(((grouped['calendar_date_count'] == 1) & (grouped['hour_of_day_count'] == 1)).all()),
        'each horizon_id must map to exactly one calendar_date and one hour_of_day',
    )


def normalize_event_source(event_source: pd.DataFrame, policy_version: str) -> pd.DataFrame:
    normalized = event_source.copy()
    normalized['scenario_key'] = policy_version
    normalized['train_service_key'] = normalized['train_service_key'].astype('string')
    normalized['station_id'] = normalized['station_id'].astype('string')
    normalized['stop_event_key'] = normalized['stop_event_key'].astype('string')
    normalized['journey_id'] = normalized['journey_id'].astype('string')
    normalized['calendar_date'] = normalized['calendar_date'].astype('string')
    normalized['horizon_id'] = normalized['horizon_id'].astype('string')
    normalized['capacity_scenario'] = normalized['capacity_scenario'].astype('string')
    normalized['execution_mode'] = normalized['execution_mode'].astype('string')
    normalized['prediction_split'] = normalized['prediction_split'].astype('string')
    normalized['optimization_run_id'] = normalized['optimization_run_id'].astype('string')
    normalized['model_name'] = normalized['model_name'].astype('string')
    normalized['model_version'] = normalized['model_version'].astype('string')
    normalized['station_name'] = normalized['station_name'].fillna(UNKNOWN_STATION_LABEL).astype('string')
    normalized['train_type'] = normalized['train_type'].fillna(UNKNOWN_LABEL).astype('string')
    normalized['line_number'] = normalized['line_number'].fillna(UNKNOWN_LABEL).astype('string')
    service_class = normalized['service_class_y'].where(normalized['service_class_y'].notna(), normalized['service_class_x'])
    normalized['service_class'] = service_class.fillna(UNKNOWN_LABEL).astype('string')
    normalized['eligibility_reason'] = normalized['eligibility_reason'].fillna(UNKNOWN_LABEL).astype('string')
    normalized['optimized_at'] = normalized['optimized_at'].astype('string')
    return normalized


def normalize_horizon_source(horizon_source: pd.DataFrame, policy_version: str) -> pd.DataFrame:
    normalized = horizon_source.copy()
    normalized['scenario_key'] = policy_version
    normalized['calendar_date'] = normalized['calendar_date'].astype('string')
    normalized['horizon_id'] = normalized['horizon_id'].astype('string')
    normalized['capacity_scenario'] = normalized['capacity_scenario'].astype('string')
    normalized['optimization_run_id'] = normalized['optimization_run_id'].astype('string')
    normalized['execution_mode'] = normalized['execution_mode'].astype('string')
    normalized['model_name'] = normalized['model_name'].astype('string')
    normalized['model_version'] = normalized['model_version'].astype('string')
    normalized['optimized_at'] = normalized['optimized_at'].astype('string')
    return normalized


def validate_dimension_conflicts(event_frame: pd.DataFrame) -> None:
    station_conflicts = event_frame.groupby('station_id')['station_name'].nunique(dropna=False)
    ensure(bool((station_conflicts == 1).all()), 'one station_id must map to one station attribute set')

    train_service_conflicts = event_frame.groupby('train_service_key').apply(
        lambda frame: frame[['train_type', 'line_number', 'service_class']].drop_duplicates().shape[0],
        include_groups=False,
    )
    ensure(bool((train_service_conflicts == 1).all()), 'one train_service_key must map to one train-service attribute set')


def validate_source_invariants(
    event_frame: pd.DataFrame,
    horizon_frame: pd.DataFrame,
    evaluation: dict[str, object],
    frozen_policy: dict[str, object],
) -> None:
    require_columns(
        event_frame,
        [
            'optimization_run_id',
            'execution_mode',
            'prediction_split',
            'stop_event_key',
            'station_id',
            'train_service_key',
            'calendar_date',
            'hour_of_day',
            'horizon_id',
            'capacity_scenario',
            'capacity_per_hour',
            'minimum_candidate_probability',
            'model_name',
            'model_version',
            'selected_threshold',
            'selected_for_review',
            'actual_is_departure_severe_delay',
            'is_eligible_candidate',
            'objective_contribution',
            'predicted_severe_delay_probability',
            'service_class_x',
            'service_class_y',
        ],
        'event_source',
    )
    require_columns(
        horizon_frame,
        [
            'optimization_run_id',
            'execution_mode',
            'calendar_date',
            'hour_of_day',
            'horizon_id',
            'capacity_scenario',
            'capacity_per_hour',
            'candidate_count',
            'eligible_candidate_count',
            'selected_event_count',
            'selected_probability_score_sum',
            'actual_severe_selected_count',
            'actual_severe_candidate_count',
            'candidate_prevalence',
            'precision_at_capacity',
            'severe_delay_coverage',
            'lift_over_candidate_prevalence',
            'model_name',
            'model_version',
        ],
        'horizon_source',
    )
    ensure(bool(event_frame['execution_mode'].eq(FINAL_MODE).all()), 'event_source execution_mode must be final')
    ensure(bool(horizon_frame['execution_mode'].eq(FINAL_MODE).all()), 'horizon_source execution_mode must be final')
    ensure(bool(event_frame['prediction_split'].eq(TEST_SPLIT).all()), 'event_source prediction_split must be test')
    ensure(evaluation.get('mode') == FINAL_MODE, 'evaluation metadata mode must be final')
    ensure(bool(evaluation.get('selected_set_match')), 'evaluation metadata must confirm selected_set_match')
    validate_non_null(event_frame, 'station_id', 'event_source')
    validate_non_null(event_frame, 'train_service_key', 'event_source')
    validate_non_null(event_frame, 'horizon_id', 'event_source')
    validate_unique(event_frame, 'stop_event_key', 'event_source')
    validate_unique(horizon_frame, 'horizon_id', 'horizon_source')
    validate_horizon_mapping(event_frame)
    ensure('policy_version' in frozen_policy and str(frozen_policy['policy_version']).strip(), 'frozen policy must contain policy_version')

    event_run_id = str(unique_value(event_frame, 'optimization_run_id', 'event_source'))
    horizon_run_id = str(unique_value(horizon_frame, 'optimization_run_id', 'horizon_source'))
    ensure(event_run_id == horizon_run_id, 'event and horizon optimization_run_id must match')

    event_model_name = str(unique_value(event_frame, 'model_name', 'event_source'))
    horizon_model_name = str(unique_value(horizon_frame, 'model_name', 'horizon_source'))
    event_model_version = str(unique_value(event_frame, 'model_version', 'event_source'))
    horizon_model_version = str(unique_value(horizon_frame, 'model_version', 'horizon_source'))
    ensure(event_model_name == horizon_model_name == str(frozen_policy['model_name']), 'model_name must match across artifacts')
    ensure(event_model_version == horizon_model_version == str(frozen_policy['model_version']), 'model_version must match across artifacts')

    event_capacity_scenario = str(unique_value(event_frame, 'capacity_scenario', 'event_source'))
    horizon_capacity_scenario = str(unique_value(horizon_frame, 'capacity_scenario', 'horizon_source'))
    ensure(event_capacity_scenario == horizon_capacity_scenario == str(frozen_policy['capacity_scenario']) == str(evaluation['capacity_scenario']), 'capacity_scenario must match across artifacts')

    event_capacity_per_hour = int(unique_value(event_frame, 'capacity_per_hour', 'event_source'))
    horizon_capacity_per_hour = int(unique_value(horizon_frame, 'capacity_per_hour', 'horizon_source'))
    ensure(event_capacity_per_hour == horizon_capacity_per_hour == int(frozen_policy['capacity_per_hour']) == int(evaluation['capacity_per_hour']), 'capacity_per_hour must match across artifacts')

    event_min_probability = float(unique_value(event_frame, 'minimum_candidate_probability', 'event_source'))
    ensure(event_min_probability == float(frozen_policy['minimum_candidate_probability']) == float(evaluation['minimum_candidate_probability']), 'minimum_candidate_probability must match across artifacts')

    event_selected_threshold = float(unique_value(event_frame, 'selected_threshold', 'event_source'))
    ensure(event_selected_threshold == float(frozen_policy['selected_threshold']), 'selected_threshold must match frozen policy')
    ensure(int(evaluation['horizon_count']) == len(horizon_frame), 'evaluation horizon_count must match horizon rows')


def ordered_columns(contract: dict[str, object], table_name: str) -> list[str]:
    table = contract['tables'][table_name]
    return [str(column['name']) for column in table['columns']]


def validate_frame_against_contract(frame: pd.DataFrame, contract: dict[str, object], table_name: str) -> None:
    expected = ordered_columns(contract, table_name)
    actual = frame.columns.tolist()
    ensure(actual == expected, f'{table_name} columns do not match frozen contract')
    column_contracts = {str(item['name']): item for item in contract['tables'][table_name]['columns']}
    for column_name, column_info in column_contracts.items():
        if not bool(column_info['nullable']):
            ensure(not frame[column_name].isna().any(), f'{table_name}.{column_name} must be non-null')
        value_range = column_info.get('range')
        if value_range is not None:
            minimum, maximum = value_range
            non_null = frame[column_name].dropna()
            ensure(bool(((non_null >= minimum) & (non_null <= maximum)).all()), f'{table_name}.{column_name} must stay within range {value_range}')


def build_event_fact(event_source: pd.DataFrame, scenario_key: str, contract: dict[str, object]) -> pd.DataFrame:
    normalized = normalize_event_source(event_source, scenario_key)
    columns = ordered_columns(contract, 'fact_event_decision')
    event_fact = normalized.loc[:, columns].copy()
    event_fact['hour_of_day'] = event_fact['hour_of_day'].astype('Int64')
    event_fact['capacity_per_hour'] = event_fact['capacity_per_hour'].astype('Int64')
    event_fact['candidate_priority_rank'] = event_fact['candidate_priority_rank'].astype('Int64')
    event_fact['selection_rank'] = event_fact['selection_rank'].astype('Int64')
    event_fact['solver_status'] = event_fact['solver_status'].astype('Int64')
    validate_frame_against_contract(event_fact, contract, 'fact_event_decision')
    return event_fact


def build_horizon_fact(horizon_source: pd.DataFrame, scenario_key: str, contract: dict[str, object]) -> pd.DataFrame:
    normalized = normalize_horizon_source(horizon_source, scenario_key)
    columns = ordered_columns(contract, 'fact_horizon_summary')
    horizon_fact = normalized.loc[:, columns].copy()
    integer_columns = [
        'hour_of_day',
        'capacity_per_hour',
        'candidate_count',
        'eligible_candidate_count',
        'selected_event_count',
        'unused_capacity',
        'actual_severe_selected_count',
        'actual_severe_candidate_count',
        'solver_status',
    ]
    for column_name in integer_columns:
        horizon_fact[column_name] = horizon_fact[column_name].astype('Int64')
    validate_frame_against_contract(horizon_fact, contract, 'fact_horizon_summary')
    return horizon_fact


def format_hour_label(hour_of_day: int) -> str:
    return f'{hour_of_day:02d}:00-{hour_of_day:02d}:59'


def build_dim_date_hour(horizon_fact: pd.DataFrame, contract: dict[str, object]) -> pd.DataFrame:
    dim = horizon_fact[['horizon_id', 'calendar_date', 'hour_of_day']].drop_duplicates().copy()
    dim['date_label'] = dim['calendar_date']
    dim['hour_label'] = dim['hour_of_day'].astype(int).map(format_hour_label)
    dim = dim.loc[:, ordered_columns(contract, 'dim_date_hour')]
    validate_frame_against_contract(dim, contract, 'dim_date_hour')
    validate_unique(dim, 'horizon_id', 'dim_date_hour')
    return dim


def build_dim_station(event_fact: pd.DataFrame, contract: dict[str, object]) -> pd.DataFrame:
    dim = event_fact[['station_id', 'station_name']].drop_duplicates().copy()
    dim = dim.loc[:, ordered_columns(contract, 'dim_station')]
    validate_frame_against_contract(dim, contract, 'dim_station')
    validate_unique(dim, 'station_id', 'dim_station')
    return dim


def build_dim_train_service(event_fact: pd.DataFrame, contract: dict[str, object]) -> pd.DataFrame:
    dim = event_fact[['train_service_key', 'train_type', 'line_number', 'service_class']].drop_duplicates().copy()
    dim = dim.loc[:, ordered_columns(contract, 'dim_train_service')]
    validate_frame_against_contract(dim, contract, 'dim_train_service')
    validate_unique(dim, 'train_service_key', 'dim_train_service')
    return dim


def build_dim_scenario(
    event_fact: pd.DataFrame,
    frozen_policy: dict[str, object],
    contract: dict[str, object],
) -> pd.DataFrame:
    scenario_display_name = (
        f"Prototype {frozen_policy['capacity_scenario']} | "
        f"threshold {float(frozen_policy['minimum_candidate_probability']):.2f} | "
        f"policy {frozen_policy['policy_version']}"
    )
    row = {
        'scenario_key': str(frozen_policy['policy_version']),
        'capacity_scenario': str(frozen_policy['capacity_scenario']),
        'capacity_per_hour': int(frozen_policy['capacity_per_hour']),
        'minimum_candidate_probability': float(frozen_policy['minimum_candidate_probability']),
        'model_name': str(frozen_policy['model_name']),
        'model_version': str(frozen_policy['model_version']),
        'selected_threshold': float(frozen_policy['selected_threshold']),
        'policy_version': str(frozen_policy['policy_version']),
        'frozen_at': str(frozen_policy['frozen_at']),
        'scenario_display_name': scenario_display_name,
    }
    dim = pd.DataFrame([row]).loc[:, ordered_columns(contract, 'dim_scenario')]
    validate_frame_against_contract(dim, contract, 'dim_scenario')
    validate_unique(dim, 'scenario_key', 'dim_scenario')
    ensure(event_fact['scenario_key'].eq(row['scenario_key']).all(), 'event_fact scenario_key must match dim_scenario')
    return dim


def validate_reconciliation(event_fact: pd.DataFrame, horizon_fact: pd.DataFrame) -> None:
    derived = (
        event_fact.groupby('horizon_id')
        .apply(
            lambda frame: pd.Series(
                {
                    'candidate_count': int(len(frame)),
                    'eligible_candidate_count': int(frame['is_eligible_candidate'].sum()),
                    'selected_event_count': int(frame['selected_for_review'].sum()),
                    'actual_severe_selected_count': int(
                        (frame['selected_for_review'] & frame['actual_is_departure_severe_delay']).sum()
                    ),
                    'actual_severe_candidate_count': int(
                        (frame['is_eligible_candidate'] & frame['actual_is_departure_severe_delay']).sum()
                    ),
                    'selected_probability_score_sum': float(
                        frame.loc[frame['selected_for_review'], 'objective_contribution'].fillna(0).sum()
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    merged = horizon_fact.merge(derived, on='horizon_id', suffixes=('_source', '_derived'))
    for metric in [
        'candidate_count',
        'eligible_candidate_count',
        'selected_event_count',
        'actual_severe_selected_count',
        'actual_severe_candidate_count',
    ]:
        ensure(
            bool((merged[f'{metric}_source'] == merged[f'{metric}_derived']).all()),
            f'event-to-horizon reconciliation failed for {metric}',
        )
    ensure(
        bool((merged['selected_probability_score_sum_source'].round(12) == merged['selected_probability_score_sum_derived'].round(12)).all()),
        'event-to-horizon reconciliation failed for selected_probability_score_sum',
    )


def validate_manifest(manifest: dict[str, object]) -> None:
    ensure(int(manifest['page_count']) == 2, 'dashboard manifest must declare exactly two pages')
    pages = manifest['pages']
    ensure(isinstance(pages, list) and len(pages) == 2, 'dashboard manifest must contain two pages')


def build_artifacts(
    event_source: pd.DataFrame,
    horizon_source: pd.DataFrame,
    evaluation: dict[str, object],
    frozen_policy: dict[str, object],
    contract: dict[str, object],
    manifest: dict[str, object],
) -> ExportArtifacts:
    validate_manifest(manifest)
    validate_source_invariants(event_source, horizon_source, evaluation, frozen_policy)
    scenario_key = str(frozen_policy['policy_version'])
    event_fact = build_event_fact(event_source, scenario_key, contract)
    validate_dimension_conflicts(event_fact)
    horizon_fact = build_horizon_fact(horizon_source, scenario_key, contract)
    validate_reconciliation(event_fact, horizon_fact)
    dim_date_hour = build_dim_date_hour(horizon_fact, contract)
    dim_station = build_dim_station(event_fact, contract)
    dim_train_service = build_dim_train_service(event_fact, contract)
    dim_scenario = build_dim_scenario(event_fact, frozen_policy, contract)
    ensure(event_fact['horizon_id'].isin(dim_date_hour['horizon_id']).all(), 'every event_fact row must join to dim_date_hour')
    ensure(horizon_fact['horizon_id'].isin(dim_date_hour['horizon_id']).all(), 'every horizon_fact row must join to dim_date_hour')
    ensure(event_fact['station_id'].isin(dim_station['station_id']).all(), 'every event_fact row must join to dim_station')
    ensure(event_fact['train_service_key'].isin(dim_train_service['train_service_key']).all(), 'every event_fact row must join to dim_train_service')
    ensure(horizon_fact['scenario_key'].isin(dim_scenario['scenario_key']).all(), 'every horizon_fact row must join to dim_scenario')
    return ExportArtifacts(
        event_fact=event_fact,
        horizon_fact=horizon_fact,
        dim_date_hour=dim_date_hour,
        dim_station=dim_station,
        dim_train_service=dim_train_service,
        dim_scenario=dim_scenario,
    )


def persist_artifacts(artifacts: ExportArtifacts, output_dir: Path) -> None:
    write_parquet(artifacts.event_fact, output_dir / 'fact_event_decision.parquet')
    write_parquet(artifacts.horizon_fact, output_dir / 'fact_horizon_summary.parquet')
    write_parquet(artifacts.dim_date_hour, output_dir / 'dim_date_hour.parquet')
    write_parquet(artifacts.dim_station, output_dir / 'dim_station.parquet')
    write_parquet(artifacts.dim_train_service, output_dir / 'dim_train_service.parquet')
    write_parquet(artifacts.dim_scenario, output_dir / 'dim_scenario.parquet')


def export_power_bi_semantic_dataset(
    *,
    event_source_path: Path = EVENT_SOURCE_PATH,
    horizon_source_path: Path = HORIZON_SOURCE_PATH,
    evaluation_source_path: Path = EVALUATION_SOURCE_PATH,
    frozen_policy_path: Path = FROZEN_POLICY_PATH,
    semantic_contract_path: Path = SEMANTIC_CONTRACT_PATH,
    dashboard_manifest_path: Path = DASHBOARD_MANIFEST_PATH,
    output_dir: Path = POWER_BI_DIR,
) -> ExportArtifacts:
    event_source = read_parquet(event_source_path)
    horizon_source = read_parquet(horizon_source_path)
    evaluation = load_json(evaluation_source_path)
    frozen_policy = load_json(frozen_policy_path)
    contract = load_json(semantic_contract_path)
    manifest = load_json(dashboard_manifest_path)
    artifacts = build_artifacts(event_source, horizon_source, evaluation, frozen_policy, contract, manifest)
    persist_artifacts(artifacts, output_dir)
    return artifacts


def main() -> None:
    export_power_bi_semantic_dataset()


if __name__ == '__main__':
    main()

