"""# @meta
# type: test
# distribution_tier: starter_kit
# scope: unit
# domain: analytics
# covers:
# - Power BI semantic export contract and reconciliation
# - Source consistency and dimension validation
# - Dashboard handoff metadata constraints
# tags:
# - fast
# - ci-safe
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'build_power_bi_semantic_dataset.py'
SCRIPTS_ROOT = str(REPO_ROOT / 'scripts')

if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load {path.name}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SEM = load_module('build_power_bi_semantic_dataset', SCRIPT_PATH)


def read_parquet(path: Path) -> pd.DataFrame:
    connection = duckdb.connect()
    try:
        return connection.execute(f"select * from read_parquet('{path.as_posix()}')").fetch_df()
    finally:
        connection.close()


@pytest.fixture()
def contract() -> dict[str, object]:
    return json.loads((REPO_ROOT / 'data' / 'scoped' / 'power_bi' / 'semantic_contract.json').read_text(encoding='utf-8'))


@pytest.fixture()
def manifest() -> dict[str, object]:
    return json.loads((REPO_ROOT / 'data' / 'scoped' / 'power_bi' / 'dashboard_mvp_manifest.json').read_text(encoding='utf-8'))


@pytest.fixture()
def synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], dict[str, object]]:
    event_source = pd.DataFrame(
        {
            'optimization_run_id': ['run-1', 'run-1', 'run-1'],
            'execution_mode': ['final', 'final', 'final'],
            'prediction_split': ['test', 'test', 'test'],
            'stop_event_key': ['A', 'B', 'C'],
            'journey_id': ['J1', 'J2', 'J3'],
            'station_id': ['S1', 'S1', 'S2'],
            'station_name': ['Berlin Hbf', 'Berlin Hbf', None],
            'train_type': ['ICE', 'ICE', None],
            'line_number': ['10', '10', None],
            'train_service_key': [1001, 1002, 1003],
            'service_class_x': ['long', 'long', 'regional'],
            'service_class_y': [None, 'long', None],
            'calendar_date': ['2025-03-19', '2025-03-19', '2025-03-19'],
            'hour_of_day': [8, 8, 9],
            'horizon_id': ['2025-03-19|8', '2025-03-19|8', '2025-03-19|9'],
            'capacity_scenario': ['hourly_capacity_3', 'hourly_capacity_3', 'hourly_capacity_3'],
            'capacity_per_hour': [3, 3, 3],
            'minimum_candidate_probability': [0.4, 0.4, 0.4],
            'model_name': ['logistic_regression', 'logistic_regression', 'logistic_regression'],
            'model_version': ['2026-06-28-v1', '2026-06-28-v1', '2026-06-28-v1'],
            'selected_threshold': [0.4, 0.4, 0.4],
            'selected_for_review': [True, False, True],
            'actual_is_departure_severe_delay': [True, False, False],
            'is_eligible_candidate': [True, True, True],
            'objective_contribution': [0.9, 0.5, 0.4],
            'predicted_severe_delay_probability': [0.9, 0.5, 0.4],
            'eligibility_reason': ['eligible', 'eligible', 'eligible'],
            'candidate_priority_rank': [1, 2, 1],
            'selection_rank': [1, None, 1],
            'priority_score': [0.9, 0.5, 0.4],
            'solver_status': [2, 2, 2],
            'optimized_at': ['2026-06-28T12:26:49+00:00'] * 3,
        }
    )
    horizon_source = pd.DataFrame(
        {
            'optimization_run_id': ['run-1', 'run-1'],
            'execution_mode': ['final', 'final'],
            'calendar_date': ['2025-03-19', '2025-03-19'],
            'hour_of_day': [8, 9],
            'horizon_id': ['2025-03-19|8', '2025-03-19|9'],
            'capacity_scenario': ['hourly_capacity_3', 'hourly_capacity_3'],
            'capacity_per_hour': [3, 3],
            'candidate_count': [2, 1],
            'eligible_candidate_count': [2, 1],
            'selected_event_count': [1, 1],
            'unused_capacity': [2, 2],
            'selected_probability_score_sum': [0.9, 0.4],
            'actual_severe_selected_count': [1, 0],
            'actual_severe_candidate_count': [1, 0],
            'candidate_prevalence': [0.5, 0.0],
            'precision_at_capacity': [1.0, 0.0],
            'severe_delay_coverage': [1.0, None],
            'lift_over_candidate_prevalence': [2.0, None],
            'solver_status': [2, 2],
            'model_name': ['logistic_regression', 'logistic_regression'],
            'model_version': ['2026-06-28-v1', '2026-06-28-v1'],
            'optimized_at': ['2026-06-28T12:26:49+00:00', '2026-06-28T12:26:49+00:00'],
        }
    )
    evaluation = {
        'mode': 'final',
        'capacity_scenario': 'hourly_capacity_3',
        'capacity_per_hour': 3,
        'minimum_candidate_probability': 0.4,
        'reference_selected_count': 2,
        'gurobi_selected_count': 2,
        'selected_set_match': True,
        'horizon_count': 2,
        'null_precision_horizon_count': 0,
    }
    policy = {
        'policy_version': '2026-06-28-v1',
        'execution_modes': ['development', 'final'],
        'canonical_probability_field': 'predicted_severe_delay_probability',
        'threshold_source': 'data/scoped/ml/evaluation.json',
        'minimum_candidate_probability': 0.4,
        'capacity_scenario': 'hourly_capacity_3',
        'capacity_per_hour': 3,
        'constraint_set': ['hourly_capacity', 'one_per_journey_per_horizon'],
        'tie_break_rule': ['predicted_severe_delay_probability desc', 'stop_event_key asc'],
        'metric_definitions': ['precision_at_capacity', 'severe_delay_coverage', 'lift_over_candidate_prevalence', 'candidate_prevalence'],
        'model_name': 'logistic_regression',
        'model_version': '2026-06-28-v1',
        'selected_threshold': 0.4,
        'frozen_at': '2026-06-28T10:26:49.750462+00:00',
    }
    return event_source, horizon_source, evaluation, policy


def test_export_power_bi_semantic_dataset_real_outputs(tmp_path: Path, contract: dict[str, object], manifest: dict[str, object]) -> None:
    contract_path = REPO_ROOT / 'data' / 'scoped' / 'power_bi' / 'semantic_contract.json'
    manifest_path = REPO_ROOT / 'data' / 'scoped' / 'power_bi' / 'dashboard_mvp_manifest.json'
    contract_hash_before = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    manifest_hash_before = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    artifacts = SEM.export_power_bi_semantic_dataset(output_dir=tmp_path)

    expected_names = {
        'fact_event_decision.parquet',
        'fact_horizon_summary.parquet',
        'dim_date_hour.parquet',
        'dim_station.parquet',
        'dim_train_service.parquet',
        'dim_scenario.parquet',
    }
    assert {path.name for path in tmp_path.glob('*.parquet')} == expected_names
    assert len(artifacts.event_fact) == 743
    assert len(artifacts.horizon_fact) == 137
    assert artifacts.event_fact['scenario_key'].nunique() == 1
    assert artifacts.event_fact['scenario_key'].iloc[0] == '2026-06-28-v1'
    assert artifacts.event_fact['execution_mode'].eq('final').all()
    assert artifacts.event_fact['prediction_split'].eq('test').all()
    assert artifacts.horizon_fact['scenario_key'].nunique() == 1

    event_fact = read_parquet(tmp_path / 'fact_event_decision.parquet')
    horizon_fact = read_parquet(tmp_path / 'fact_horizon_summary.parquet')
    dim_date_hour = read_parquet(tmp_path / 'dim_date_hour.parquet')
    dim_station = read_parquet(tmp_path / 'dim_station.parquet')
    dim_train_service = read_parquet(tmp_path / 'dim_train_service.parquet')
    dim_scenario = read_parquet(tmp_path / 'dim_scenario.parquet')

    assert event_fact.columns.tolist() == [column['name'] for column in contract['tables']['fact_event_decision']['columns']]
    assert horizon_fact.columns.tolist() == [column['name'] for column in contract['tables']['fact_horizon_summary']['columns']]
    assert dim_date_hour['horizon_id'].is_unique
    assert dim_station['station_id'].is_unique
    assert dim_train_service['train_service_key'].is_unique
    assert dim_scenario['scenario_key'].is_unique
    assert event_fact['horizon_id'].isin(dim_date_hour['horizon_id']).all()
    assert horizon_fact['horizon_id'].isin(dim_date_hour['horizon_id']).all()
    assert event_fact['station_id'].isin(dim_station['station_id']).all()
    assert event_fact['train_service_key'].isin(dim_train_service['train_service_key']).all()
    assert event_fact['scenario_key'].isin(dim_scenario['scenario_key']).all()
    assert horizon_fact['scenario_key'].isin(dim_scenario['scenario_key']).all()
    assert manifest['page_count'] == 2
    assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == contract_hash_before
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == manifest_hash_before


def test_build_artifacts_rejects_station_conflicts(
    synthetic_inputs: tuple[pd.DataFrame, pd.DataFrame, dict[str, object], dict[str, object]],
    contract: dict[str, object],
    manifest: dict[str, object],
) -> None:
    event_source, horizon_source, evaluation, policy = synthetic_inputs
    event_source.loc[1, 'station_name'] = 'BERLIN HBF'

    with pytest.raises(ValueError, match='one station_id must map to one station attribute set'):
        SEM.build_artifacts(event_source, horizon_source, evaluation, policy, contract, manifest)


def test_build_artifacts_rejects_horizon_reconciliation_drift(
    synthetic_inputs: tuple[pd.DataFrame, pd.DataFrame, dict[str, object], dict[str, object]],
    contract: dict[str, object],
    manifest: dict[str, object],
) -> None:
    event_source, horizon_source, evaluation, policy = synthetic_inputs
    horizon_source.loc[horizon_source['horizon_id'] == '2025-03-19|8', 'selected_event_count'] = 2

    with pytest.raises(ValueError, match='selected_event_count'):
        SEM.build_artifacts(event_source, horizon_source, evaluation, policy, contract, manifest)


def test_build_artifacts_marks_hidden_ratios_and_display_rules(
    synthetic_inputs: tuple[pd.DataFrame, pd.DataFrame, dict[str, object], dict[str, object]],
    contract: dict[str, object],
    manifest: dict[str, object],
) -> None:
    event_source, horizon_source, evaluation, policy = synthetic_inputs
    artifacts = SEM.build_artifacts(event_source, horizon_source, evaluation, policy, contract, manifest)

    horizon_columns = {column['name']: column for column in contract['tables']['fact_horizon_summary']['columns']}
    assert horizon_columns['candidate_prevalence']['visible'] is False
    assert horizon_columns['precision_at_capacity']['purpose'] == 'source reconciliation only'
    assert horizon_columns['severe_delay_coverage']['visible'] is False
    assert horizon_columns['lift_over_candidate_prevalence']['default_aggregation'] == 'none'

    event_columns = {column['name']: column for column in contract['tables']['fact_event_decision']['columns']}
    assert event_columns['station_name']['visible'] is False
    assert event_columns['train_type']['visible'] is False
    assert event_columns['line_number']['visible'] is False
    assert event_columns['service_class']['visible'] is False

    date_hour_columns = {column['name']: column for column in contract['tables']['dim_date_hour']['columns']}
    assert date_hour_columns['date_label']['sort_by'] == 'calendar_date'
    assert date_hour_columns['hour_label']['sort_by'] == 'hour_of_day'
    assert artifacts.dim_date_hour['hour_label'].tolist() == ['08:00-08:59', '09:00-09:59']
    assert artifacts.dim_scenario['scenario_display_name'].iloc[0].startswith('Prototype hourly_capacity_3')
