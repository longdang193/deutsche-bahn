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
SCORED_PATH = ML_DIR / 'scored_stop_events.parquet'
ML_EVALUATION_PATH = ML_DIR / 'evaluation.json'
FROZEN_POLICY_PATH = OPTIMIZATION_DIR / 'frozen_policy.json'
DUCKDB_PATH = REPO_ROOT / 'data' / 'scoped' / 'local_scope_bronze.duckdb'
CANONICAL_PROBABILITY_FIELD = 'predicted_severe_delay_probability'
LEGACY_PROBABILITY_FIELD = 'predicted_probability'
DEFAULT_CAPACITY_PER_HOUR = 3
DEFAULT_CAPACITY_SCENARIO = 'hourly_capacity_3'
DEVELOPMENT_MODE = 'development'
FINAL_MODE = 'final'
MODE_TO_SPLIT = {
    DEVELOPMENT_MODE: 'validation',
    FINAL_MODE: 'test',
}
ELIGIBILITY_REASON_ELIGIBLE = 'eligible'
ELIGIBILITY_REASON_BELOW_THRESHOLD = 'below_minimum_candidate_probability'
ELIGIBILITY_REASON_INVALID_PROBABILITY = 'invalid_probability'
ELIGIBILITY_REASON_DUPLICATE_KEY = 'duplicate_stop_event_key'
ELIGIBILITY_REASON_MISSING_REQUIRED_FIELD = 'missing_required_field'
ELIGIBILITY_REASON_LOWER_PRIORITY_DUPLICATE_JOURNEY = 'lower_priority_duplicate_journey_candidate'
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


@dataclass(frozen=True)
class FrozenPolicy:
    policy_version: str
    execution_modes: list[str]
    canonical_probability_field: str
    threshold_source: str
    minimum_candidate_probability: float
    capacity_scenario: str
    capacity_per_hour: int
    constraint_set: list[str]
    tie_break_rule: list[str]
    metric_definitions: list[str]
    model_name: str
    model_version: str
    selected_threshold: float
    frozen_at: str


def load_ml_metadata() -> dict[str, object]:
    return json.loads(ML_EVALUATION_PATH.read_text(encoding='utf-8'))


def load_scored_rows() -> pd.DataFrame:
    connection = duckdb.connect()
    try:
        return connection.execute(f"select * from read_parquet('{SCORED_PATH.as_posix()}')").fetch_df()
    finally:
        connection.close()


def build_frozen_policy(
    *,
    metadata: dict[str, object],
    capacity_per_hour: int = DEFAULT_CAPACITY_PER_HOUR,
    minimum_candidate_probability: float | None = None,
) -> dict[str, object]:
    selected_threshold = float(metadata['selected_threshold'])
    threshold = selected_threshold if minimum_candidate_probability is None else minimum_candidate_probability
    policy = FrozenPolicy(
        policy_version='2026-06-28-v1',
        execution_modes=[DEVELOPMENT_MODE, FINAL_MODE],
        canonical_probability_field=CANONICAL_PROBABILITY_FIELD,
        threshold_source='data/scoped/ml/evaluation.json',
        minimum_candidate_probability=float(threshold),
        capacity_scenario=DEFAULT_CAPACITY_SCENARIO if capacity_per_hour == DEFAULT_CAPACITY_PER_HOUR else f'hourly_capacity_{capacity_per_hour}',
        capacity_per_hour=int(capacity_per_hour),
        constraint_set=['hourly_capacity', 'one_per_journey_per_horizon'],
        tie_break_rule=[f'{CANONICAL_PROBABILITY_FIELD} desc', 'stop_event_key asc'],
        metric_definitions=['precision_at_capacity', 'severe_delay_coverage', 'lift_over_candidate_prevalence', 'candidate_prevalence'],
        model_name=str(metadata['model_name']),
        model_version=str(metadata['model_version']),
        selected_threshold=selected_threshold,
        frozen_at=datetime.now(UTC).isoformat(),
    )
    return asdict(policy)


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
    if all(field in scored_rows.columns for field in OPTIONAL_ENRICHMENT_FIELDS):
        return scored_rows
    connection = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        gold_lookup = connection.execute(
            """
            select distinct stop_event_key, station_name, train_service_key, service_class
            from gold.feature_stop_event
            """
        ).fetch_df()
    finally:
        connection.close()
    if gold_lookup['stop_event_key'].duplicated().any():
        raise ValueError('gold enrichment lookup has duplicate stop_event_key values')
    before_count = len(scored_rows)
    enriched = scored_rows.merge(gold_lookup, on='stop_event_key', how='left', validate='one_to_one')
    if len(enriched) != before_count:
        raise ValueError('gold enrichment changed candidate row count')
    if enriched['stop_event_key'].duplicated().any():
        raise ValueError('gold enrichment created duplicate stop_event_key values')
    return enriched


