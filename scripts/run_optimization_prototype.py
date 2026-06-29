"""# @meta
# type: script
# distribution_tier: starter_kit
# scope: local
# domain: optimization
# tags:
# - optimization
# - gurobi
# - duckdb
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import duckdb
import gurobipy as gp
import pandas as pd
from gurobipy import GRB

REPO_ROOT = Path(__file__).resolve().parents[1]
ML_DIR = REPO_ROOT / 'data' / 'scoped' / 'ml'
OPTIMIZATION_DIR = REPO_ROOT / 'data' / 'scoped' / 'optimization'
CONFIG_DIR = REPO_ROOT / 'configs' / 'optimization'
POWER_BI_DIR = REPO_ROOT / 'data' / 'scoped' / 'power_bi'
SCORED_PATH = ML_DIR / 'scored_stop_events.parquet'
ML_EVALUATION_PATH = ML_DIR / 'evaluation.json'
SEARCH_CONFIG_PATH = CONFIG_DIR / 'optimization_policy_search_config.json'
FROZEN_POLICY_PATH = OPTIMIZATION_DIR / 'frozen_policy.json'
DASHBOARD_MANIFEST_PATH = POWER_BI_DIR / 'dashboard_mvp_manifest.json'
CANONICAL_PROBABILITY_FIELD = 'predicted_severe_delay_probability'
LEGACY_PROBABILITY_FIELD = 'predicted_probability'
DEFAULT_CAPACITY_PER_HOUR = 3
DEFAULT_CAPACITY_SCENARIO = 'hourly_capacity_3'
DEFAULT_POLICY_NAME = 'gurobi_soft_station_penalty'
DEVELOPMENT_MODE = 'development'
FINAL_MODE = 'final'
MODE_TO_SPLIT = {
    DEVELOPMENT_MODE: 'validation',
    FINAL_MODE: 'test',
}
POLICY_NAMES = ('random', 'ml_first', 'constrained_greedy', DEFAULT_POLICY_NAME)
ALLOWED_SOLVER_STATUS_OPTIMAL = 'OPTIMAL'
ALLOWED_SOLVER_STATUS_TIME_LIMIT_WITH_INCUMBENT = 'TIME_LIMIT_WITH_INCUMBENT'
ELIGIBILITY_REASON_ELIGIBLE = 'eligible'
ELIGIBILITY_REASON_BELOW_THRESHOLD = 'below_minimum_candidate_probability'
ELIGIBILITY_REASON_INVALID_PROBABILITY = 'invalid_probability'
ELIGIBILITY_REASON_DUPLICATE_KEY = 'duplicate_stop_event_key'
ELIGIBILITY_REASON_MISSING_REQUIRED_FIELD = 'missing_required_field'
REQUIRED_SCORED_FIELDS = (
    'stop_event_key',
    'journey_id',
    'service_date',
    'station_id',
    'train_type',
    'line_number',
    'prediction_split',
    'hour_of_day',
    'model_name',
    'model_version',
    'selected_threshold',
    'actual_is_departure_severe_delay',
)
OPTIONAL_ENRICHMENT_FIELDS = ('station_name', 'train_service_key', 'service_class')
RANDOM_SEED = 17
PREFERRED_STATION_LOAD_CANDIDATES = [1, 2]
ELIGIBLE_LAMBDAS = [0.05, 0.1, 0.2]
SCENARIO_CAPACITIES = [1, 3, 5, 10]


@dataclass(frozen=True)
class FrozenPolicy:
    optimization_policy_name: str
    optimization_policy_version: str
    execution_modes: list[str]
    solver_name: str
    solver_version: object
    canonical_probability_field: str
    threshold_source: str
    selected_threshold: float
    minimum_candidate_probability: float
    scoring_model_name: str
    scoring_model_version: str
    capacity_scenario: str
    capacity_per_hour: int
    preferred_station_load_per_station_hour: int
    diagnostic_station_excess_penalty_lambda: float
    eligible_frozen_station_excess_penalty_lambdas: list[float]
    frozen_station_excess_penalty_lambda: float
    feasible_selection_rule: str
    constraint_set: list[str]
    baseline_policies: list[str]
    tie_break_rule: list[str]
    scenario_capacities: list[int]
    metric_definitions: list[str]
    frozen_at: str


def build_search_config() -> dict[str, object]:
    return {
        'optimization_policy_name': DEFAULT_POLICY_NAME,
        'optimization_policy_version': '2026-06-29-v1',
        'canonical_tuning_capacity_per_hour': DEFAULT_CAPACITY_PER_HOUR,
        'scenario_capacities': SCENARIO_CAPACITIES,
        'preferred_station_load_per_station_hour_candidates': PREFERRED_STATION_LOAD_CANDIDATES,
        'diagnostic_station_excess_penalty_lambda': 0.0,
        'eligible_frozen_station_excess_penalty_lambdas': ELIGIBLE_LAMBDAS,
        'winner_selection_rule': [
            'selected_severe_event_count desc',
            'severe_delay_coverage desc',
            'station_concentration_excess_total asc',
            'distinct_stations_covered desc',
            'station_excess_penalty_lambda asc',
            'preferred_station_load_per_station_hour asc',
        ],
        'random_seed': RANDOM_SEED,
        'development_allowed_solver_statuses': [
            ALLOWED_SOLVER_STATUS_OPTIMAL,
            ALLOWED_SOLVER_STATUS_TIME_LIMIT_WITH_INCUMBENT,
        ],
        'final_allowed_solver_statuses': [
            ALLOWED_SOLVER_STATUS_OPTIMAL,
            ALLOWED_SOLVER_STATUS_TIME_LIMIT_WITH_INCUMBENT,
        ],
    }


def ensure_search_config() -> dict[str, object]:
    if SEARCH_CONFIG_PATH.exists():
        return json.loads(SEARCH_CONFIG_PATH.read_text(encoding='utf-8'))
    config = build_search_config()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SEARCH_CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding='utf-8')
    return config


def load_ml_metadata() -> dict[str, object]:
    metadata = json.loads(ML_EVALUATION_PATH.read_text(encoding='utf-8'))
    # ponytail: prefer current rebuilt ML threshold over stale frozen-policy remnants; add dedicated threshold registry only if multiple concurrent model lines appear.
    if 'selected_threshold' in metadata:
        metadata['selected_threshold'] = float(metadata['selected_threshold'])
    return metadata


def load_scored_rows() -> pd.DataFrame:
    connection = duckdb.connect()
    try:
        return connection.execute(f"select * from read_parquet('{SCORED_PATH.as_posix()}')").fetch_df()
    finally:
        connection.close()


def build_frozen_policy(
    *,
    metadata: dict[str, object],
    search_config: dict[str, object],
    preferred_station_load_per_station_hour: int,
    frozen_station_excess_penalty_lambda: float,
    capacity_per_hour: int = DEFAULT_CAPACITY_PER_HOUR,
    minimum_candidate_probability: float | None = None,
) -> dict[str, object]:
    selected_threshold = float(metadata['selected_threshold'])
    threshold = selected_threshold if minimum_candidate_probability is None else minimum_candidate_probability
    policy = FrozenPolicy(
        optimization_policy_name=str(search_config['optimization_policy_name']),
        optimization_policy_version=str(search_config['optimization_policy_version']),
        execution_modes=[DEVELOPMENT_MODE, FINAL_MODE],
        solver_name='gurobi',
        solver_version=gp.gurobi.version(),
        canonical_probability_field=CANONICAL_PROBABILITY_FIELD,
        threshold_source='data/scoped/ml/evaluation.json',
        selected_threshold=selected_threshold,
        minimum_candidate_probability=float(threshold),
        scoring_model_name=str(metadata['model_name']),
        scoring_model_version=str(metadata['model_version']),
        capacity_scenario=DEFAULT_CAPACITY_SCENARIO if capacity_per_hour == DEFAULT_CAPACITY_PER_HOUR else f'hourly_capacity_{capacity_per_hour}',
        capacity_per_hour=int(capacity_per_hour),
        preferred_station_load_per_station_hour=int(preferred_station_load_per_station_hour),
        diagnostic_station_excess_penalty_lambda=float(search_config['diagnostic_station_excess_penalty_lambda']),
        eligible_frozen_station_excess_penalty_lambdas=list(search_config['eligible_frozen_station_excess_penalty_lambdas']),
        frozen_station_excess_penalty_lambda=float(frozen_station_excess_penalty_lambda),
        feasible_selection_rule='exact_feasible_selection_target',
        constraint_set=['exact_feasible_selection_target', 'one_per_journey_per_horizon'],
        baseline_policies=list(POLICY_NAMES),
        tie_break_rule=[f'{CANONICAL_PROBABILITY_FIELD} desc', 'stop_event_key asc'],
        scenario_capacities=list(search_config['scenario_capacities']),
        metric_definitions=[
            'precision_at_capacity',
            'severe_delay_coverage',
            'lift_over_candidate_prevalence',
            'candidate_prevalence',
            'station_concentration_excess_total',
        ],
        frozen_at=datetime.now(UTC).isoformat(),
    )
    data = asdict(policy)
    validate_frozen_policy(data, search_config)
    return data


def validate_frozen_policy(frozen_policy: dict[str, object], search_config: dict[str, object]) -> None:
    if float(frozen_policy['minimum_candidate_probability']) != float(frozen_policy['selected_threshold']):
        raise ValueError('minimum_candidate_probability must equal selected_threshold')
    if float(frozen_policy['frozen_station_excess_penalty_lambda']) <= 0:
        raise ValueError('frozen final lambda must be positive')
    eligible = {float(value) for value in search_config['eligible_frozen_station_excess_penalty_lambdas']}
    if float(frozen_policy['frozen_station_excess_penalty_lambda']) not in eligible:
        raise ValueError('frozen lambda must come from eligible positive lambda set')


def save_frozen_policy(frozen_policy: dict[str, object]) -> None:
    OPTIMIZATION_DIR.mkdir(parents=True, exist_ok=True)
    FROZEN_POLICY_PATH.write_text(json.dumps(frozen_policy, indent=2), encoding='utf-8')


def load_frozen_policy() -> dict[str, object]:
    return json.loads(FROZEN_POLICY_PATH.read_text(encoding='utf-8'))


def normalize_probability_field(scored_rows: pd.DataFrame) -> pd.DataFrame:
    normalized = scored_rows.copy()
    if CANONICAL_PROBABILITY_FIELD in normalized.columns:
        return normalized
    if LEGACY_PROBABILITY_FIELD not in normalized.columns:
        raise ValueError(f'missing canonical probability field: {CANONICAL_PROBABILITY_FIELD}')
    normalized[CANONICAL_PROBABILITY_FIELD] = normalized[LEGACY_PROBABILITY_FIELD]
    normalized = normalized.drop(columns=[LEGACY_PROBABILITY_FIELD])
    return normalized


def enrich_scored_rows(scored_rows: pd.DataFrame) -> pd.DataFrame:
    enriched = scored_rows.copy()
    for field in OPTIONAL_ENRICHMENT_FIELDS:
        if field not in enriched.columns:
            enriched[field] = pd.NA
    if 'predicted_is_departure_severe_delay' not in enriched.columns:
        enriched['predicted_is_departure_severe_delay'] = False
    return enriched


def stable_sort(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(
        by=[CANONICAL_PROBABILITY_FIELD, 'stop_event_key'],
        ascending=[False, True],
        kind='mergesort',
    )



def prepare_candidates(
    *,
    scored_rows: pd.DataFrame,
    metadata: dict[str, object],
    execution_mode: Literal['development', 'final'],
    frozen_policy: dict[str, object],
) -> pd.DataFrame:
    selected = normalize_probability_field(scored_rows)
    selected = enrich_scored_rows(selected)
    missing_fields = [field for field in REQUIRED_SCORED_FIELDS if field not in selected.columns]
    if missing_fields:
        raise ValueError(f'missing required scored fields: {missing_fields}')
    split = MODE_TO_SPLIT[execution_mode]
    selected = selected.loc[selected['prediction_split'] == split].copy()
    if selected.empty:
        raise ValueError(f'no scored rows found for split {split}')

    model_versions = selected['model_version'].dropna().unique().tolist()
    if len(model_versions) != 1:
        raise ValueError('exactly one model_version must exist in selected scored rows')
    if model_versions[0] != metadata['model_version']:
        raise ValueError('scored row model_version does not match metadata model_version')

    selected_threshold = float(metadata['selected_threshold'])
    selected['selected_threshold'] = selected_threshold
    selected['predicted_is_departure_severe_delay'] = selected[CANONICAL_PROBABILITY_FIELD] >= selected_threshold
    selected['service_date'] = pd.to_datetime(selected['service_date'])
    selected['calendar_date'] = selected['service_date'].dt.strftime('%Y-%m-%d')
    selected['hour_of_day'] = selected['hour_of_day'].astype(int)
    selected['horizon_id'] = selected['calendar_date'] + '|' + selected['hour_of_day'].astype(str)
    selected['capacity_scenario'] = str(frozen_policy['capacity_scenario'])
    selected['capacity_per_hour'] = int(frozen_policy['capacity_per_hour'])
    selected['minimum_candidate_probability'] = float(frozen_policy['minimum_candidate_probability'])
    selected['execution_mode'] = execution_mode
    selected['optimization_run_id'] = f'{execution_mode}-{uuid.uuid4().hex[:8]}'
    selected['optimized_at'] = datetime.now(UTC).isoformat()
    selected['priority_score'] = selected[CANONICAL_PROBABILITY_FIELD]
    selected['preferred_station_load_per_station_hour'] = int(frozen_policy['preferred_station_load_per_station_hour'])
    selected['frozen_station_excess_penalty_lambda'] = float(frozen_policy['frozen_station_excess_penalty_lambda'])
    selected['is_eligible_candidate'] = True
    selected['eligibility_reason'] = ELIGIBILITY_REASON_ELIGIBLE
    selected.loc[selected[CANONICAL_PROBABILITY_FIELD].isna(), ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_INVALID_PROBABILITY]
    selected.loc[(~selected[CANONICAL_PROBABILITY_FIELD].between(0, 1, inclusive='both')) & selected['is_eligible_candidate'], ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_INVALID_PROBABILITY]
    selected.loc[(selected[CANONICAL_PROBABILITY_FIELD] < float(frozen_policy['minimum_candidate_probability'])) & selected['is_eligible_candidate'], ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_BELOW_THRESHOLD]
    selected.loc[selected[['stop_event_key', 'journey_id', 'station_id', 'hour_of_day']].isna().any(axis=1) & selected['is_eligible_candidate'], ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_MISSING_REQUIRED_FIELD]
    selected.loc[selected['stop_event_key'].duplicated(keep=False), ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_DUPLICATE_KEY]

    ranked_parts: list[pd.DataFrame] = []
    for _, horizon_frame in selected.groupby('horizon_id', sort=True):
        sorted_frame = stable_sort(horizon_frame)
        sorted_frame['candidate_priority_rank'] = range(1, len(sorted_frame) + 1)
        ranked_parts.append(sorted_frame)
    ranked = pd.concat(ranked_parts, ignore_index=True) if ranked_parts else selected.copy()

    ranked['feasible_selection_target'] = 0
    for _, horizon_frame in ranked.groupby('horizon_id', sort=False):
        eligible = horizon_frame.loc[horizon_frame['is_eligible_candidate']]
        feasible_target = min(int(frozen_policy['capacity_per_hour']), int(eligible['journey_id'].nunique()))
        ranked.loc[horizon_frame.index, 'feasible_selection_target'] = feasible_target
    return ranked


def _frame_signature(stop_event_key: str, horizon_id: str, seed: int) -> str:
    return hashlib.sha256(f'{seed}|{horizon_id}|{stop_event_key}'.encode('utf-8')).hexdigest()


def _journey_safe_select(eligible: pd.DataFrame, target: int, ordered_keys: list[str]) -> set[str]:
    selected_keys: set[str] = set()
    selected_journeys: set[str] = set()
    row_map = eligible.set_index('stop_event_key')
    for key in ordered_keys:
        if len(selected_keys) >= target:
            break
        journey_id = str(row_map.loc[key, 'journey_id'])
        if journey_id in selected_journeys:
            continue
        selected_keys.add(key)
        selected_journeys.add(journey_id)
    return selected_keys


def _station_excess_total(selected_frame: pd.DataFrame, preferred_load: int) -> float:
    if selected_frame.empty:
        return 0.0
    counts = selected_frame.groupby(['horizon_id', 'station_id']).size()
    return float(sum(max(int(value) - preferred_load, 0) for value in counts.tolist()))


def _delta_station_excess(selected_frame: pd.DataFrame, candidate_station_id: str, preferred_load: int) -> float:
    current = 0 if selected_frame.empty else int((selected_frame['station_id'] == candidate_station_id).sum())
    before = max(current - preferred_load, 0)
    after = max((current + 1) - preferred_load, 0)
    return float(after - before)


def _map_solver_status(model: gp.Model) -> str:
    if model.Status == GRB.OPTIMAL:
        return ALLOWED_SOLVER_STATUS_OPTIMAL
    if model.Status == GRB.TIME_LIMIT and model.SolCount:
        return ALLOWED_SOLVER_STATUS_TIME_LIMIT_WITH_INCUMBENT
    return str(model.Status)


def _finalize_decision_frame(
    frame: pd.DataFrame,
    *,
    policy_name: str,
    solver_status: str,
    selected_keys: set[str],
    objective_value: float,
    frozen_policy: dict[str, object],
) -> pd.DataFrame:
    decided = frame.copy()
    decided['policy_name'] = policy_name
    decided['optimization_policy_name'] = str(frozen_policy['optimization_policy_name'])
    decided['optimization_policy_version'] = str(frozen_policy['optimization_policy_version'])
    decided['scoring_model_name'] = decided['model_name']
    decided['scoring_model_version'] = decided['model_version']
    decided['selected_for_review'] = decided['stop_event_key'].isin(selected_keys)
    decided['objective_contribution'] = decided.apply(
        lambda row: float(row[CANONICAL_PROBABILITY_FIELD]) if bool(row['selected_for_review']) else 0.0,
        axis=1,
    )
    decided['solver_status'] = solver_status
    decided['solver_objective_value'] = float(objective_value)
    decided['selection_rank'] = pd.NA
    for _, horizon_frame in decided.loc[decided['selected_for_review']].groupby('horizon_id', sort=True):
        ranked = stable_sort(horizon_frame)
        decided.loc[ranked.index, 'selection_rank'] = range(1, len(ranked) + 1)
    decided = decided.sort_values(by=['horizon_id', 'candidate_priority_rank', 'stop_event_key'], kind='mergesort').reset_index(drop=True)
    return decided


def _select_ml_first(horizon_frame: pd.DataFrame) -> set[str]:
    eligible = stable_sort(horizon_frame.loc[horizon_frame['is_eligible_candidate']])
    target = int(horizon_frame['feasible_selection_target'].iloc[0])
    return _journey_safe_select(eligible, target, eligible['stop_event_key'].tolist())


def _select_random(horizon_frame: pd.DataFrame, seed: int) -> set[str]:
    eligible = horizon_frame.loc[horizon_frame['is_eligible_candidate']].copy()
    target = int(horizon_frame['feasible_selection_target'].iloc[0])
    eligible['random_order'] = eligible.apply(
        lambda row: _frame_signature(str(row['stop_event_key']), str(row['horizon_id']), seed),
        axis=1,
    )
    eligible = eligible.sort_values(by=['random_order', 'stop_event_key'], kind='mergesort').reset_index(drop=True)
    return _journey_safe_select(eligible, target, eligible['stop_event_key'].tolist())


def _select_constrained_greedy(horizon_frame: pd.DataFrame, frozen_policy: dict[str, object]) -> tuple[set[str], float]:
    eligible = horizon_frame.loc[horizon_frame['is_eligible_candidate']].copy()
    target = int(horizon_frame['feasible_selection_target'].iloc[0])
    preferred_load = int(frozen_policy['preferred_station_load_per_station_hour'])
    penalty_lambda = float(frozen_policy['frozen_station_excess_penalty_lambda'])
    selected_keys: set[str] = set()
    selected_journeys: set[str] = set()
    selected_rows = eligible.iloc[0:0].copy()
    objective_value = 0.0
    for _ in range(target):
        candidates = eligible.loc[~eligible['journey_id'].isin(selected_journeys)].copy()
        if candidates.empty:
            break
        candidates['delta_station_excess'] = candidates['station_id'].apply(
            lambda station_id: _delta_station_excess(selected_rows, str(station_id), preferred_load)
        )
        candidates['marginal_score'] = candidates[CANONICAL_PROBABILITY_FIELD] - penalty_lambda * candidates['delta_station_excess']
        candidates = candidates.sort_values(
            by=['marginal_score', CANONICAL_PROBABILITY_FIELD, 'stop_event_key'],
            ascending=[False, False, True],
            kind='mergesort',
        ).reset_index(drop=True)
        chosen = candidates.iloc[0]
        selected_keys.add(str(chosen['stop_event_key']))
        selected_journeys.add(str(chosen['journey_id']))
        selected_rows = pd.concat([selected_rows, chosen.to_frame().T], ignore_index=True)
        objective_value += float(chosen[CANONICAL_PROBABILITY_FIELD]) - penalty_lambda * float(chosen['delta_station_excess'])
    return selected_keys, objective_value


def _select_gurobi(horizon_frame: pd.DataFrame, frozen_policy: dict[str, object]) -> tuple[set[str], str, float]:
    eligible = horizon_frame.loc[horizon_frame['is_eligible_candidate']].copy()
    target = int(horizon_frame['feasible_selection_target'].iloc[0])
    if target == 0 or eligible.empty:
        return set(), ALLOWED_SOLVER_STATUS_OPTIMAL, 0.0
    preferred_load = int(frozen_policy['preferred_station_load_per_station_hour'])
    penalty_lambda = float(frozen_policy['frozen_station_excess_penalty_lambda'])
    model = gp.Model('optimization_value_add')
    model.Params.OutputFlag = 0
    model.Params.Seed = RANDOM_SEED
    decision_vars = {
        str(row.stop_event_key): model.addVar(vtype=GRB.BINARY, name=f'x_{row.stop_event_key}')
        for row in eligible.itertuples(index=False)
    }
    station_vars = {
        station_id: model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name=f'u_{station_id}')
        for station_id in sorted(eligible['station_id'].astype(str).unique().tolist())
    }
    model.setObjective(
        gp.quicksum(decision_vars[str(row.stop_event_key)] * float(row.predicted_severe_delay_probability) for row in eligible.itertuples(index=False))
        - penalty_lambda * gp.quicksum(station_vars.values()),
        GRB.MAXIMIZE,
    )
    model.addConstr(gp.quicksum(decision_vars.values()) == target, name='exact_target')
    for journey_id, group in eligible.groupby('journey_id', sort=True):
        model.addConstr(gp.quicksum(decision_vars[str(key)] for key in group['stop_event_key']) <= 1, name=f'journey_{journey_id}')
    for station_id, group in eligible.groupby('station_id', sort=True):
        model.addConstr(
            station_vars[str(station_id)] >= gp.quicksum(decision_vars[str(key)] for key in group['stop_event_key']) - preferred_load,
            name=f'station_{station_id}',
        )
    model.optimize()
    solver_status = _map_solver_status(model)
    selected_keys = {key for key, variable in decision_vars.items() if variable.X > 0.5}
    return selected_keys, solver_status, float(model.ObjVal if model.SolCount else 0.0)


def select_policy(
    frame: pd.DataFrame,
    policy_name: str,
    *,
    frozen_policy: dict[str, object],
    search_config: dict[str, object],
) -> pd.DataFrame:
    selected_keys: set[str] = set()
    objective_value = 0.0
    solver_status = 'deterministic'
    for _, horizon_frame in frame.groupby('horizon_id', sort=True):
        if policy_name == 'ml_first':
            horizon_selected = _select_ml_first(horizon_frame)
        elif policy_name == 'random':
            horizon_selected = _select_random(horizon_frame, int(search_config['random_seed']))
        elif policy_name == 'constrained_greedy':
            horizon_selected, horizon_objective = _select_constrained_greedy(horizon_frame, frozen_policy)
            objective_value += horizon_objective
        elif policy_name == DEFAULT_POLICY_NAME:
            horizon_selected, solver_status, horizon_objective = _select_gurobi(horizon_frame, frozen_policy)
            objective_value += horizon_objective
        else:
            raise ValueError(f'unsupported policy_name: {policy_name}')
        if policy_name in ('ml_first', 'random'):
            objective_value += float(horizon_frame.loc[horizon_frame['stop_event_key'].isin(horizon_selected), CANONICAL_PROBABILITY_FIELD].sum())
        selected_keys.update(horizon_selected)
    return _finalize_decision_frame(
        frame,
        policy_name=policy_name,
        solver_status=solver_status,
        selected_keys=selected_keys,
        objective_value=objective_value,
        frozen_policy=frozen_policy,
    )


def build_horizon_summary(decisions: pd.DataFrame) -> pd.DataFrame:
    summary_rows: list[dict[str, object]] = []
    for horizon_id, horizon_frame in decisions.groupby('horizon_id', sort=True):
        selected = horizon_frame.loc[horizon_frame['selected_for_review']]
        eligible = horizon_frame.loc[horizon_frame['is_eligible_candidate']]
        candidate_count = int(len(horizon_frame))
        eligible_candidate_count = int(len(eligible))
        selected_count = int(len(selected))
        actual_severe_selected_count = int(selected['actual_is_departure_severe_delay'].fillna(False).astype(bool).sum())
        actual_severe_candidate_count = int(eligible['actual_is_departure_severe_delay'].fillna(False).astype(bool).sum())
        candidate_prevalence = None if eligible_candidate_count == 0 else actual_severe_candidate_count / eligible_candidate_count
        precision_at_capacity = None if selected_count == 0 else actual_severe_selected_count / selected_count
        severe_delay_coverage = None if actual_severe_candidate_count == 0 else actual_severe_selected_count / actual_severe_candidate_count
        lift = None
        if candidate_prevalence not in (None, 0) and precision_at_capacity is not None:
            lift = precision_at_capacity / candidate_prevalence
        station_counts = selected.groupby('station_id').size() if not selected.empty else pd.Series(dtype='int64')
        preferred_load = int(horizon_frame['preferred_station_load_per_station_hour'].iloc[0])
        station_excess = float(sum(max(int(value) - preferred_load, 0) for value in station_counts.tolist()))
        summary_rows.append(
            {
                'optimization_run_id': horizon_frame['optimization_run_id'].iloc[0],
                'execution_mode': horizon_frame['execution_mode'].iloc[0],
                'policy_name': horizon_frame['policy_name'].iloc[0],
                'calendar_date': horizon_frame['calendar_date'].iloc[0],
                'hour_of_day': int(horizon_frame['hour_of_day'].iloc[0]),
                'horizon_id': horizon_id,
                'capacity_scenario': horizon_frame['capacity_scenario'].iloc[0],
                'capacity_per_hour': int(horizon_frame['capacity_per_hour'].iloc[0]),
                'feasible_selection_target': int(horizon_frame['feasible_selection_target'].iloc[0]),
                'candidate_count': candidate_count,
                'eligible_candidate_count': eligible_candidate_count,
                'selected_event_count': selected_count,
                'candidate_shortage_count': int(horizon_frame['capacity_per_hour'].iloc[0]) - int(horizon_frame['feasible_selection_target'].iloc[0]),
                'unused_capacity': int(horizon_frame['capacity_per_hour'].iloc[0]) - selected_count,
                'selected_probability_score_sum': float(selected[CANONICAL_PROBABILITY_FIELD].sum()),
                'actual_severe_selected_count': actual_severe_selected_count,
                'selected_severe_event_count': actual_severe_selected_count,
                'actual_severe_candidate_count': actual_severe_candidate_count,
                'candidate_prevalence': candidate_prevalence,
                'precision_at_capacity': precision_at_capacity,
                'severe_delay_coverage': severe_delay_coverage,
                'lift_over_candidate_prevalence': lift,
                'distinct_selected_stations': int(selected['station_id'].nunique()),
                'max_selected_same_station_in_horizon': int(station_counts.max()) if not station_counts.empty else 0,
                'station_concentration_excess_total': station_excess,
                'penalty_active_in_horizon': station_excess > 0,
                'solver_status': horizon_frame['solver_status'].iloc[0],
                'scoring_model_name': horizon_frame['scoring_model_name'].iloc[0],
                'scoring_model_version': horizon_frame['scoring_model_version'].iloc[0],
                'optimization_policy_name': horizon_frame['optimization_policy_name'].iloc[0],
                'optimization_policy_version': horizon_frame['optimization_policy_version'].iloc[0],
                'preferred_station_load_per_station_hour': int(horizon_frame['preferred_station_load_per_station_hour'].iloc[0]),
                'frozen_station_excess_penalty_lambda': float(horizon_frame['frozen_station_excess_penalty_lambda'].iloc[0]),
                'optimized_at': horizon_frame['optimized_at'].iloc[0],
            }
        )
    return pd.DataFrame(summary_rows)


def build_horizon_policy_metrics(policy_frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for frame in policy_frames:
        summary = build_horizon_summary(frame)
        hashes: list[str] = []
        for _, horizon_frame in frame.groupby('horizon_id', sort=True):
            selected_keys = sorted(horizon_frame.loc[horizon_frame['selected_for_review'], 'stop_event_key'].astype(str).tolist())
            hashes.append(hashlib.sha256('|'.join(selected_keys).encode('utf-8')).hexdigest())
        summary['selected_stop_event_key_hash'] = hashes
        frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _compute_lift(row: pd.Series, random_map: dict[tuple[str, int], object]) -> float | None:
    baseline = random_map.get((str(row['execution_mode']), int(row['capacity_per_hour'])))
    if baseline in (None, 0) or pd.isna(baseline):
        return None
    return float(row['precision_at_capacity']) / float(baseline)


def build_policy_comparison(policy_frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for frame in policy_frames:
        summary = build_horizon_summary(frame)
        if summary.empty:
            continue
        selected_events = frame.loc[frame['selected_for_review']]
        total_actual_severe = int(frame.loc[frame['is_eligible_candidate'], 'actual_is_departure_severe_delay'].fillna(False).astype(bool).sum())
        selected_severe = int(selected_events['actual_is_departure_severe_delay'].fillna(False).astype(bool).sum())
        selected_count = int(selected_events.shape[0])
        horizon_count = int(summary.shape[0])
        precision = None if selected_count == 0 else selected_severe / selected_count
        coverage = None if total_actual_severe == 0 else selected_severe / total_actual_severe
        rows.append(
            {
                'execution_mode': summary['execution_mode'].iloc[0],
                'policy_name': summary['policy_name'].iloc[0],
                'capacity_scenario': summary['capacity_scenario'].iloc[0],
                'capacity_per_hour': int(summary['capacity_per_hour'].iloc[0]),
                'selected_event_count': selected_count,
                'selected_severe_event_count': selected_severe,
                'precision_at_capacity': precision,
                'severe_delay_coverage': coverage,
                'lift_vs_random': None,
                'expected_risk_score_captured': float(selected_events[CANONICAL_PROBABILITY_FIELD].sum()),
                'distinct_stations_covered': int(selected_events['station_id'].nunique()),
                'max_selected_same_station_in_horizon': int(summary['max_selected_same_station_in_horizon'].max()),
                'station_concentration_excess_total': float(summary['station_concentration_excess_total'].sum()),
                'unused_capacity_total': int(summary['unused_capacity'].sum()),
                'binding_horizon_count': int((summary['feasible_selection_target'] == summary['capacity_per_hour']).sum()),
                'binding_horizon_rate': float((summary['feasible_selection_target'] == summary['capacity_per_hour']).sum() / horizon_count),
                'candidate_shortage_horizon_count': int((summary['candidate_shortage_count'] > 0).sum()),
                'candidate_shortage_horizon_rate': float((summary['candidate_shortage_count'] > 0).sum() / horizon_count),
                'median_feasible_selection_target': float(summary['feasible_selection_target'].median()),
                'preferred_station_load_per_station_hour': int(summary['preferred_station_load_per_station_hour'].iloc[0]),
                'frozen_station_excess_penalty_lambda': float(summary['frozen_station_excess_penalty_lambda'].iloc[0]),
            }
        )
    comparison = pd.DataFrame(rows)
    if comparison.empty:
        return comparison
    random_map = comparison.loc[comparison['policy_name'] == 'random'].set_index(['execution_mode', 'capacity_per_hour'])['precision_at_capacity'].to_dict()
    comparison['lift_vs_random'] = comparison.apply(lambda row: _compute_lift(row, random_map), axis=1)
    return comparison


def build_pairwise_policy_diagnostics(reference: pd.DataFrame, candidate: pd.DataFrame) -> dict[str, object]:
    horizon_ids = sorted(set(reference['horizon_id']).intersection(candidate['horizon_id']))
    matching = 0
    jaccards: list[float] = []
    disagreements = 0
    penalty_active = 0
    for horizon_id in horizon_ids:
        left = set(reference.loc[(reference['horizon_id'] == horizon_id) & reference['selected_for_review'], 'stop_event_key'].astype(str))
        right_frame = candidate.loc[candidate['horizon_id'] == horizon_id]
        right = set(right_frame.loc[right_frame['selected_for_review'], 'stop_event_key'].astype(str))
        if left == right:
            matching += 1
        else:
            disagreements += len(left.symmetric_difference(right))
        union = left.union(right)
        jaccards.append(1.0 if not union else len(left.intersection(right)) / len(union))
        preferred_load = int(right_frame['preferred_station_load_per_station_hour'].iloc[0])
        penalty_active += int(_station_excess_total(right_frame.loc[right_frame['selected_for_review']], preferred_load) > 0)
    horizon_count = len(horizon_ids)
    return {
        'horizon_count': horizon_count,
        'matching_horizon_count': matching,
        'differing_horizon_count': horizon_count - matching,
        'selected_set_match_rate': 1.0 if horizon_count == 0 else matching / horizon_count,
        'mean_selected_set_jaccard': None if not jaccards else float(sum(jaccards) / len(jaccards)),
        'selected_event_disagreement_count': disagreements,
        'penalty_active_horizon_count': penalty_active,
    }


def build_opportunity_diagnostics(prepared: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for horizon_id, horizon_frame in prepared.groupby('horizon_id', sort=True):
        eligible = horizon_frame.loc[horizon_frame['is_eligible_candidate']]
        station_counts = eligible.groupby('station_id').size() if not eligible.empty else pd.Series(dtype='int64')
        rows.append(
            {
                'calendar_date': horizon_frame['calendar_date'].iloc[0],
                'hour_of_day': int(horizon_frame['hour_of_day'].iloc[0]),
                'horizon_id': horizon_id,
                'capacity_per_hour': int(horizon_frame['capacity_per_hour'].iloc[0]),
                'eligible_event_count': int(eligible.shape[0]),
                'distinct_eligible_journey_count': int(eligible['journey_id'].nunique()),
                'distinct_eligible_station_count': int(eligible['station_id'].nunique()),
                'max_candidate_count_at_one_station': int(station_counts.max()) if not station_counts.empty else 0,
                'feasible_selection_target': int(horizon_frame['feasible_selection_target'].iloc[0]),
                'station_excess_could_activate': bool(not station_counts.empty and int(station_counts.max()) > 1),
                'capacity_binds': bool(int(horizon_frame['feasible_selection_target'].iloc[0]) == int(horizon_frame['capacity_per_hour'].iloc[0])),
            }
        )
    return pd.DataFrame(rows)


def _assert_allowed_solver_statuses(policy_frames: list[pd.DataFrame], *, execution_mode: str, search_config: dict[str, object]) -> None:
    allowed = set(search_config['development_allowed_solver_statuses'] if execution_mode == DEVELOPMENT_MODE else search_config['final_allowed_solver_statuses'])
    for frame in policy_frames:
        if str(frame['policy_name'].iloc[0]) != DEFAULT_POLICY_NAME:
            continue
        statuses = set(frame['solver_status'].dropna().astype(str).unique().tolist())
        if not statuses.issubset(allowed):
            raise ValueError(f'disallowed solver statuses for {execution_mode}: {sorted(statuses)}')


def tune_development_policy(
    prepared: pd.DataFrame,
    *,
    metadata: dict[str, object],
    search_config: dict[str, object],
) -> tuple[pd.DataFrame, dict[str, object]]:
    rows: list[dict[str, object]] = []
    zero_cache: dict[int, pd.DataFrame] = {}
    for preferred_load in search_config['preferred_station_load_per_station_hour_candidates']:
        zero_policy = build_frozen_policy(
            metadata=metadata,
            search_config=search_config,
            preferred_station_load_per_station_hour=int(preferred_load),
            frozen_station_excess_penalty_lambda=float(search_config['eligible_frozen_station_excess_penalty_lambdas'][0]),
        )
        zero_policy['frozen_station_excess_penalty_lambda'] = float(search_config['diagnostic_station_excess_penalty_lambda'])
        zero_frame = select_policy(prepared, DEFAULT_POLICY_NAME, frozen_policy=zero_policy, search_config=search_config)
        zero_cache[int(preferred_load)] = zero_frame
        for penalty_lambda in [float(search_config['diagnostic_station_excess_penalty_lambda'])] + [float(value) for value in search_config['eligible_frozen_station_excess_penalty_lambdas']]:
            candidate_policy = build_frozen_policy(
                metadata=metadata,
                search_config=search_config,
                preferred_station_load_per_station_hour=int(preferred_load),
                frozen_station_excess_penalty_lambda=max(penalty_lambda, 0.05),
            )
            candidate_policy['frozen_station_excess_penalty_lambda'] = penalty_lambda
            frame = select_policy(prepared, DEFAULT_POLICY_NAME, frozen_policy=candidate_policy, search_config=search_config)
            summary = build_horizon_summary(frame)
            diagnostics = build_pairwise_policy_diagnostics(zero_cache[int(preferred_load)], frame)
            selected = frame.loc[frame['selected_for_review']]
            total_actual_severe = int(frame.loc[frame['is_eligible_candidate'], 'actual_is_departure_severe_delay'].fillna(False).astype(bool).sum())
            selected_severe = int(selected['actual_is_departure_severe_delay'].fillna(False).astype(bool).sum())
            rows.append(
                {
                    'preferred_station_load_per_station_hour': int(preferred_load),
                    'station_excess_penalty_lambda': float(penalty_lambda),
                    'is_diagnostic_zero_penalty': penalty_lambda == float(search_config['diagnostic_station_excess_penalty_lambda']),
                    'solver_status': frame['solver_status'].iloc[0],
                    'selected_severe_event_count': selected_severe,
                    'total_actual_severe_candidate_count': total_actual_severe,
                    'severe_delay_coverage': None if total_actual_severe == 0 else selected_severe / total_actual_severe,
                    'station_concentration_excess_total': float(summary['station_concentration_excess_total'].sum()),
                    'distinct_stations_covered': int(selected['station_id'].nunique()),
                    'matching_horizon_count_vs_zero_penalty': diagnostics['matching_horizon_count'],
                    'differing_horizon_count_vs_zero_penalty': diagnostics['differing_horizon_count'],
                }
            )
    tuning = pd.DataFrame(rows)
    eligible = tuning.loc[~tuning['is_diagnostic_zero_penalty']].copy()
    eligible = eligible.sort_values(
        by=['selected_severe_event_count', 'severe_delay_coverage', 'station_concentration_excess_total', 'distinct_stations_covered', 'station_excess_penalty_lambda', 'preferred_station_load_per_station_hour'],
        ascending=[False, False, True, False, True, True],
        kind='mergesort',
    ).reset_index(drop=True)
    winner = eligible.iloc[0]
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=int(winner['preferred_station_load_per_station_hour']),
        frozen_station_excess_penalty_lambda=float(winner['station_excess_penalty_lambda']),
    )
    return tuning, frozen_policy


def persist_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    try:
        connection.register('frame_view', frame)
        connection.execute(f"copy frame_view to '{path.as_posix()}' (format parquet)")
    finally:
        connection.close()


def build_mode_outputs(
    *,
    scored_rows: pd.DataFrame,
    metadata: dict[str, object],
    execution_mode: Literal['development', 'final'],
    search_config: dict[str, object],
    frozen_policy: dict[str, object],
) -> dict[str, object]:
    policy_frames: list[pd.DataFrame] = []
    canonical_event_decision: pd.DataFrame | None = None
    canonical_horizon_summary: pd.DataFrame | None = None
    for capacity_per_hour in search_config['scenario_capacities']:
        capacity_policy = dict(frozen_policy)
        capacity_policy['capacity_per_hour'] = int(capacity_per_hour)
        capacity_policy['capacity_scenario'] = DEFAULT_CAPACITY_SCENARIO if int(capacity_per_hour) == DEFAULT_CAPACITY_PER_HOUR else f'hourly_capacity_{capacity_per_hour}'
        prepared = prepare_candidates(
            scored_rows=scored_rows,
            metadata=metadata,
            execution_mode=execution_mode,
            frozen_policy=capacity_policy,
        )
        for policy_name in POLICY_NAMES:
            frame = select_policy(prepared, policy_name, frozen_policy=capacity_policy, search_config=search_config)
            policy_frames.append(frame)
            if policy_name == DEFAULT_POLICY_NAME and int(capacity_per_hour) == DEFAULT_CAPACITY_PER_HOUR:
                canonical_event_decision = frame
                canonical_horizon_summary = build_horizon_summary(frame)
    _assert_allowed_solver_statuses(policy_frames, execution_mode=execution_mode, search_config=search_config)
    if canonical_event_decision is None or canonical_horizon_summary is None:
        raise ValueError('canonical artifacts were not produced')
    horizon_policy_metrics = build_horizon_policy_metrics(policy_frames)
    policy_comparison = build_policy_comparison(policy_frames)
    comparison_lookup = {(str(frame['policy_name'].iloc[0]), int(frame['capacity_per_hour'].iloc[0])): frame for frame in policy_frames}
    pairwise = {
        'gurobi_vs_ml_first': build_pairwise_policy_diagnostics(comparison_lookup[('ml_first', DEFAULT_CAPACITY_PER_HOUR)], comparison_lookup[(DEFAULT_POLICY_NAME, DEFAULT_CAPACITY_PER_HOUR)]),
        'gurobi_vs_constrained_greedy': build_pairwise_policy_diagnostics(comparison_lookup[('constrained_greedy', DEFAULT_CAPACITY_PER_HOUR)], comparison_lookup[(DEFAULT_POLICY_NAME, DEFAULT_CAPACITY_PER_HOUR)]),
    }
    evaluation = {
        'mode': execution_mode,
        'frozen_policy': frozen_policy,
        'horizon_policy_metrics_path': f'data/scoped/optimization/{execution_mode}/horizon_policy_metrics.parquet',
        'policy_comparison_path': f'data/scoped/optimization/{execution_mode}/policy_comparison.parquet',
        'pairwise_diagnostics': pairwise,
    }
    return {
        'event_decision': canonical_event_decision,
        'horizon_summary': canonical_horizon_summary,
        'horizon_policy_metrics': horizon_policy_metrics,
        'policy_comparison': policy_comparison,
        'evaluation': evaluation,
    }


def update_dashboard_manifest() -> None:
    manifest = {
        'artifact': 'dashboard_mvp_manifest',
        'status': 'handoff_ready',
        'metadata_contract_only': True,
        'report_build_status': 'pending',
        'page_count': 4,
        'notes': [
            'Prototype / historical evaluation only.',
            'ML scores severe-delay risk. Gurobi selects limited review slots under capacity and station-concentration trade-off.',
            'Canonical event_decision and horizon_summary are frozen Gurobi at capacity 3. Cross-policy and cross-capacity analysis lives in policy_comparison and horizon_policy_metrics.',
            'Expanded same-hub scope is stress-test evidence, not causal impact proof.',
        ],
        'semantic_contract': {
            'canonical_policy_name': DEFAULT_POLICY_NAME,
            'canonical_capacity_per_hour': DEFAULT_CAPACITY_PER_HOUR,
            'comparison_policies': list(POLICY_NAMES),
            'scenario_capacities': SCENARIO_CAPACITIES,
            'wording_guardrails': [
                'Say prototype / historical evaluation.',
                'Do not claim causal avoided-delay impact.',
                'Separate ML prediction from optimizer decision.',
            ],
        },
        'pages': [
            {
                'page_key': 'overview_capacity',
                'page_title': 'Overview and Capacity',
                'required_slicers': ['calendar_date', 'hour_of_day', 'scenario_key'],
                'required_visual_groups': ['selected_vs_eligible_cards', 'candidate_prevalence_cards', 'precision_coverage_lift_cards', 'capacity_utilization_cards', 'date_hour_capacity_trend'],
            },
            {
                'page_key': 'candidate_station_detail',
                'page_title': 'Candidate and Station Detail',
                'required_slicers': ['calendar_date', 'hour_of_day', 'scenario_key', 'station_id', 'train_service_key', 'eligibility_reason', 'selected_for_review'],
                'required_visual_groups': ['selected_vs_not_selected_breakdown', 'station_detail_table', 'train_service_detail_table', 'candidate_probability_distribution'],
            },
            {
                'page_key': 'decision_story',
                'page_title': 'Decision Story',
                'required_slicers': ['calendar_date', 'hour_of_day', 'scenario_key'],
                'required_visual_groups': ['capacity_regime_story', 'selection_examples', 'station_tradeoff_story'],
            },
            {
                'page_key': 'method_comparison',
                'page_title': 'How Methods Compare',
                'required_slicers': ['scenario_key'],
                'required_visual_groups': ['policy_comparison_cards', 'pairwise_comparison', 'capacity_comparison'],
            },
        ],
    }
    POWER_BI_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def update_thread_notes() -> None:
    thread_path = REPO_ROOT / 'docs' / 'intent' / 'workstreams' / 'threads' / 'deutsche-bahn-decision-dashboard' / 'thread-optimization-value-add-redesign.md'
    if not thread_path.exists():
        return
    content = thread_path.read_text(encoding='utf-8')
    if '## Execution Notes' in content:
        return
    content += '\n\n## Execution Notes\n\n- implemented deterministic search config under configs/optimization/optimization_policy_search_config.json\n- implemented canonical frozen Gurobi outputs at capacity 3 plus cross-policy comparison artifacts\n- kept service weights, corridor constraints, intervention cost modeling, and BigQuery migration deferred\n'
    thread_path.write_text(content, encoding='utf-8')


def main() -> None:
    search_config = ensure_search_config()
    metadata = load_ml_metadata()
    scored_rows = load_scored_rows()

    development_seed_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=int(search_config['preferred_station_load_per_station_hour_candidates'][0]),
        frozen_station_excess_penalty_lambda=float(search_config['eligible_frozen_station_excess_penalty_lambdas'][0]),
    )
    development_prepared = prepare_candidates(
        scored_rows=scored_rows,
        metadata=metadata,
        execution_mode=DEVELOPMENT_MODE,
        frozen_policy=development_seed_policy,
    )
    opportunity = build_opportunity_diagnostics(development_prepared)
    tuning_results, frozen_policy = tune_development_policy(development_prepared, metadata=metadata, search_config=search_config)
    save_frozen_policy(frozen_policy)

    for execution_mode in (DEVELOPMENT_MODE, FINAL_MODE):
        mode_outputs = build_mode_outputs(
            scored_rows=scored_rows,
            metadata=metadata,
            execution_mode=execution_mode,
            search_config=search_config,
            frozen_policy=frozen_policy,
        )
        mode_dir = OPTIMIZATION_DIR / execution_mode
        persist_frame(mode_outputs['event_decision'], mode_dir / 'event_decision.parquet')
        persist_frame(mode_outputs['horizon_summary'], mode_dir / 'horizon_summary.parquet')
        persist_frame(mode_outputs['horizon_policy_metrics'], mode_dir / 'horizon_policy_metrics.parquet')
        persist_frame(mode_outputs['policy_comparison'], mode_dir / 'policy_comparison.parquet')
        if execution_mode == DEVELOPMENT_MODE:
            persist_frame(opportunity, mode_dir / 'opportunity_diagnostics.parquet')
            persist_frame(tuning_results, mode_dir / 'tuning_search_results.parquet')
            mode_outputs['evaluation']['opportunity_diagnostics_path'] = 'data/scoped/optimization/development/opportunity_diagnostics.parquet'
            mode_outputs['evaluation']['tuning_search_results_path'] = 'data/scoped/optimization/development/tuning_search_results.parquet'
            mode_outputs['evaluation']['development_tuning_winner'] = {
                'preferred_station_load_per_station_hour': frozen_policy['preferred_station_load_per_station_hour'],
                'frozen_station_excess_penalty_lambda': frozen_policy['frozen_station_excess_penalty_lambda'],
            }
        (mode_dir / 'evaluation.json').write_text(json.dumps(mode_outputs['evaluation'], indent=2), encoding='utf-8')

    update_dashboard_manifest()
    update_thread_notes()


if __name__ == '__main__':
    main()
