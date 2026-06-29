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

import hashlib
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
POLICY_COMPARISON_SOURCE_PATH: Final[Path] = OPTIMIZATION_FINAL_DIR / 'policy_comparison.parquet'
HORIZON_POLICY_METRICS_SOURCE_PATH: Final[Path] = OPTIMIZATION_FINAL_DIR / 'horizon_policy_metrics.parquet'
EVALUATION_SOURCE_PATH: Final[Path] = OPTIMIZATION_FINAL_DIR / 'evaluation.json'
SEMANTIC_CONTRACT_PATH: Final[Path] = POWER_BI_DIR / 'semantic_contract.json'
DASHBOARD_MANIFEST_PATH: Final[Path] = POWER_BI_DIR / 'dashboard_mvp_manifest.json'
SOURCE_MONTH_PATH: Final[Path] = REPO_ROOT / 'data' / 'source' / 'data-2025-03.parquet'
UNKNOWN_STATION_LABEL: Final[str] = 'Unknown station'
UNKNOWN_LABEL: Final[str] = 'Unknown'
FINAL_MODE: Final[str] = 'final'
TEST_SPLIT: Final[str] = 'test'


SOLVER_STATUS_CODE_MAP: Final[dict[str, int]] = {
    'OPTIMAL': 2,
    'DETERMINISTIC': 1,
}
POLICY_DISPLAY_MAP: Final[dict[str, tuple[str, int]]] = {
    'random': ('Random', 1),
    'ml_first': ('ML-first', 2),
    'constrained_greedy': ('Constrained greedy', 3),
    'gurobi_soft_station_penalty': ('Gurobi', 4),
}
PAIRWISE_COMPARATORS: Final[tuple[str, ...]] = ('random', 'ml_first', 'constrained_greedy')


def coerce_solver_status(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors='coerce')
    missing = numeric.isna()
    if missing.any():
        mapped = series.astype('string').str.upper().map(SOLVER_STATUS_CODE_MAP)
        numeric = numeric.where(~missing, mapped)
    ensure(not numeric.isna().any(), 'solver_status contains unsupported values')
    return numeric.astype('Int64')


@dataclass(frozen=True)
class ExportArtifacts:
    event_fact: pd.DataFrame
    horizon_fact: pd.DataFrame
    dim_date_hour: pd.DataFrame
    dim_station: pd.DataFrame
    dim_train_service: pd.DataFrame
    dim_scenario: pd.DataFrame
    policy_comparison_fact: pd.DataFrame
    horizon_policy_metrics_fact: pd.DataFrame
    policy_pairwise_summary_fact: pd.DataFrame


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


def policy_version_value(frozen_policy: dict[str, object]) -> str:
    if 'policy_version' in frozen_policy:
        return str(frozen_policy['policy_version'])
    return str(frozen_policy['optimization_policy_version'])


def model_name_value(frozen_policy: dict[str, object]) -> str:
    if 'model_name' in frozen_policy:
        return str(frozen_policy['model_name'])
    return str(frozen_policy['scoring_model_name'])


def model_version_value(frozen_policy: dict[str, object]) -> str:
    if 'model_version' in frozen_policy:
        return str(frozen_policy['model_version'])
    return str(frozen_policy['scoring_model_version'])



