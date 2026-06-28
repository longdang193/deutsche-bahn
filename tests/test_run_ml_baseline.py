"""# @meta
# type: test
# distribution_tier: starter_kit
# scope: unit
# domain: ml
# covers:
# - ML baseline split integrity
# - ML baseline feature allowlist enforcement
# tags:
# - fast
# - ci-safe
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / 'scripts' / 'run_ml_baseline.py'
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

ML_BASELINE = load_module('run_ml_baseline', SCRIPT_PATH)
ALLOWED_FEATURE_COLUMNS = ML_BASELINE.ALLOWED_FEATURE_COLUMNS
EXCLUDED_FEATURE_COLUMNS = ML_BASELINE.EXCLUDED_FEATURE_COLUMNS
assign_journey_anchor_splits = ML_BASELINE.assign_journey_anchor_splits
build_modeling_frame = ML_BASELINE.build_modeling_frame
coerce_feature_types = ML_BASELINE.coerce_feature_types


def test_build_modeling_frame_excludes_leakage_and_preserves_journey_split() -> None:
    frame = pd.DataFrame(
        {
            "stop_event_key": [1, 2, 3, 4, 5, 6],
            "journey_id": ["J1", "J1", "J2", "J3", "J4", "J5"],
            "service_date": pd.to_datetime(
                [
                    "2025-03-01",
                    "2025-03-01",
                    "2025-03-02",
                    "2025-03-03",
                    "2025-03-04",
                    "2025-03-05",
                ]
            ),
            "station_id": ["A", "A", "B", "C", "D", "E"],
            "train_type": ["ICE"] * 6,
            "line_number": ["1"] * 6,
            "service_class": ["long_distance"] * 6,
            "day_name": ["Sat", "Sat", "Sun", "Mon", "Tue", "Wed"],
            "time_band": ["morning"] * 6,
            "hour_of_day": [8, 9, 10, 11, 12, 13],
            "day_of_week": [6, 6, 7, 1, 2, 3],
            "month": [3] * 6,
            "week_of_year": [9, 9, 9, 10, 10, 10],
            "arrival_delay_min": [5.0, 7.0, 0.0, 2.0, 1.0, 8.0],
            "is_weekend": [True, True, True, False, False, False],
            "is_cancellation": [False] * 6,
            "is_arrival_cancelled": [False] * 6,
            "has_arrival_time_data": [True] * 6,
            "departure_delay_min": [16.0, 17.0, 0.0, 0.0, 20.0, 0.0],
            "delay_bucket": ["15_to_29"] * 6,
            "has_departure_time_data": [True] * 6,
            "event_delay_min": [16.0, 17.0, 0.0, 0.0, 20.0, 0.0],
            "is_delayed": [True, True, False, False, True, False],
            "is_severe_delay": [True, True, False, False, True, False],
            "is_extreme_delay": [False] * 6,
            "is_departure_cancelled": [False] * 6,
            "has_delay_measurement": [True] * 6,
            "is_departure_severe_delay": [True, True, False, False, True, False],
        }
    )

    split_frame = assign_journey_anchor_splits(frame)
    modeling_frame = build_modeling_frame(split_frame)
    modeling_frame = coerce_feature_types(modeling_frame)

    assert str(modeling_frame["is_weekend"].dtype) == "Int64"
    assert set(ALLOWED_FEATURE_COLUMNS) == {
        "station_id",
        "train_type",
        "line_number",
        "service_class",
        "day_name",
        "time_band",
        "hour_of_day",
        "day_of_week",
        "month",
        "week_of_year",
        "arrival_delay_min",
        "is_weekend",
        "is_cancellation",
        "is_arrival_cancelled",
        "has_arrival_time_data",
    }
    assert "delay_bucket" in EXCLUDED_FEATURE_COLUMNS
    assert "has_departure_time_data" in EXCLUDED_FEATURE_COLUMNS
    assert "delay_bucket" not in modeling_frame.columns
    assert "has_departure_time_data" not in modeling_frame.columns
    assert set(modeling_frame["prediction_split"]) == {"train", "validation", "test"}

    split_counts = modeling_frame.groupby("journey_id")["prediction_split"].nunique()
    assert split_counts.eq(1).all()

    grouped = (
        modeling_frame.groupby("prediction_split")["journey_anchor_date"]
        .agg(["min", "max"])
        .sort_index()
    )
    assert grouped.loc["train", "max"] < grouped.loc["validation", "min"]
    assert grouped.loc["validation", "max"] < grouped.loc["test", "min"]


def test_assign_journey_anchor_splits_requires_all_three_splits() -> None:
    frame = pd.DataFrame(
        {
            "journey_id": ["J1", "J2"],
            "service_date": pd.to_datetime(["2025-03-01", "2025-03-02"]),
        }
    )

    with pytest.raises(ValueError, match="at least three unique journey anchor dates"):
        assign_journey_anchor_splits(frame)


