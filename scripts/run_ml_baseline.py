"""# @meta
# type: script
# distribution_tier: starter_kit
# scope: local
# domain: ml
# tags:
# - ml
# - duckdb
# - sklearn
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "scoped" / "local_scope_bronze.duckdb"
SCOPED_DIR = REPO_ROOT / "data" / "scoped"
MANIFEST_PATH = SCOPED_DIR / "manifests" / "scope_expansion_manifest.json"
OUTPUT_DIR = SCOPED_DIR / "ml"
MODEL_PATH = OUTPUT_DIR / "severe_delay_model.joblib"
SCORED_OUTPUT_PATH = OUTPUT_DIR / "scored_stop_events.parquet"
EVALUATION_PATH = OUTPUT_DIR / "evaluation.json"
STAGE_A_SCORED_OUTPUT_PATH = OUTPUT_DIR / "stage_a_frozen_scored_stop_events.parquet"
STAGE_A_EVALUATION_PATH = OUTPUT_DIR / "stage_a_scope_diagnostic.json"
GOLD_TABLE_NAME = "gold.feature_stop_event"
MODEL_NAME = "logistic_regression"
MODEL_VERSION = "2026-06-28-v1"
TRAIN_SPLIT = "train"
VALIDATION_SPLIT = "validation"
TEST_SPLIT = "test"
SPLIT_ORDER = (TRAIN_SPLIT, VALIDATION_SPLIT, TEST_SPLIT)
ALLOWED_FEATURE_COLUMNS = (
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
)
EXCLUDED_FEATURE_COLUMNS = (
    "stop_event_key",
    "date_key",
    "hour_key",
    "station_key",
    "train_service_key",
    "service_date",
    "calendar_date",
    "journey_id",
    "stop_sequence",
    "station_name",
    "train_number",
    "year",
    "provider_delay_in_min",
    "departure_delay_min",
    "delay_change_min",
    "event_delay_min",
    "has_delay_measurement",
    "is_delayed",
    "is_severe_delay",
    "is_extreme_delay",
    "delay_bucket",
    "is_departure_cancelled",
    "has_departure_time_data",
    "is_active_stop",
    "is_departure_severe_delay",
    "journey_anchor_date",
    "prediction_split",
)
IDENTIFIER_COLUMNS = (
    "stop_event_key",
    "journey_id",
    "service_date",
    "station_id",
    "train_type",
    "line_number",
    "source_file",
)
TARGET_COLUMN = "is_departure_severe_delay"
CATEGORICAL_COLUMNS = (
    "station_id",
    "train_type",
    "line_number",
    "service_class",
    "day_name",
    "time_band",
)
NUMERIC_COLUMNS = (
    "hour_of_day",
    "day_of_week",
    "month",
    "week_of_year",
    "arrival_delay_min",
)
BOOLEAN_COLUMNS = (
    "is_weekend",
    "is_cancellation",
    "is_arrival_cancelled",
    "has_arrival_time_data",
)


@dataclass(frozen=True)
class SplitMetrics:
    split: str
    row_count: int
    journey_count: int
    positive_count: int
    negative_count: int
    prevalence: float
    anchor_date_min: str
    anchor_date_max: str


@dataclass(frozen=True)
class EvaluationBundle:
    duckdb_path: str
    source_table: str
    model_name: str
    model_version: str
    target_column: str
    feature_columns: list[str]
    selected_threshold: float
    split_metrics: list[dict[str, object]]
    validation_metrics: dict[str, object]
    test_metrics: dict[str, object]
    excluded_feature_columns: list[str]
    scored_output_path: str
    model_path: str
    scored_row_count: int
    scored_split_counts: dict[str, int]
    scored_at: str


def load_gold_frame() -> pd.DataFrame:
    connection = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        return connection.execute(
            f"select * from {GOLD_TABLE_NAME}"
        ).fetch_df()
    finally:
        connection.close()

def load_scope_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def stage_a_probability_column(model_name: str, model_version: str) -> str:
    return f"stage_a_frozen_probability__{model_name}__{model_version}"


def add_scope_slice_labels(frame: pd.DataFrame, manifest: dict[str, object]) -> pd.DataFrame:
    labeled = frame.copy()
    baseline_source_file = str(manifest["baseline_source_file_name"])
    added_source_file = str(manifest["added_week_source_file_name"])
    added_week_start = pd.Timestamp(str(manifest["added_week_start_date"]))
    added_week_end = pd.Timestamp(str(manifest["added_week_end_date"]))
    service_date = pd.to_datetime(labeled["service_date"]).dt.normalize()
    labeled["scope_slice"] = "unknown_scope_slice"
    labeled.loc[labeled["source_file"] == baseline_source_file, "scope_slice"] = "baseline_month"
    added_mask = (
        (labeled["source_file"] == added_source_file)
        & (service_date >= added_week_start)
        & (service_date <= added_week_end)
    )
    labeled.loc[added_mask, "scope_slice"] = "added_disrupted_week"
    return labeled


def persist_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    try:
        connection.register("frame_view", frame)
        connection.execute(f"copy frame_view to '{path.as_posix()}' (format parquet)")
    finally:
        connection.close()


def build_stage_a_scope_diagnostic(
    *,
    pipeline: Pipeline,
    selected_threshold: float,
    modeling_frame: pd.DataFrame,
    manifest: dict[str, object],
    model_name: str,
    model_version: str,
) -> dict[str, object]:
    scored = modeling_frame.copy()
    probability_column = stage_a_probability_column(model_name, model_version)
    probabilities = pipeline.predict_proba(scored.loc[:, ALLOWED_FEATURE_COLUMNS])[:, 1]
    scored[probability_column] = probabilities
    scored["stage_a_predicted_severe_delay_probability"] = probabilities
    scored["stage_a_selected_by_frozen_threshold"] = scored[probability_column] >= selected_threshold
    scored = add_scope_slice_labels(scored, manifest)
    persist_frame(scored, STAGE_A_SCORED_OUTPUT_PATH)

    scope_rows: list[dict[str, object]] = []
    for scope_slice, scope_frame in scored.groupby("scope_slice", sort=True):
        selected_mask = scope_frame["stage_a_selected_by_frozen_threshold"].fillna(False).astype(bool)
        scope_rows.append(
            {
                "scope_slice": scope_slice,
                "row_count": int(scope_frame.shape[0]),
                "journey_count": int(scope_frame["journey_id"].nunique()),
                "severe_event_count": int(scope_frame[TARGET_COLUMN].fillna(False).astype(bool).sum()),
                "selected_by_frozen_threshold_count": int(selected_mask.sum()),
                "selected_severe_event_count": int(scope_frame.loc[selected_mask, TARGET_COLUMN].fillna(False).astype(bool).sum()),
                "mean_probability": float(scope_frame[probability_column].mean()),
                "max_probability": float(scope_frame[probability_column].max()),
                "service_date_min": str(pd.to_datetime(scope_frame["service_date"]).min().date()),
                "service_date_max": str(pd.to_datetime(scope_frame["service_date"]).max().date()),
            }
        )

    diagnostic = {
        "stage": "A",
        "diagnostic_type": "frozen_model_scope_expansion",
        "model_name": model_name,
        "model_version": model_version,
        "selected_threshold": selected_threshold,
        "probability_column": probability_column,
        "manifest_path": str(MANIFEST_PATH),
        "scored_output_path": str(STAGE_A_SCORED_OUTPUT_PATH),
        "scope_rows": scope_rows,
    }
    STAGE_A_EVALUATION_PATH.write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    return diagnostic


def assign_journey_anchor_splits(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("modeling frame is empty")
    if "journey_id" not in frame.columns or "service_date" not in frame.columns:
        raise ValueError("journey_id and service_date are required for split assignment")

    assigned = frame.copy()
    assigned["service_date"] = pd.to_datetime(assigned["service_date"]).dt.normalize()
    anchor_dates = assigned.groupby("journey_id", as_index=False)["service_date"].min()
    anchor_dates = anchor_dates.rename(columns={"service_date": "journey_anchor_date"})
    unique_dates = sorted(anchor_dates["journey_anchor_date"].dropna().unique())
    if len(unique_dates) < 3:
        raise ValueError("need at least three unique journey anchor dates for train/validation/test split")

    train_end = max(1, int(len(unique_dates) * 0.6))
    validation_end = max(train_end + 1, int(len(unique_dates) * 0.8))
    if validation_end >= len(unique_dates):
        validation_end = len(unique_dates) - 1
    if train_end >= validation_end:
        train_end = validation_end - 1
    if train_end < 1 or validation_end <= train_end:
        raise ValueError("journey-anchor split could not allocate train, validation, and test partitions")

    date_to_split: dict[pd.Timestamp, str] = {}
    for date_value in unique_dates[:train_end]:
        date_to_split[date_value] = TRAIN_SPLIT
    for date_value in unique_dates[train_end:validation_end]:
        date_to_split[date_value] = VALIDATION_SPLIT
    for date_value in unique_dates[validation_end:]:
        date_to_split[date_value] = TEST_SPLIT

    anchor_dates["prediction_split"] = anchor_dates["journey_anchor_date"].map(date_to_split)
    assigned = assigned.merge(anchor_dates, on="journey_id", how="left", validate="many_to_one")
    if assigned["prediction_split"].isna().any():
        raise ValueError("prediction split assignment left null values")
    return assigned


def coerce_feature_types(frame: pd.DataFrame) -> pd.DataFrame:
    typed = frame.copy()
    for column in BOOLEAN_COLUMNS:
        typed[column] = typed[column].astype("Int64")
    for column in NUMERIC_COLUMNS:
        typed[column] = pd.to_numeric(typed[column], errors="coerce")
    return typed


def build_modeling_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing_columns = [
        column
        for column in (*IDENTIFIER_COLUMNS, *ALLOWED_FEATURE_COLUMNS, TARGET_COLUMN, "journey_anchor_date", "prediction_split")
        if column not in frame.columns
    ]
    if missing_columns:
        raise ValueError(f"missing required columns: {missing_columns}")

    modeling_frame = frame.loc[
        frame[TARGET_COLUMN].notna() & (~frame["is_cancellation"]) & (~frame["is_departure_cancelled"])
    ].copy()
    modeling_frame[TARGET_COLUMN] = modeling_frame[TARGET_COLUMN].astype(bool)
    selected_columns = list(
        dict.fromkeys(
            [*IDENTIFIER_COLUMNS, "journey_anchor_date", "prediction_split", *ALLOWED_FEATURE_COLUMNS, TARGET_COLUMN]
        )
    )
    modeling_frame = modeling_frame.loc[:, selected_columns]
    return modeling_frame


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                list(CATEGORICAL_COLUMNS),
            ),
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                list(NUMERIC_COLUMNS),
            ),
            (
                "boolean",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                    ]
                ),
                list(BOOLEAN_COLUMNS),
            ),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )


def require_binary_target(split_name: str, frame: pd.DataFrame) -> None:
    positives = int(frame[TARGET_COLUMN].sum())
    negatives = int((~frame[TARGET_COLUMN]).sum())
    if positives == 0 or negatives == 0:
        raise ValueError(f"{split_name} split must contain both positive and negative rows")


def select_threshold(validation_frame: pd.DataFrame, probabilities: pd.Series) -> tuple[float, float]:
    best_threshold = 0.5
    best_f1 = -1.0
    actual = validation_frame[TARGET_COLUMN].astype(int)
    for threshold in [round(value, 2) for value in pd.Series(range(5, 100, 5)).div(100).tolist()]:
        predicted = (probabilities >= threshold).astype(int)
        score = f1_score(actual, predicted, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_threshold = threshold
    return best_threshold, best_f1


def compute_split_metrics(split_name: str, frame: pd.DataFrame) -> SplitMetrics:
    positive_count = int(frame[TARGET_COLUMN].sum())
    row_count = int(len(frame))
    negative_count = row_count - positive_count
    prevalence = positive_count / row_count if row_count else 0.0
    return SplitMetrics(
        split=split_name,
        row_count=row_count,
        journey_count=int(frame["journey_id"].nunique()),
        positive_count=positive_count,
        negative_count=negative_count,
        prevalence=prevalence,
        anchor_date_min=str(frame["journey_anchor_date"].min().date()),
        anchor_date_max=str(frame["journey_anchor_date"].max().date()),
    )


def compute_scored_metrics(
    split_name: str,
    frame: pd.DataFrame,
    probabilities: pd.Series,
    threshold: float,
    naive_prevalence: float,
) -> dict[str, object]:
    actual = frame[TARGET_COLUMN].astype(int)
    predicted = (probabilities >= threshold).astype(int)
    precision, recall, f1_value, _ = precision_recall_fscore_support(
        actual,
        predicted,
        average="binary",
        zero_division=0,
    )
    tn, fp, fn, tp = confusion_matrix(actual, predicted, labels=[0, 1]).ravel()
    return {
        "split": split_name,
        "pr_auc": average_precision_score(actual, probabilities),
        "roc_auc": roc_auc_score(actual, probabilities),
        "precision": precision,
        "recall": recall,
        "f1": f1_value,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "naive_baseline_prevalence": naive_prevalence,
    }


def verify_split_integrity(frame: pd.DataFrame) -> None:
    split_counts = frame.groupby("journey_id")["prediction_split"].nunique()
    if not split_counts.eq(1).all():
        raise AssertionError("journey_id crosses split boundaries")

    boundaries = frame.groupby("prediction_split")["journey_anchor_date"].agg(["min", "max"])
    boundaries = boundaries.loc[list(SPLIT_ORDER)]
    if not boundaries.loc[TRAIN_SPLIT, "max"] < boundaries.loc[VALIDATION_SPLIT, "min"]:
        raise AssertionError("train and validation anchor dates overlap")
    if not boundaries.loc[VALIDATION_SPLIT, "max"] < boundaries.loc[TEST_SPLIT, "min"]:
        raise AssertionError("validation and test anchor dates overlap")


def persist_scored_output(frame: pd.DataFrame) -> None:
    persist_frame(frame, SCORED_OUTPUT_PATH)


def run() -> EvaluationBundle:
    gold_frame = load_gold_frame()
    split_frame = assign_journey_anchor_splits(gold_frame)
    modeling_frame = build_modeling_frame(split_frame)
    modeling_frame = coerce_feature_types(modeling_frame)
    verify_split_integrity(modeling_frame)

    train_frame = modeling_frame.loc[modeling_frame["prediction_split"] == TRAIN_SPLIT].copy()
    validation_frame = modeling_frame.loc[modeling_frame["prediction_split"] == VALIDATION_SPLIT].copy()
    test_frame = modeling_frame.loc[modeling_frame["prediction_split"] == TEST_SPLIT].copy()
    for split_name, split_frame_part in (
        (TRAIN_SPLIT, train_frame),
        (VALIDATION_SPLIT, validation_frame),
        (TEST_SPLIT, test_frame),
    ):
        require_binary_target(split_name, split_frame_part)

    pipeline = build_pipeline()
    pipeline.fit(train_frame.loc[:, ALLOWED_FEATURE_COLUMNS], train_frame[TARGET_COLUMN].astype(int))

    validation_probabilities = pd.Series(
        pipeline.predict_proba(validation_frame.loc[:, ALLOWED_FEATURE_COLUMNS])[:, 1],
        index=validation_frame.index,
    )
    selected_threshold, _ = select_threshold(validation_frame, validation_probabilities)
    manifest = load_scope_manifest()
    stage_a_scope_diagnostic = build_stage_a_scope_diagnostic(
        pipeline=pipeline,
        selected_threshold=selected_threshold,
        modeling_frame=modeling_frame,
        manifest=manifest,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
    )
    test_probabilities = pd.Series(
        pipeline.predict_proba(test_frame.loc[:, ALLOWED_FEATURE_COLUMNS])[:, 1],
        index=test_frame.index,
    )

    held_out_frame = pd.concat([validation_frame, test_frame]).copy()
    held_out_probabilities = pd.concat([validation_probabilities, test_probabilities]).sort_index()
    held_out_frame["predicted_probability"] = held_out_probabilities
    held_out_frame["predicted_is_departure_severe_delay"] = (
        held_out_frame["predicted_probability"] >= selected_threshold
    )
    held_out_frame["actual_is_departure_severe_delay"] = held_out_frame[TARGET_COLUMN]
    held_out_frame["model_name"] = MODEL_NAME
    held_out_frame["model_version"] = MODEL_VERSION
    held_out_frame["selected_threshold"] = selected_threshold
    held_out_frame["scope_stage"] = "B"
    held_out_frame["scope_evaluation_mode"] = "rebuilt_pipeline"
    held_out_frame["scored_at"] = datetime.now(UTC).isoformat()
    held_out_frame = add_scope_slice_labels(held_out_frame, manifest)

    persist_scored_output(held_out_frame)
    joblib.dump(pipeline, MODEL_PATH)

    training_prevalence = float(train_frame[TARGET_COLUMN].mean())
    split_metrics = [
        asdict(compute_split_metrics(TRAIN_SPLIT, train_frame)),
        asdict(compute_split_metrics(VALIDATION_SPLIT, validation_frame)),
        asdict(compute_split_metrics(TEST_SPLIT, test_frame)),
    ]
    evaluation = EvaluationBundle(
        duckdb_path=str(DUCKDB_PATH),
        source_table=GOLD_TABLE_NAME,
        model_name=MODEL_NAME,
        model_version=MODEL_VERSION,
        target_column=TARGET_COLUMN,
        feature_columns=list(ALLOWED_FEATURE_COLUMNS),
        selected_threshold=selected_threshold,
        split_metrics=split_metrics,
        validation_metrics=compute_scored_metrics(
            VALIDATION_SPLIT,
            validation_frame,
            validation_probabilities,
            selected_threshold,
            training_prevalence,
        ),
        test_metrics=compute_scored_metrics(
            TEST_SPLIT,
            test_frame,
            test_probabilities,
            selected_threshold,
            training_prevalence,
        ),
        excluded_feature_columns=list(EXCLUDED_FEATURE_COLUMNS),
        scored_output_path=str(SCORED_OUTPUT_PATH),
        model_path=str(MODEL_PATH),
        scored_row_count=int(len(held_out_frame)),
        scored_split_counts={
            split_name: int(count)
            for split_name, count in held_out_frame["prediction_split"].value_counts().sort_index().items()
        },
        scored_at=held_out_frame["scored_at"].iloc[0],
    )
    evaluation_payload = asdict(evaluation)
    evaluation_payload["scope_manifest_path"] = str(MANIFEST_PATH)
    evaluation_payload["scope_stage"] = "B"
    evaluation_payload["scope_evaluation_mode"] = "rebuilt_pipeline"
    evaluation_payload["stage_a_scope_diagnostic_path"] = str(STAGE_A_EVALUATION_PATH)
    evaluation_payload["stage_a_scored_output_path"] = str(STAGE_A_SCORED_OUTPUT_PATH)
    evaluation_payload["stage_a_scope_rows"] = stage_a_scope_diagnostic["scope_rows"]
    EVALUATION_PATH.write_text(json.dumps(evaluation_payload, indent=2), encoding="utf-8")
    return evaluation


def main() -> None:
    evaluation = run()
    print(json.dumps(asdict(evaluation), indent=2))


if __name__ == "__main__":
    main()