def load_station_name_lookup() -> pd.DataFrame:
    connection = duckdb.connect()
    try:
        query = f"""
            select
                cast(eva as varchar) as station_id,
                min(station_name) as station_name
            from read_parquet('{SOURCE_MONTH_PATH.as_posix()}')
            where eva is not null
              and station_name is not null
              and trim(station_name) <> ''
            group by 1
        """
        lookup = connection.execute(query).fetch_df()
    finally:
        connection.close()
    lookup['station_id'] = lookup['station_id'].astype('string')
    lookup['station_name'] = lookup['station_name'].astype('string')
    validate_unique(lookup, 'station_id', 'station_name_lookup')
    return lookup

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
    normalized['train_service_key'] = normalized['train_service_key'].where(normalized['train_service_key'].notna(), normalized['journey_id'].astype('string'))
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
    normalized['station_name'] = normalized['station_name'].astype('string')
    missing_station_name = normalized['station_name'].isna()
    if missing_station_name.any():
        station_lookup = load_station_name_lookup()
        normalized = normalized.merge(station_lookup, on='station_id', how='left', suffixes=('', '_lookup'))
        normalized['station_name'] = normalized['station_name'].where(~missing_station_name, normalized['station_name_lookup'])
        normalized = normalized.drop(columns=['station_name_lookup'])
    normalized['station_name'] = normalized['station_name'].fillna(UNKNOWN_STATION_LABEL)
    normalized['train_type'] = normalized['train_type'].astype('string').fillna(UNKNOWN_LABEL)
    normalized['line_number'] = normalized['line_number'].astype('string').fillna('Not provided in source')
    if 'service_class' in normalized.columns:
        service_class = normalized['service_class']
    else:
        service_class = normalized['service_class_y'].where(normalized['service_class_y'].notna(), normalized['service_class_x'])
    normalized['service_class'] = service_class.astype('string').fillna(UNKNOWN_LABEL)
    normalized['eligibility_reason'] = normalized['eligibility_reason'].astype('string').fillna(UNKNOWN_LABEL)
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
    if 'model_name' in normalized.columns:
        normalized['model_name'] = normalized['model_name'].astype('string')
    else:
        normalized['model_name'] = normalized['scoring_model_name'].astype('string')
    if 'model_version' in normalized.columns:
        normalized['model_version'] = normalized['model_version'].astype('string')
    else:
        normalized['model_version'] = normalized['scoring_model_version'].astype('string')
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
    scenario_key = policy_version_value(frozen_policy)
    event_frame = normalize_event_source(event_frame, scenario_key)
    horizon_frame = normalize_horizon_source(horizon_frame, scenario_key)
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
            'service_class',
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
    validate_non_null(event_frame, 'station_id', 'event_source')
    validate_non_null(event_frame, 'train_service_key', 'event_source')
    validate_non_null(event_frame, 'horizon_id', 'event_source')
    validate_unique(event_frame, 'stop_event_key', 'event_source')
    validate_unique(horizon_frame, 'horizon_id', 'horizon_source')
    validate_horizon_mapping(event_frame)
    ensure(policy_version_value(frozen_policy).strip(), 'frozen policy must contain policy version')
    evaluation_policy = evaluation.get('frozen_policy', evaluation)

    event_run_id = str(unique_value(event_frame, 'optimization_run_id', 'event_source'))
    horizon_run_id = str(unique_value(horizon_frame, 'optimization_run_id', 'horizon_source'))
    ensure(event_run_id == horizon_run_id, 'event and horizon optimization_run_id must match')

    event_model_name = str(unique_value(event_frame, 'model_name', 'event_source'))
    horizon_model_name = str(unique_value(horizon_frame, 'model_name', 'horizon_source'))
    event_model_version = str(unique_value(event_frame, 'model_version', 'event_source'))
    horizon_model_version = str(unique_value(horizon_frame, 'model_version', 'horizon_source'))
    ensure(event_model_name == horizon_model_name == model_name_value(frozen_policy), 'model_name must match across artifacts')
    ensure(event_model_version == horizon_model_version == model_version_value(frozen_policy), 'model_version must match across artifacts')

    event_capacity_scenario = str(unique_value(event_frame, 'capacity_scenario', 'event_source'))
    horizon_capacity_scenario = str(unique_value(horizon_frame, 'capacity_scenario', 'horizon_source'))
    ensure(event_capacity_scenario == horizon_capacity_scenario == str(frozen_policy['capacity_scenario']), 'capacity_scenario must match across artifacts')
    if 'capacity_scenario' in evaluation_policy:
        ensure(event_capacity_scenario == str(evaluation_policy['capacity_scenario']), 'capacity_scenario must match evaluation metadata')

    event_capacity_per_hour = int(unique_value(event_frame, 'capacity_per_hour', 'event_source'))
    horizon_capacity_per_hour = int(unique_value(horizon_frame, 'capacity_per_hour', 'horizon_source'))
    ensure(event_capacity_per_hour == horizon_capacity_per_hour == int(frozen_policy['capacity_per_hour']), 'capacity_per_hour must match across artifacts')
    if 'capacity_per_hour' in evaluation_policy:
        ensure(event_capacity_per_hour == int(evaluation_policy['capacity_per_hour']), 'capacity_per_hour must match evaluation metadata')

    event_min_probability = float(unique_value(event_frame, 'minimum_candidate_probability', 'event_source'))
    ensure(event_min_probability == float(frozen_policy['minimum_candidate_probability']), 'minimum_candidate_probability must match across artifacts')
    if 'minimum_candidate_probability' in evaluation_policy:
        ensure(event_min_probability == float(evaluation_policy['minimum_candidate_probability']), 'minimum_candidate_probability must match evaluation metadata')

    event_selected_threshold = float(unique_value(event_frame, 'selected_threshold', 'event_source'))
    ensure(event_selected_threshold == float(frozen_policy['selected_threshold']), 'selected_threshold must match frozen policy')
    if 'horizon_count' in evaluation:
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


