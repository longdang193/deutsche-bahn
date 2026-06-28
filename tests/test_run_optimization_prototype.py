"""# @meta
# type: test
# distribution_tier: starter_kit
# scope: unit
# domain: optimization
# covers:
# - Optimization candidate preparation and policy freezing
# - Deterministic reference and Gurobi selection equality
# - Descriptive summary metric edge-case handling
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
build_frozen_policy = OPT.build_frozen_policy
prepare_candidates = OPT.prepare_candidates
run_reference_selector = OPT.run_reference_selector
run_gurobi_selector = OPT.run_gurobi_selector
build_horizon_summary = OPT.build_horizon_summary
CANONICAL_PROBABILITY_FIELD = OPT.CANONICAL_PROBABILITY_FIELD
CAPACITY_SCENARIO = OPT.DEFAULT_CAPACITY_SCENARIO


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
            'stop_event_key': ['A1', 'A2', 'A3', 'B1', 'C1', 'D1'],
            'journey_id': ['J1', 'J1', 'J2', 'J3', 'J4', 'J5'],
            'service_date': pd.to_datetime([
                '2025-03-19 08:00:00',
                '2025-03-19 08:10:00',
                '2025-03-19 08:20:00',
                '2025-03-19 09:00:00',
                '2025-03-19 10:00:00',
                '2025-03-19 11:00:00',
            ]),
            'station_id': ['S1', 'S1', 'S2', 'S3', 'S4', 'S5'],
            'station_name': ['A', 'A', 'B', 'C', 'D', 'E'],
            'train_type': ['ICE', 'ICE', 'IC', 'RE', 'ICE', 'IC'],
            'line_number': ['1', '1', '2', '3', '4', '5'],
            'train_service_key': ['TS1', 'TS1', 'TS2', 'TS3', 'TS4', 'TS5'],
            'service_class': ['long', 'long', 'long', 'regional', 'long', 'long'],
            'prediction_split': ['validation'] * 5 + ['test'],
            'hour_of_day': [8, 8, 8, 9, 10, 11],
            'selected_threshold': [0.4] * 6,
            'model_name': ['logistic_regression'] * 6,
            'model_version': ['2026-06-28-v1'] * 6,
            'predicted_probability': [0.91, 0.87, 0.80, 0.35, 0.40, 0.95],
            'actual_is_departure_severe_delay': [True, False, True, False, False, True],
        }
    )


def test_prepare_candidates_normalizes_probability_and_preserves_scoped_rows() -> None:
    metadata = make_metadata()
    scored_rows = make_scored_rows()
    frozen_policy = build_frozen_policy(metadata=metadata)

    prepared = prepare_candidates(
        scored_rows=scored_rows,
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )

    assert CANONICAL_PROBABILITY_FIELD in prepared.columns
    assert 'predicted_probability' not in prepared.columns
    assert prepared['prediction_split'].eq('validation').all()
    assert len(prepared) == 5
    assert prepared['is_eligible_candidate'].tolist() == [True, True, True, False, True]
    assert prepared.loc[prepared['stop_event_key'] == 'B1', 'eligibility_reason'].item() == 'below_minimum_candidate_probability'
    assert prepared['capacity_scenario'].nunique() == 1
    assert prepared['capacity_scenario'].nunique() == 1
    assert prepared['capacity_scenario'].iloc[0] == CAPACITY_SCENARIO


def test_prepare_candidates_rejects_model_version_drift() -> None:
    metadata = make_metadata()
    scored_rows = make_scored_rows()
    scored_rows.loc[1, 'model_version'] = 'bad-version'
    frozen_policy = build_frozen_policy(metadata=metadata)

    with pytest.raises(ValueError, match='exactly one model_version'):
        prepare_candidates(
            scored_rows=scored_rows,
            metadata=metadata,
            execution_mode='development',
            frozen_policy=frozen_policy,
        )


def test_reference_and_gurobi_match_without_label_leakage() -> None:
    metadata = make_metadata()
    scored_rows = make_scored_rows()
    frozen_policy = build_frozen_policy(metadata=metadata, capacity_per_hour=2)
    prepared = prepare_candidates(
        scored_rows=scored_rows,
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )

    reference = run_reference_selector(prepared, frozen_policy)
    gurobi = run_gurobi_selector(prepared, frozen_policy)
    label_swapped = prepared.copy()
    label_swapped['actual_is_departure_severe_delay'] = ~label_swapped['actual_is_departure_severe_delay']
    relabeled = run_reference_selector(label_swapped, frozen_policy)

    assert reference['selected_for_review'].sum() == 2
    assert set(reference.loc[reference['selected_for_review'], 'stop_event_key']) == set(gurobi.loc[gurobi['selected_for_review'], 'stop_event_key'])
    assert reference['selected_for_review'].tolist() == relabeled['selected_for_review'].tolist()
    assert reference.loc[reference['selected_for_review'], 'objective_contribution'].sum() == pytest.approx(reference['solver_objective_value'].iloc[0])


def test_horizon_summary_uses_null_for_undefined_ratios() -> None:
    metadata = make_metadata()
    scored_rows = make_scored_rows()
    frozen_policy = build_frozen_policy(metadata=metadata, capacity_per_hour=1, minimum_candidate_probability=0.99)
    prepared = prepare_candidates(
        scored_rows=scored_rows,
        metadata=metadata,
        execution_mode='development',
        frozen_policy=frozen_policy,
    )
    decisions = run_reference_selector(prepared, frozen_policy)
    summary = build_horizon_summary(decisions)

    zero_horizon = summary.loc[summary['horizon_id'] == '2025-03-19|10']
    assert len(summary) == 3
    assert zero_horizon['eligible_candidate_count'].item() == 0
    assert pd.isna(zero_horizon['candidate_prevalence'].item())
    assert pd.isna(zero_horizon['precision_at_capacity'].item())
    assert pd.isna(zero_horizon['severe_delay_coverage'].item())
    assert pd.isna(zero_horizon['lift_over_candidate_prevalence'].item())


def test_frozen_policy_contains_single_source_runtime_contract() -> None:
    metadata = make_metadata()
    frozen_policy = build_frozen_policy(metadata=metadata)

    assert frozen_policy['canonical_probability_field'] == CANONICAL_PROBABILITY_FIELD
    assert frozen_policy['threshold_source'] == 'data/scoped/ml/evaluation.json'
    assert frozen_policy['minimum_candidate_probability'] == 0.4
    assert frozen_policy['capacity_scenario'] == CAPACITY_SCENARIO
    json.dumps(frozen_policy)