def prepare_candidates(
    *,
    scored_rows: pd.DataFrame,
    metadata: dict[str, object],
    execution_mode: Literal['development', 'final'],
    frozen_policy: dict[str, object],
) -> pd.DataFrame:
    expected_split = MODE_TO_SPLIT[execution_mode]
    normalized = normalize_probability_field(scored_rows)
    normalized = enrich_scored_rows(normalized)
    missing_fields = [field for field in REQUIRED_SCORED_FIELDS if field not in normalized.columns]
    if missing_fields:
        raise ValueError(f'missing required fields: {missing_fields}')

    selected = normalized.loc[normalized['prediction_split'] == expected_split].copy()
    if selected.empty:
        raise ValueError(f'no scored rows found for split {expected_split}')
    model_versions = selected['model_version'].dropna().unique().tolist()
    if len(model_versions) != 1:
        raise ValueError('exactly one model_version must exist in selected scored rows')
    if model_versions[0] != metadata['model_version']:
        raise ValueError('scored row model_version does not match metadata model_version')

    selected_threshold = float(metadata['selected_threshold'])
    if not 0 <= selected_threshold <= 1:
        raise ValueError('selected_threshold must be between 0 and 1')
    if 'selected_threshold' in selected.columns:
        row_thresholds = selected['selected_threshold'].dropna().unique().tolist()
        if len(row_thresholds) > 1 or (row_thresholds and float(row_thresholds[0]) != selected_threshold):
            raise ValueError('scored row threshold does not match metadata threshold')

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

    selected['is_eligible_candidate'] = True
    selected['eligibility_reason'] = ELIGIBILITY_REASON_ELIGIBLE
    selected.loc[selected[CANONICAL_PROBABILITY_FIELD].isna(), ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_INVALID_PROBABILITY]
    selected.loc[
        (~selected[CANONICAL_PROBABILITY_FIELD].between(0, 1, inclusive='both')) & selected['is_eligible_candidate'],
        ['is_eligible_candidate', 'eligibility_reason'],
    ] = [False, ELIGIBILITY_REASON_INVALID_PROBABILITY]
    selected.loc[
        (selected[CANONICAL_PROBABILITY_FIELD] < float(frozen_policy['minimum_candidate_probability'])) & selected['is_eligible_candidate'],
        ['is_eligible_candidate', 'eligibility_reason'],
    ] = [False, ELIGIBILITY_REASON_BELOW_THRESHOLD]
    selected.loc[
        selected[['stop_event_key', 'journey_id', 'station_id', 'hour_of_day']].isna().any(axis=1) & selected['is_eligible_candidate'],
        ['is_eligible_candidate', 'eligibility_reason'],
    ] = [False, ELIGIBILITY_REASON_MISSING_REQUIRED_FIELD]
    duplicate_mask = selected['stop_event_key'].duplicated(keep=False)
    selected.loc[duplicate_mask, ['is_eligible_candidate', 'eligibility_reason']] = [False, ELIGIBILITY_REASON_DUPLICATE_KEY]
    selected['priority_score'] = selected[CANONICAL_PROBABILITY_FIELD]
    return selected