def probability_bin_floor(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors='coerce')
    return (numeric.fillna(-1).floordiv(0.05) * 0.05).where(numeric.notna())

def probability_band_label(value: object) -> str:
    if pd.isna(value):
        return UNKNOWN_LABEL
    probability = float(value)
    if probability < 0.10:
        return '00-10%'
    if probability < 0.20:
        return '10-20%'
    if probability < 0.30:
        return '20-30%'
    if probability < 0.40:
        return '30-40%'
    if probability < 0.50:
        return '40-50%'
    if probability < 0.60:
        return '50-60%'
    if probability < 0.70:
        return '60-70%'
    if probability < 0.80:
        return '70-80%'
    if probability < 0.90:
        return '80-90%'
    return '90-100%'

def probability_band_sort(value: object) -> int:
    if pd.isna(value):
        return 99
    return min(10, int(float(value) * 10) + 1)

def build_event_fact(event_source: pd.DataFrame, scenario_key: str, contract: dict[str, object]) -> pd.DataFrame:
    normalized = normalize_event_source(event_source, scenario_key)
    normalized['predicted_severe_delay_probability (bins)'] = probability_bin_floor(normalized['predicted_severe_delay_probability'])
    normalized['Review Eligibility'] = normalized['is_eligible_candidate'].map({True: 'Can be reviewed', False: 'Not reviewable'}).fillna('Not reviewable')
    normalized['Review Decision'] = normalized.apply(
        lambda row: 'Not reviewable' if not bool(row['is_eligible_candidate']) else ('Chosen for review' if bool(row['selected_for_review']) else 'Not chosen for review'),
        axis=1,
    )
    normalized['Actual Outcome'] = normalized['actual_is_departure_severe_delay'].map({True: 'Became severe', False: 'Did not become severe'}).fillna('Outcome unavailable')
    normalized['Predicted Risk Band'] = normalized['predicted_severe_delay_probability'].map(probability_band_label)
    normalized['Predicted Risk Band Sort'] = normalized['predicted_severe_delay_probability'].map(probability_band_sort).astype('Int64')
    columns = ordered_columns(contract, 'fact_event_decision')
    event_fact = normalized.loc[:, columns].copy()
    event_fact['hour_of_day'] = event_fact['hour_of_day'].astype('Int64')
    event_fact['capacity_per_hour'] = event_fact['capacity_per_hour'].astype('Int64')
    event_fact['candidate_priority_rank'] = event_fact['candidate_priority_rank'].astype('Int64')
    event_fact['selection_rank'] = event_fact['selection_rank'].astype('Int64')
    event_fact['solver_status'] = coerce_solver_status(event_fact['solver_status'])
    event_fact['Predicted Risk Band Sort'] = event_fact['Predicted Risk Band Sort'].astype('Int64')
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
        if column_name == 'solver_status':
            horizon_fact[column_name] = coerce_solver_status(horizon_fact[column_name])
        else:
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
        f"policy {policy_version_value(frozen_policy)}"
    )
    row = {
        'scenario_key': policy_version_value(frozen_policy),
        'capacity_scenario': str(frozen_policy['capacity_scenario']),
        'capacity_per_hour': int(frozen_policy['capacity_per_hour']),
        'minimum_candidate_probability': float(frozen_policy['minimum_candidate_probability']),
        'model_name': model_name_value(frozen_policy),
        'model_version': model_version_value(frozen_policy),
        'selected_threshold': float(frozen_policy['selected_threshold']),
        'policy_version': policy_version_value(frozen_policy),
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


def normalize_policy_display(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized['policy_name'] = normalized['policy_name'].astype('string')
    normalized['policy_display_name'] = normalized['policy_name'].map(lambda value: POLICY_DISPLAY_MAP[str(value)][0]).astype('string')
    normalized['policy_sort_order'] = normalized['policy_name'].map(lambda value: POLICY_DISPLAY_MAP[str(value)][1]).astype('Int64')
    return normalized

def fingerprint_capacity_group(frame: pd.DataFrame) -> str:
    ordered = frame.sort_values('horizon_id')[['horizon_id', 'candidate_count', 'eligible_candidate_count', 'feasible_selection_target', 'actual_severe_candidate_count']]
    return hashlib.sha256(ordered.to_json(orient='records').encode('utf-8')).hexdigest()

def validate_policy_completeness(frame: pd.DataFrame, frame_name: str) -> None:
    expected = set(POLICY_DISPLAY_MAP)
    for capacity, group in frame.groupby('capacity_per_hour', sort=True):
        actual = set(group['policy_name'].astype(str).unique().tolist())
        ensure(actual == expected, f'{frame_name} capacity {capacity} must contain policies {sorted(expected)}')

def validate_horizon_policy_metrics_source(horizon_policy_metrics: pd.DataFrame, evaluation: dict[str, object], frozen_policy: dict[str, object]) -> pd.DataFrame:
    require_columns(horizon_policy_metrics, [
        'optimization_run_id', 'execution_mode', 'policy_name', 'calendar_date', 'hour_of_day', 'horizon_id',
        'capacity_scenario', 'capacity_per_hour', 'feasible_selection_target', 'candidate_count', 'eligible_candidate_count',
        'selected_event_count', 'candidate_shortage_count', 'unused_capacity', 'selected_probability_score_sum',
        'actual_severe_selected_count', 'selected_severe_event_count', 'actual_severe_candidate_count', 'candidate_prevalence',
        'precision_at_capacity', 'severe_delay_coverage', 'lift_over_candidate_prevalence', 'distinct_selected_stations',
        'max_selected_same_station_in_horizon', 'station_concentration_excess_total', 'penalty_active_in_horizon', 'solver_status',
        'scoring_model_name', 'scoring_model_version', 'optimization_policy_name', 'optimization_policy_version',
        'preferred_station_load_per_station_hour', 'frozen_station_excess_penalty_lambda', 'optimized_at', 'selected_stop_event_key_hash',
    ], 'horizon_policy_metrics_source')
    normalized = normalize_policy_display(horizon_policy_metrics.copy())
    normalized['execution_mode'] = normalized['execution_mode'].astype('string')
    ensure(bool(normalized['execution_mode'].eq(FINAL_MODE).all()), 'horizon_policy_metrics execution_mode must be final')
    normalized['optimization_run_id'] = normalized['optimization_run_id'].astype('string')
    normalized['scoring_model_name'] = normalized['scoring_model_name'].astype('string')
    normalized['scoring_model_version'] = normalized['scoring_model_version'].astype('string')
    normalized['optimization_policy_version'] = normalized['optimization_policy_version'].astype('string')
    normalized['optimized_at'] = normalized['optimized_at'].astype('string')
    normalized['candidate_pool_fingerprint'] = ''
    validate_policy_completeness(normalized, 'horizon_policy_metrics_source')
    ensure(evaluation.get('mode') == FINAL_MODE, 'evaluation metadata mode must be final')
    ensure(str(unique_value(normalized, 'scoring_model_name', 'horizon_policy_metrics_source')) == model_name_value(frozen_policy), 'scoring_model_name must match frozen policy')
    ensure(str(unique_value(normalized, 'scoring_model_version', 'horizon_policy_metrics_source')) == model_version_value(frozen_policy), 'scoring_model_version must match frozen policy')
    ensure(str(unique_value(normalized, 'optimization_policy_version', 'horizon_policy_metrics_source')) == policy_version_value(frozen_policy), 'optimization_policy_version must match frozen policy')
    for capacity, group in normalized.groupby('capacity_per_hour', sort=True):
        reference = None
        for _, policy_group in group.groupby('policy_name', sort=True):
            policy_view = policy_group.sort_values('horizon_id')[['horizon_id', 'candidate_count', 'eligible_candidate_count', 'feasible_selection_target', 'actual_severe_candidate_count']].reset_index(drop=True)
            if reference is None:
                reference = policy_view
            else:
                ensure(reference.equals(policy_view), f'horizon_policy_metrics capacity {capacity} must share candidate-pool invariants across policies')
        normalized.loc[group.index, 'candidate_pool_fingerprint'] = fingerprint_capacity_group(reference)
    return normalized

def validate_policy_comparison_source(policy_comparison: pd.DataFrame, horizon_policy_metrics: pd.DataFrame) -> pd.DataFrame:
    require_columns(policy_comparison, [
        'execution_mode', 'policy_name', 'capacity_scenario', 'capacity_per_hour', 'selected_event_count', 'selected_severe_event_count',
        'precision_at_capacity', 'severe_delay_coverage', 'lift_vs_random', 'expected_risk_score_captured', 'distinct_stations_covered',
        'max_selected_same_station_in_horizon', 'station_concentration_excess_total', 'unused_capacity_total', 'binding_horizon_count',
        'binding_horizon_rate', 'candidate_shortage_horizon_count', 'candidate_shortage_horizon_rate', 'median_feasible_selection_target',
        'preferred_station_load_per_station_hour', 'frozen_station_excess_penalty_lambda',
    ], 'policy_comparison_source')
    normalized = normalize_policy_display(policy_comparison.copy())
    normalized['execution_mode'] = normalized['execution_mode'].astype('string')
    ensure(bool(normalized['execution_mode'].eq(FINAL_MODE).all()), 'policy_comparison execution_mode must be final')
    validate_policy_completeness(normalized, 'policy_comparison_source')
    run_lookup = horizon_policy_metrics[['capacity_per_hour', 'optimization_run_id', 'candidate_pool_fingerprint', 'scoring_model_name', 'scoring_model_version', 'optimization_policy_version', 'optimized_at']].drop_duplicates()
    validate_unique(run_lookup, 'capacity_per_hour', 'comparison_run_lookup')
    normalized = normalized.merge(run_lookup, on='capacity_per_hour', how='left')
    ensure(not normalized['optimization_run_id'].isna().any(), 'policy_comparison must align to horizon comparison run metadata')
    normalized['horizon_count'] = normalized['binding_horizon_count'].astype('Int64') + normalized['candidate_shortage_horizon_count'].astype('Int64')
    normalized['mean_station_concentration_excess_per_horizon'] = normalized['station_concentration_excess_total'] / normalized['horizon_count'].where(normalized['horizon_count'] != 0)
    normalized['mean_unused_capacity_per_horizon'] = normalized['unused_capacity_total'] / normalized['horizon_count'].where(normalized['horizon_count'] != 0)
    return normalized

def build_policy_comparison_fact(policy_comparison: pd.DataFrame, horizon_policy_metrics: pd.DataFrame, contract: dict[str, object]) -> pd.DataFrame:
    normalized = validate_policy_comparison_source(policy_comparison, horizon_policy_metrics)
    fact = normalized.loc[:, ordered_columns(contract, 'fact_policy_comparison')].copy()
    for column_name in ['policy_sort_order', 'capacity_per_hour', 'horizon_count', 'selected_event_count', 'selected_severe_event_count', 'distinct_stations_covered', 'max_selected_same_station_in_horizon', 'unused_capacity_total', 'binding_horizon_count', 'candidate_shortage_horizon_count', 'preferred_station_load_per_station_hour']:
        fact[column_name] = fact[column_name].astype('Int64')
    validate_frame_against_contract(fact, contract, 'fact_policy_comparison')
    ensure(not fact.duplicated(['optimization_run_id', 'capacity_per_hour', 'policy_name']).any(), 'fact_policy_comparison grain must be unique')
    return fact

def build_horizon_policy_metrics_fact(horizon_policy_metrics: pd.DataFrame, evaluation: dict[str, object], frozen_policy: dict[str, object], contract: dict[str, object]) -> pd.DataFrame:
    normalized = validate_horizon_policy_metrics_source(horizon_policy_metrics, evaluation, frozen_policy)
    fact = normalized.loc[:, ordered_columns(contract, 'fact_horizon_policy_metrics')].copy()
    for column_name in ['policy_sort_order', 'hour_of_day', 'capacity_per_hour', 'feasible_selection_target', 'candidate_count', 'eligible_candidate_count', 'selected_event_count', 'candidate_shortage_count', 'unused_capacity', 'actual_severe_selected_count', 'selected_severe_event_count', 'actual_severe_candidate_count', 'distinct_selected_stations', 'max_selected_same_station_in_horizon', 'preferred_station_load_per_station_hour']:
        fact[column_name] = fact[column_name].astype('Int64')
    validate_frame_against_contract(fact, contract, 'fact_horizon_policy_metrics')
    ensure(not fact.duplicated(['optimization_run_id', 'capacity_per_hour', 'policy_name', 'horizon_id']).any(), 'fact_horizon_policy_metrics grain must be unique')
    return fact

def classify_pairwise_outcome(gurobi_row: pd.Series, comparator_row: pd.Series) -> str:
    gurobi_tuple = (int(gurobi_row['actual_severe_selected_count']), round(float(gurobi_row['selected_probability_score_sum']), 12), -round(float(gurobi_row['station_concentration_excess_total']), 12), -int(gurobi_row['unused_capacity']))
    comparator_tuple = (int(comparator_row['actual_severe_selected_count']), round(float(comparator_row['selected_probability_score_sum']), 12), -round(float(comparator_row['station_concentration_excess_total']), 12), -int(comparator_row['unused_capacity']))
    if gurobi_tuple > comparator_tuple:
        return 'win'
    if gurobi_tuple < comparator_tuple:
        return 'loss'
    return 'tie'

def build_policy_pairwise_summary_fact(policy_fact: pd.DataFrame, horizon_fact: pd.DataFrame, contract: dict[str, object]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for capacity in sorted(policy_fact['capacity_per_hour'].dropna().unique().tolist()):
        capacity_policy = policy_fact.loc[policy_fact['capacity_per_hour'] == capacity].copy()
        capacity_horizon = horizon_fact.loc[horizon_fact['capacity_per_hour'] == capacity].copy()
        gurobi_policy = capacity_policy.loc[capacity_policy['policy_name'] == 'gurobi_soft_station_penalty'].iloc[0]
        gurobi_horizon = capacity_horizon.loc[capacity_horizon['policy_name'] == 'gurobi_soft_station_penalty'].set_index('horizon_id')
        for comparator in PAIRWISE_COMPARATORS:
            comparator_policy = capacity_policy.loc[capacity_policy['policy_name'] == comparator].iloc[0]
            comparator_horizon = capacity_horizon.loc[capacity_horizon['policy_name'] == comparator].set_index('horizon_id')
            aligned = gurobi_horizon.join(comparator_horizon, lsuffix='_gurobi', rsuffix='_comparator', how='inner')
            outcomes: list[str] = []
            for _, row in aligned.iterrows():
                gurobi_row = row[[name for name in aligned.columns if name.endswith('_gurobi')]].rename(lambda value: value[:-7])
                comparator_row = row[[name for name in aligned.columns if name.endswith('_comparator')]].rename(lambda value: value[:-11])
                outcomes.append(classify_pairwise_outcome(gurobi_row, comparator_row))
            rows.append({
                'optimization_run_id': str(gurobi_policy['optimization_run_id']),
                'candidate_pool_fingerprint': str(gurobi_policy['candidate_pool_fingerprint']),
                'scoring_model_name': str(gurobi_policy['scoring_model_name']),
                'scoring_model_version': str(gurobi_policy['scoring_model_version']),
                'optimization_policy_version': str(gurobi_policy['optimization_policy_version']),
                'optimized_at': str(gurobi_policy['optimized_at']),
                'execution_mode': FINAL_MODE,
                'capacity_per_hour': int(capacity),
                'reference_policy_name': 'gurobi_soft_station_penalty',
                'reference_policy_display_name': 'Gurobi',
                'comparator_policy_name': comparator,
                'comparator_policy_display_name': POLICY_DISPLAY_MAP[comparator][0],
                'compared_horizon_count': int(len(aligned)),
                'win_horizon_count': int(sum(item == 'win' for item in outcomes)),
                'tie_horizon_count': int(sum(item == 'tie' for item in outcomes)),
                'loss_horizon_count': int(sum(item == 'loss' for item in outcomes)),
                'selected_set_match_rate': float((aligned['selected_stop_event_key_hash_gurobi'] == aligned['selected_stop_event_key_hash_comparator']).mean()) if len(aligned) else None,
                'gurobi_selected_severe_event_count': int(gurobi_policy['selected_severe_event_count']),
                'comparator_selected_severe_event_count': int(comparator_policy['selected_severe_event_count']),
                'selected_severe_event_count_delta': int(gurobi_policy['selected_severe_event_count']) - int(comparator_policy['selected_severe_event_count']),
                'gurobi_precision_at_capacity': float(gurobi_policy['precision_at_capacity']) if pd.notna(gurobi_policy['precision_at_capacity']) else None,
                'comparator_precision_at_capacity': float(comparator_policy['precision_at_capacity']) if pd.notna(comparator_policy['precision_at_capacity']) else None,
                'precision_at_capacity_delta': float(gurobi_policy['precision_at_capacity']) - float(comparator_policy['precision_at_capacity']) if pd.notna(gurobi_policy['precision_at_capacity']) and pd.notna(comparator_policy['precision_at_capacity']) else None,
                'gurobi_severe_delay_coverage': float(gurobi_policy['severe_delay_coverage']) if pd.notna(gurobi_policy['severe_delay_coverage']) else None,
                'comparator_severe_delay_coverage': float(comparator_policy['severe_delay_coverage']) if pd.notna(comparator_policy['severe_delay_coverage']) else None,
                'severe_delay_coverage_delta': float(gurobi_policy['severe_delay_coverage']) - float(comparator_policy['severe_delay_coverage']) if pd.notna(gurobi_policy['severe_delay_coverage']) and pd.notna(comparator_policy['severe_delay_coverage']) else None,
                'gurobi_mean_station_concentration_excess_per_horizon': float(gurobi_policy['mean_station_concentration_excess_per_horizon']) if pd.notna(gurobi_policy['mean_station_concentration_excess_per_horizon']) else None,
                'comparator_mean_station_concentration_excess_per_horizon': float(comparator_policy['mean_station_concentration_excess_per_horizon']) if pd.notna(comparator_policy['mean_station_concentration_excess_per_horizon']) else None,
                'mean_station_concentration_excess_per_horizon_delta': float(gurobi_policy['mean_station_concentration_excess_per_horizon']) - float(comparator_policy['mean_station_concentration_excess_per_horizon']) if pd.notna(gurobi_policy['mean_station_concentration_excess_per_horizon']) and pd.notna(comparator_policy['mean_station_concentration_excess_per_horizon']) else None,
                'gurobi_mean_unused_capacity_per_horizon': float(gurobi_policy['mean_unused_capacity_per_horizon']) if pd.notna(gurobi_policy['mean_unused_capacity_per_horizon']) else None,
                'comparator_mean_unused_capacity_per_horizon': float(comparator_policy['mean_unused_capacity_per_horizon']) if pd.notna(comparator_policy['mean_unused_capacity_per_horizon']) else None,
                'mean_unused_capacity_per_horizon_delta': float(gurobi_policy['mean_unused_capacity_per_horizon']) - float(comparator_policy['mean_unused_capacity_per_horizon']) if pd.notna(gurobi_policy['mean_unused_capacity_per_horizon']) and pd.notna(comparator_policy['mean_unused_capacity_per_horizon']) else None,
            })
    fact = pd.DataFrame(rows).loc[:, ordered_columns(contract, 'fact_policy_pairwise_summary')].copy()
    for column_name in ['capacity_per_hour', 'compared_horizon_count', 'win_horizon_count', 'tie_horizon_count', 'loss_horizon_count', 'gurobi_selected_severe_event_count', 'comparator_selected_severe_event_count', 'selected_severe_event_count_delta']:
        fact[column_name] = fact[column_name].astype('Int64')
    validate_frame_against_contract(fact, contract, 'fact_policy_pairwise_summary')
    ensure(bool((fact['win_horizon_count'] + fact['tie_horizon_count'] + fact['loss_horizon_count'] == fact['compared_horizon_count']).all()), 'fact_policy_pairwise_summary win/tie/loss counts must reconcile')
    return fact

def validate_manifest(manifest: dict[str, object]) -> None:
    ensure(int(manifest['page_count']) == 4, 'dashboard manifest must declare exactly four pages')
    pages = manifest['pages']
    ensure(isinstance(pages, list) and len(pages) == 4, 'dashboard manifest must contain four pages')


def build_artifacts(
    event_source: pd.DataFrame,
    horizon_source: pd.DataFrame,
    policy_comparison_source: pd.DataFrame,
    horizon_policy_metrics_source: pd.DataFrame,
    evaluation: dict[str, object],
    frozen_policy: dict[str, object],
    contract: dict[str, object],
    manifest: dict[str, object],
) -> ExportArtifacts:
    validate_manifest(manifest)
    validate_source_invariants(event_source, horizon_source, evaluation, frozen_policy)
    scenario_key = policy_version_value(frozen_policy)
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
    horizon_policy_metrics_fact = build_horizon_policy_metrics_fact(horizon_policy_metrics_source, evaluation, frozen_policy, contract)
    policy_comparison_fact = build_policy_comparison_fact(policy_comparison_source, horizon_policy_metrics_fact, contract)
    policy_pairwise_summary_fact = build_policy_pairwise_summary_fact(policy_comparison_fact, horizon_policy_metrics_fact, contract)
    return ExportArtifacts(
        event_fact=event_fact,
        horizon_fact=horizon_fact,
        dim_date_hour=dim_date_hour,
        dim_station=dim_station,
        dim_train_service=dim_train_service,
        dim_scenario=dim_scenario,
        policy_comparison_fact=policy_comparison_fact,
        horizon_policy_metrics_fact=horizon_policy_metrics_fact,
        policy_pairwise_summary_fact=policy_pairwise_summary_fact,
    )


def persist_artifacts(artifacts: ExportArtifacts, output_dir: Path) -> None:
    write_parquet(artifacts.event_fact, output_dir / 'fact_event_decision.parquet')
    write_parquet(artifacts.horizon_fact, output_dir / 'fact_horizon_summary.parquet')
    write_parquet(artifacts.dim_date_hour, output_dir / 'dim_date_hour.parquet')
    write_parquet(artifacts.dim_station, output_dir / 'dim_station.parquet')
    write_parquet(artifacts.dim_train_service, output_dir / 'dim_train_service.parquet')
    write_parquet(artifacts.dim_scenario, output_dir / 'dim_scenario.parquet')
    write_parquet(artifacts.policy_comparison_fact, output_dir / 'fact_policy_comparison.parquet')
    write_parquet(artifacts.horizon_policy_metrics_fact, output_dir / 'fact_horizon_policy_metrics.parquet')
    write_parquet(artifacts.policy_pairwise_summary_fact, output_dir / 'fact_policy_pairwise_summary.parquet')


def export_power_bi_semantic_dataset(
    *,
    event_source_path: Path = EVENT_SOURCE_PATH,
    horizon_source_path: Path = HORIZON_SOURCE_PATH,
    policy_comparison_source_path: Path = POLICY_COMPARISON_SOURCE_PATH,
    horizon_policy_metrics_source_path: Path = HORIZON_POLICY_METRICS_SOURCE_PATH,
    evaluation_source_path: Path = EVALUATION_SOURCE_PATH,
    frozen_policy_path: Path = FROZEN_POLICY_PATH,
    semantic_contract_path: Path = SEMANTIC_CONTRACT_PATH,
    dashboard_manifest_path: Path = DASHBOARD_MANIFEST_PATH,
    output_dir: Path = POWER_BI_DIR,
) -> ExportArtifacts:
    event_source = read_parquet(event_source_path)
    horizon_source = read_parquet(horizon_source_path)
    policy_comparison_source = read_parquet(policy_comparison_source_path)
    horizon_policy_metrics_source = read_parquet(horizon_policy_metrics_source_path)
    evaluation = load_json(evaluation_source_path)
    frozen_policy = load_json(frozen_policy_path)
    contract = load_json(semantic_contract_path)
    manifest = load_json(dashboard_manifest_path)
    artifacts = build_artifacts(event_source, horizon_source, policy_comparison_source, horizon_policy_metrics_source, evaluation, frozen_policy, contract, manifest)
    persist_artifacts(artifacts, output_dir)
    return artifacts


def main() -> None:
    export_power_bi_semantic_dataset()


if __name__ == '__main__':
    main()

