"""# @meta
# type: test
# distribution_tier: starter_kit
# scope: unit
# domain: optimization
# covers:
# - Optimization candidate preparation and frozen policy contracts
# - Deterministic baseline and Gurobi policy behavior
# - Comparison metric and null-handling contracts
# tags:
# - fast
# - ci-safe
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_optimization_prototype.py'
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


OPT = load_module('run_optimization_prototype', SCRIPT_PATH)
build_search_config = OPT.build_search_config
build_frozen_policy = OPT.build_frozen_policy
prepare_candidates = OPT.prepare_candidates
select_policy = OPT.select_policy
build_horizon_summary = OPT.build_horizon_summary
build_policy_comparison = OPT.build_policy_comparison
build_pairwise_policy_diagnostics = OPT.build_pairwise_policy_diagnostics
CANONICAL_PROBABILITY_FIELD = OPT.CANONICAL_PROBABILITY_FIELD
DEFAULT_CAPACITY_PER_HOUR = OPT.DEFAULT_CAPACITY_PER_HOUR


def make_metadata(*, threshold: float = 0.4) -> dict[str, object]:
    return {
        'selected_threshold': threshold,
        'model_name': 'logistic_regression',
        'model_version': '2026-06-28-v1',
        'target_column': 'is_departure_severe_delay',
    }


def make_scored_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            'stop_event_key': ['A1', 'A2', 'A3', 'B1', 'B2', 'C1', 'D1'],
            'journey_id': ['J1', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6'],
            'service_date': pd.to_datetime([
                '2025-03-19 08:00:00',
                '2025-03-19 08:10:00',
                '2025-03-19 08:20:00',
                '2025-03-19 08:30:00',
                '2025-03-19 08:40:00',
                '2025-03-19 09:00:00',
                '2025-03-19 10:00:00',
            ]),
            'station_id': ['S1', 'S1', 'S2', 'S1', 'S3', 'S4', 'S5'],
            'station_name': ['A', 'A', 'B', 'A', 'C', 'D', 'E'],
            'train_type': ['ICE', 'ICE', 'IC', 'RE', 'RE', 'ICE', 'IC'],
            'line_number': ['1', '1', '2', '3', '3', '4', '5'],
            'train_service_key': ['TS1', 'TS1', 'TS2', 'TS3', 'TS4', 'TS5', 'TS6'],
            'service_class': ['long', 'long', 'long', 'regional', 'regional', 'long', 'long'],
            'prediction_split': ['validation'] * 6 + ['test'],
            'hour_of_day': [8, 8, 8, 8, 8, 9, 10],
            'selected_threshold': [0.4] * 7,
            'model_name': ['logistic_regression'] * 7,
            'model_version': ['2026-06-28-v1'] * 7,
            'predicted_probability': [0.95, 0.90, 0.89, 0.88, 0.72, 0.60, 0.91],
            'actual_is_departure_severe_delay': [True, False, True, True, False, False, True],
        }
    )


def test_build_search_config_contains_split_contract() -> None:
    search_config = build_search_config()

    assert search_config['canonical_tuning_capacity_per_hour'] == DEFAULT_CAPACITY_PER_HOUR
    assert search_config['scenario_capacities'] == [1, 3, 5, 10]
    assert search_config['diagnostic_station_excess_penalty_lambda'] == 0.0
    assert search_config['eligible_frozen_station_excess_penalty_lambdas'] == [0.05, 0.1, 0.2]
    assert search_config['development_allowed_solver_statuses'] == ['OPTIMAL', 'TIME_LIMIT_WITH_INCUMBENT']
    assert search_config['final_allowed_solver_statuses'] == ['OPTIMAL', 'TIME_LIMIT_WITH_INCUMBENT']
    json.dumps(search_config)


def test_prepare_candidates_sets_feasible_selection_target() -> None:
    metadata = make_metadata()
    search_config = build_search_config()
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=1,
        frozen_station_excess_penalty_lambda=0.1,
    )
    prepared = prepare_candidates(
        scored_rows=make_scored_rows(),
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )

    horizon_8 = prepared.loc[prepared['horizon_id'] == '2025-03-19|8']
    assert CANONICAL_PROBABILITY_FIELD in prepared.columns
    assert prepared['prediction_split'].eq('validation').all()
    assert horizon_8['feasible_selection_target'].nunique() == 1
    assert horizon_8['feasible_selection_target'].iloc[0] == 3


def test_capacity_one_keeps_ml_first_and_gurobi_equal() -> None:
    metadata = make_metadata()
    search_config = build_search_config()
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=1,
        frozen_station_excess_penalty_lambda=0.2,
        capacity_per_hour=1,
    )
    prepared = prepare_candidates(
        scored_rows=make_scored_rows(),
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )

    ml_first = select_policy(prepared, 'ml_first', frozen_policy=frozen_policy, search_config=search_config)
    gurobi = select_policy(prepared, 'gurobi_soft_station_penalty', frozen_policy=frozen_policy, search_config=search_config)

    ml_keys = set(ml_first.loc[ml_first['selected_for_review'], 'stop_event_key'])
    gurobi_keys = set(gurobi.loc[gurobi['selected_for_review'], 'stop_event_key'])
    assert ml_keys == gurobi_keys


def test_random_policy_is_row_order_invariant() -> None:
    metadata = make_metadata()
    search_config = build_search_config()
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=1,
        frozen_station_excess_penalty_lambda=0.1,
    )
    prepared = prepare_candidates(
        scored_rows=make_scored_rows(),
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )
    shuffled = prepared.sample(frac=1.0, random_state=77).reset_index(drop=True)

    first = select_policy(prepared, 'random', frozen_policy=frozen_policy, search_config=search_config)
    second = select_policy(shuffled, 'random', frozen_policy=frozen_policy, search_config=search_config)

    assert first['selected_for_review'].tolist() == second['selected_for_review'].tolist()


def test_policy_comparison_uses_defined_formulas() -> None:
    metadata = make_metadata()
    search_config = build_search_config()
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=1,
        frozen_station_excess_penalty_lambda=0.1,
    )
    prepared = prepare_candidates(
        scored_rows=make_scored_rows(),
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )

    policies = [
        select_policy(prepared, 'random', frozen_policy=frozen_policy, search_config=search_config),
        select_policy(prepared, 'ml_first', frozen_policy=frozen_policy, search_config=search_config),
        select_policy(prepared, 'constrained_greedy', frozen_policy=frozen_policy, search_config=search_config),
        select_policy(prepared, 'gurobi_soft_station_penalty', frozen_policy=frozen_policy, search_config=search_config),
    ]
    comparison = build_policy_comparison(policies)

    ml_first = comparison.loc[comparison['policy_name'] == 'ml_first'].iloc[0]
    assert ml_first['capacity_per_hour'] == DEFAULT_CAPACITY_PER_HOUR
    assert ml_first['selected_event_count'] == int(policies[1]['selected_for_review'].sum())
    assert ml_first['expected_risk_score_captured'] == pytest.approx(
        policies[1].loc[policies[1]['selected_for_review'], CANONICAL_PROBABILITY_FIELD].sum()
    )
    assert {'random', 'ml_first', 'constrained_greedy', 'gurobi_soft_station_penalty'} == set(comparison['policy_name'])


def test_pairwise_diagnostics_report_partial_difference() -> None:
    metadata = make_metadata()
    search_config = build_search_config()
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=1,
        frozen_station_excess_penalty_lambda=0.2,
    )
    prepared = prepare_candidates(
        scored_rows=make_scored_rows(),
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )
    ml_first = select_policy(prepared, 'ml_first', frozen_policy=frozen_policy, search_config=search_config)
    gurobi = select_policy(prepared, 'gurobi_soft_station_penalty', frozen_policy=frozen_policy, search_config=search_config)

    diagnostics = build_pairwise_policy_diagnostics(ml_first, gurobi)

    assert diagnostics['matching_horizon_count'] + diagnostics['differing_horizon_count'] == diagnostics['horizon_count']
    assert 0.0 <= diagnostics['selected_set_match_rate'] <= 1.0


def test_horizon_summary_uses_null_for_undefined_ratios() -> None:
    metadata = make_metadata(threshold=0.99)
    search_config = build_search_config()
    frozen_policy = build_frozen_policy(
        metadata=metadata,
        search_config=search_config,
        preferred_station_load_per_station_hour=1,
        frozen_station_excess_penalty_lambda=0.1,
        minimum_candidate_probability=0.99,
        capacity_per_hour=1,
    )
    prepared = prepare_candidates(
        scored_rows=make_scored_rows(),
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )
    decisions = select_policy(prepared, 'ml_first', frozen_policy=frozen_policy, search_config=search_config)
    summary = build_horizon_summary(decisions)

    zero_horizon = summary.loc[summary['horizon_id'] == '2025-03-19|9']
    assert zero_horizon['eligible_candidate_count'].item() == 0
    assert pd.isna(zero_horizon['candidate_prevalence'].item())
    assert pd.isna(zero_horizon['precision_at_capacity'].item())
    assert pd.isna(zero_horizon['severe_delay_coverage'].item())
    assert pd.isna(zero_horizon['lift_over_candidate_prevalence'].item())
