---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: ml-baseline-severe-delay
parent_thread: deutsche-bahn-decision-dashboard.ml-baseline-severe-delay
parent_spec: docs/superpowers/specs/2026-06-28-10-37-ml-baseline-severe-delay-spec.md
targets:
  - scripts/
  - data/scoped/local_scope_bronze.duckdb
  - data/scoped/gold_validation_summary.json
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-ml-baseline-severe-delay.md
related_features: []
related_stages: []
---

## Goal

Implement the local severe-delay ML baseline on top of the validated Gold Deutsche Bahn slice, producing one reproducible classifier, one scored event-level output, and one compact evaluation bundle ready for downstream optimization prototyping and historical Power BI evaluation.

## Key Deliverables

### Local ML dataset and training pipeline

Create one deterministic local pipeline that reads validated Gold event rows, filters the eligible modeling population, prepares the bounded feature set, applies the journey-anchor time split, and trains one logistic regression baseline.

### Scored output and evaluation artifacts

Produce one scored event-level prediction artifact plus one compact evaluation artifact showing split counts, threshold choice, and validation/test metrics for the severe-delay baseline.

### Documented downstream handoff readiness

Update the ML thread state so downstream optimization and dashboard work can start from a clear validated prediction contract without reopening Gold feature assumptions.

## Task/Wave Breakdown

### Task 1: Build Gold-to-ML dataset preparation path

**Purpose:**
- encode the approved ML feature contract and split logic into one local preparation path

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-10-37-ml-baseline-severe-delay-spec.md`
- Inspect: `sql/duckdb/gold/02_build_gold_feature_layer.sql`
- Modify: `scripts/run_ml_baseline.py`
- Verify: `scripts/run_ml_baseline.py`

**Preconditions:**
- accepted ML spec is current
- validated Gold outputs exist in `data/scoped/local_scope_bronze.duckdb`

**Steps:**
- [ ] Step 1: add one local dataset-preparation path that reads `gold.feature_stop_event`
- [ ] Step 2: filter eligible modeling rows where `is_cancellation = false`, `departure_delay_min is not null`, and `is_departure_severe_delay is not null`
- [ ] Step 3: implement explicit feature allowlist:
  - categorical: `station_id`, `train_type`, `line_number`, `service_class`, `day_name`, `time_band`
  - numeric: `hour_of_day`, `day_of_week`, `month`, `week_of_year`, `arrival_delay_min`
  - boolean: `is_weekend`, `is_cancellation`, `is_arrival_cancelled`, `has_arrival_time_data`
- [ ] Step 4: reject leakage columns explicitly:
  - `is_departure_severe_delay`, `stop_event_key`, `journey_id`, `station_key`, `train_service_key`, `date_key`, `hour_key`, `stop_sequence`
  - `departure_delay_min`, `delay_change_min`, `event_delay_min`, `has_delay_measurement`, `is_delayed`, `is_severe_delay`, `is_extreme_delay`, `delay_bucket`, `is_departure_cancelled`
- [ ] Step 5: implement deterministic split metadata using journey anchor date and one `journey_id` per split only

**Verification:**
- [ ] inspect preparation code and confirm it uses only Gold inputs, filters eligible rows, excludes leakage columns, and assigns reproducible journey-safe splits

**Exit Criteria:**
- one local repeatable dataset-preparation path exists

### Task 2: Add baseline training and threshold-selection runner

**Purpose:**
- provide one deterministic local execution path for training and threshold selection

**Files:**
- Inspect: `scripts/run_gold_feature_layer.py`
- Modify: `scripts/run_ml_baseline.py`
- Verify: `scripts/run_ml_baseline.py`

**Preconditions:**
- Task 1 complete
- Python ML runtime is available locally

**Steps:**
- [ ] Step 1: create `scripts/run_ml_baseline.py`
- [ ] Step 2: fit one `ColumnTransformer` pipeline on training rows only:
  - categorical -> fill `missing` -> `OneHotEncoder(handle_unknown="ignore")`
  - numeric -> median imputation -> `StandardScaler`
  - boolean -> most-frequent imputation -> `0/1`
- [ ] Step 3: train one logistic regression baseline with `class_weight = null`
- [ ] Step 4: score validation set and choose threshold by severe-delay F1 only on validation rows
- [ ] Step 5: freeze threshold before final test evaluation and fail fast when validation/test lack positive or negative examples

**Verification:**
- [ ] inspect runner code and confirm preprocessing, model family, and threshold-selection logic match the spec

**Exit Criteria:**
- one local repeatable ML training command exists

### Task 3: Emit scored output and evaluation evidence

**Purpose:**
- produce baseline predictions and prove the bounded ML spec is satisfied

**Files:**
- Inspect: `data/scoped/local_scope_bronze.duckdb`
- Modify: `data/scoped/ml/`
- Verify: `data/scoped/ml/`

**Preconditions:**
- Tasks 1 and 2 complete

**Steps:**
- [ ] Step 1: execute the local ML baseline build
- [ ] Step 2: persist exactly three artifacts:
  - `data/scoped/ml/severe_delay_model.joblib`
  - `data/scoped/ml/scored_stop_events.parquet`
  - `data/scoped/ml/evaluation.json`
- [ ] Step 3: write scored rows for held-out `validation` and `test` only, with join keys, actual label, probability, predicted flag, split, and model metadata
- [ ] Step 4: write evaluation JSON with split counts, boundary dates, class prevalence, selected threshold, PR-AUC, ROC-AUC, precision, recall, F1, confusion matrix, naive-baseline comparison, and model metadata

**Verification:**
- [ ] run local checks confirming threshold is selected from validation only
- [ ] run local checks confirming each `journey_id` appears in one split only and split anchor dates do not overlap
- [ ] inspect scored output confirming required join keys and prediction fields exist for `validation|test` rows only
- [ ] inspect evaluation artifact confirming class prevalence, PR-AUC, ROC-AUC, precision, recall, F1, confusion matrix, naive baseline, and split counts are present

**Exit Criteria:**
- local ML baseline is trained, scored, and evidenced

### Task 4: Sync thread state and hand off downstream

**Purpose:**
- close the ML baseline slice cleanly and make downstream entry assumptions explicit

**Files:**
- Inspect: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-ml-baseline-severe-delay.md`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-ml-baseline-severe-delay.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-ml-baseline-severe-delay.md`

**Preconditions:**
- Task 3 complete

**Steps:**
- [ ] Step 1: mark validated label, feature boundary, split logic, scored output, and evaluation bundle in the thread
- [ ] Step 2: note deferred items remain deferred: advanced models, optimization policy, dashboard semantics, and cloud runtime
- [ ] Step 3: make optimization prototyping and historical Power BI evaluation handoffs explicit from the validated baseline prediction contract

**Verification:**
- [ ] inspect thread notes and confirm downstream work can start without reopening ML baseline design decisions

**Exit Criteria:**
- ML baseline implementation is documented well enough for downstream handoff

## Verification

- run the local ML baseline command against `data/scoped/local_scope_bronze.duckdb`
- confirm training uses only Gold event inputs and excludes documented leakage columns
- confirm split assignment is journey-anchor based, journey-safe, and reproducible
- confirm threshold is selected from validation only before final test evaluation
- inspect held-out scored output and evaluation artifacts for required fields and metrics

## Completion Criteria

A plan item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>