def stable_sort(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.sort_values(
        by=[CANONICAL_PROBABILITY_FIELD, 'stop_event_key'],
        ascending=[False, True],
        kind='mergesort',
    ).reset_index(drop=True)


def assign_candidate_priority_ranks(frame: pd.DataFrame) -> pd.DataFrame:
    ranked_parts: list[pd.DataFrame] = []
    for horizon_id, horizon_frame in frame.groupby('horizon_id', sort=True):
        sorted_frame = stable_sort(horizon_frame)
        sorted_frame['candidate_priority_rank'] = range(1, len(sorted_frame) + 1)
        ranked_parts.append(sorted_frame)
    return pd.concat(ranked_parts, ignore_index=True) if ranked_parts else frame.copy()


def mark_lower_priority_duplicates(frame: pd.DataFrame) -> pd.DataFrame:
    marked = frame.copy()
    for (horizon_id, journey_id), group in marked.groupby(['horizon_id', 'journey_id'], sort=False):
        eligible_group = group.loc[group['is_eligible_candidate']]
        if len(eligible_group) <= 1:
            continue
        keep_index = stable_sort(eligible_group).index[0]
        drop_indices = [idx for idx in eligible_group.index if idx != keep_index]
        marked.loc[drop_indices, 'is_eligible_candidate'] = False
        marked.loc[drop_indices, 'eligibility_reason'] = ELIGIBILITY_REASON_LOWER_PRIORITY_DUPLICATE_JOURNEY
    return marked


def finalize_decision_frame(frame: pd.DataFrame, *, solver_status: str, selected_keys: set[str], objective_value: float) -> pd.DataFrame:
    decided = frame.copy()
    decided['selected_for_review'] = decided['stop_event_key'].isin(selected_keys)
    decided['objective_contribution'] = decided.apply(
        lambda row: float(row[CANONICAL_PROBABILITY_FIELD]) if row['selected_for_review'] else 0.0,
        axis=1,
    )
    decided['solver_status'] = solver_status
    decided['solver_objective_value'] = objective_value
    decided['selection_rank'] = pd.NA
    for horizon_id, horizon_frame in decided.loc[decided['selected_for_review']].groupby('horizon_id', sort=True):
        ranked = stable_sort(horizon_frame)
        decided.loc[ranked.index, 'selection_rank'] = range(1, len(ranked) + 1)
    return decided


def run_reference_selector(frame: pd.DataFrame, frozen_policy: dict[str, object]) -> pd.DataFrame:
    ranked = assign_candidate_priority_ranks(frame)
    constrained = mark_lower_priority_duplicates(ranked)
    selected_keys: set[str] = set()
    for horizon_id, horizon_frame in constrained.groupby('horizon_id', sort=True):
        eligible = stable_sort(horizon_frame.loc[horizon_frame['is_eligible_candidate']])
        capacity = int(frozen_policy['capacity_per_hour'])
        selected_keys.update(eligible.head(capacity)['stop_event_key'].tolist())
    return finalize_decision_frame(
        constrained,
        solver_status='reference',
        selected_keys=selected_keys,
        objective_value=float(constrained.loc[constrained['stop_event_key'].isin(selected_keys), CANONICAL_PROBABILITY_FIELD].sum()),
    )


def run_gurobi_selector(frame: pd.DataFrame, frozen_policy: dict[str, object]) -> pd.DataFrame:
    ranked = assign_candidate_priority_ranks(frame)
    constrained = mark_lower_priority_duplicates(ranked)
    eligible = constrained.loc[constrained['is_eligible_candidate']].copy()
    model = gp.Model('optimization_prototype')
    model.Params.OutputFlag = 0
    decision_vars = {
        row.stop_event_key: model.addVar(vtype=GRB.BINARY, name=f"x_{row.stop_event_key}")
        for row in eligible.itertuples(index=False)
    }
    model.setObjective(
        gp.quicksum(decision_vars[row.stop_event_key] * float(row.predicted_severe_delay_probability) for row in eligible.itertuples(index=False)),
        GRB.MAXIMIZE,
    )
    capacity = int(frozen_policy['capacity_per_hour'])
    for horizon_id, horizon_frame in eligible.groupby('horizon_id', sort=True):
        model.addConstr(gp.quicksum(decision_vars[key] for key in horizon_frame['stop_event_key']) <= capacity, name=f'cap_{horizon_id}')
    for (horizon_id, journey_id), group in eligible.groupby(['horizon_id', 'journey_id'], sort=True):
        model.addConstr(gp.quicksum(decision_vars[key] for key in group['stop_event_key']) <= 1, name=f'journey_{horizon_id}_{journey_id}')
    model.optimize()
    selected_keys = {key for key, var in decision_vars.items() if var.X > 0.5}
    return finalize_decision_frame(
        constrained,
        solver_status=GRB.Status.OPTIMAL if model.Status == GRB.OPTIMAL else str(model.Status),
        selected_keys=selected_keys,
        objective_value=float(model.ObjVal if model.SolCount else 0.0),
    )


def compare_selected_sets(reference: pd.DataFrame, gurobi_frame: pd.DataFrame) -> None:
    reference_keys = set(reference.loc[reference['selected_for_review'], 'stop_event_key'])
    gurobi_keys = set(gurobi_frame.loc[gurobi_frame['selected_for_review'], 'stop_event_key'])
    if reference_keys != gurobi_keys:
        raise AssertionError('Gurobi selected set does not match deterministic reference selected set')


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
        summary_rows.append(
            {
                'optimization_run_id': horizon_frame['optimization_run_id'].iloc[0],
                'execution_mode': horizon_frame['execution_mode'].iloc[0],
                'calendar_date': horizon_frame['calendar_date'].iloc[0],
                'hour_of_day': int(horizon_frame['hour_of_day'].iloc[0]),
                'horizon_id': horizon_id,
                'capacity_scenario': horizon_frame['capacity_scenario'].iloc[0],
                'capacity_per_hour': int(horizon_frame['capacity_per_hour'].iloc[0]),
                'candidate_count': candidate_count,
                'eligible_candidate_count': eligible_candidate_count,
                'selected_event_count': selected_count,
                'unused_capacity': int(horizon_frame['capacity_per_hour'].iloc[0]) - selected_count,
                'selected_probability_score_sum': float(selected['objective_contribution'].sum()),
                'actual_severe_selected_count': actual_severe_selected_count,
                'actual_severe_candidate_count': actual_severe_candidate_count,
                'candidate_prevalence': candidate_prevalence,
                'precision_at_capacity': precision_at_capacity,
                'severe_delay_coverage': severe_delay_coverage,
                'lift_over_candidate_prevalence': lift,
                'solver_status': horizon_frame['solver_status'].iloc[0],
                'model_name': horizon_frame['model_name'].iloc[0],
                'model_version': horizon_frame['model_version'].iloc[0],
                'optimized_at': horizon_frame['optimized_at'].iloc[0],
            }
        )
    return pd.DataFrame(summary_rows)


def build_evaluation(reference: pd.DataFrame, gurobi_frame: pd.DataFrame, summary: pd.DataFrame, frozen_policy: dict[str, object]) -> dict[str, object]:
    return {
        'mode': reference['execution_mode'].iloc[0],
        'capacity_scenario': frozen_policy['capacity_scenario'],
        'capacity_per_hour': frozen_policy['capacity_per_hour'],
        'minimum_candidate_probability': frozen_policy['minimum_candidate_probability'],
        'reference_selected_count': int(reference['selected_for_review'].sum()),
        'gurobi_selected_count': int(gurobi_frame['selected_for_review'].sum()),
        'selected_set_match': True,
        'horizon_count': int(len(summary)),
        'null_precision_horizon_count': int(summary['precision_at_capacity'].isna().sum()),
    }


def persist_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    try:
        connection.register('frame_view', frame)
        connection.execute(f"copy frame_view to '{path.as_posix()}' (format parquet)")
    finally:
        connection.close()


def run_mode(execution_mode: Literal['development', 'final'], frozen_policy: dict[str, object] | None = None) -> None:
    metadata = load_ml_metadata()
    if frozen_policy is None:
        if execution_mode == FINAL_MODE:
            if not FROZEN_POLICY_PATH.exists():
                raise ValueError('final mode requires frozen_policy.json')
            frozen_policy = load_frozen_policy()
        else:
            frozen_policy = build_frozen_policy(metadata=metadata)
    elif execution_mode == FINAL_MODE:
        stored_policy = load_frozen_policy() if FROZEN_POLICY_PATH.exists() else None
        if stored_policy is None:
            raise ValueError('final mode requires frozen_policy.json')
        if frozen_policy != stored_policy:
            raise ValueError('final mode must reject policy overrides and use frozen_policy.json only')

    scored_rows = load_scored_rows()
    prepared = prepare_candidates(
        scored_rows=scored_rows,
        metadata=metadata,
        execution_mode=execution_mode,
        frozen_policy=frozen_policy,
    )
    reference = run_reference_selector(prepared, frozen_policy)
    gurobi_frame = run_gurobi_selector(prepared, frozen_policy)
    compare_selected_sets(reference, gurobi_frame)
    summary = build_horizon_summary(gurobi_frame)
    evaluation = build_evaluation(reference, gurobi_frame, summary, frozen_policy)

    mode_dir = OPTIMIZATION_DIR / execution_mode
    persist_frame(gurobi_frame, mode_dir / 'event_decision.parquet')
    persist_frame(summary, mode_dir / 'horizon_summary.parquet')
    (mode_dir / 'evaluation.json').write_text(json.dumps(evaluation, indent=2), encoding='utf-8')


def main() -> None:
    metadata = load_ml_metadata()
    frozen_policy = build_frozen_policy(metadata=metadata)
    save_frozen_policy(frozen_policy)
    run_mode(DEVELOPMENT_MODE, frozen_policy)
    run_mode(FINAL_MODE, frozen_policy)


if __name__ == '__main__':
    main()
