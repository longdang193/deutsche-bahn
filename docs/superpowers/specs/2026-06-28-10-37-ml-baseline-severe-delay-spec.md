---
layer: change
artifact_type: spec
status: active
template_id: detailed-specification
name: ml-baseline-severe-delay
parent_thread: deutsche-bahn-decision-dashboard.ml-baseline-severe-delay
targets:
  - scripts/
  - data/scoped/local_scope_bronze.duckdb
  - data/scoped/gold_validation_summary.json
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-ml-baseline-severe-delay.md
related_features: []
related_stages: []
---

## Goal

Define the exact local ML baseline built from the validated Gold Deutsche Bahn slice so the project has one reproducible severe departure delay classifier, one scored output contract, and one minimal evaluation bundle ready for downstream optimization prototyping and historical Power BI evaluation.

## Key Deliverables

### Concrete ML dataset contract

Define the exact modeling slice for the scoped local data, including label, allowed feature columns, excluded leakage columns, and time-based split strategy.

### Baseline model and scored-output contract

Define one bounded baseline classifier plus one scored output table or artifact, including prediction fields, probability field, threshold rule, and downstream join keys.

### Gold-to-ML validation boundary

Define the exact validation checks that prove the baseline is trained on Gold-only inputs, evaluated with a clean validation/test boundary, and handed off without leaking optimizer or dashboard-specific semantics into the ML layer.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- define current behavior, boundaries, and design constraints before proposing decisions

**Steps:**
- [ ] inspect current source-of-truth surfaces
- [ ] identify unresolved contract edges
- [ ] record affected invariants, interfaces, and dependency boundaries

**Verification:**
- [ ] current-state understanding is explicit enough to support concrete design decisions

**Exit Criteria:**
- no core design decision depends on unstated assumptions

### Wave 2: Decision closure

**Purpose:**
- resolve design choices and document why chosen shape is preferred

**Steps:**
- [ ] define major design decisions
- [ ] compare alternatives where non-obvious
- [ ] record impact on interfaces, invariants, and downstream implementation

**Verification:**
- [ ] each major design question has a documented decision or explicit deferral

**Exit Criteria:**
- design is internally coherent and bounded

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare the spec for implementation handoff by making proof expectations explicit

**Steps:**
- [ ] define validation plan
- [ ] confirm invariant preservation strategy
- [ ] identify any open approval questions or follow-up notes

**Verification:**
- [ ] validation plan proves intended behavior and contract preservation

**Exit Criteria:**
- spec is ready for approval or implementation planning

## Design Decisions

### Decision: Local ML baseline stays one binary classifier over `gold.feature_stop_event`

- context: first ML lane needs one small, reproducible baseline that proves predictive value before richer models or aggregates
- choice: train one event-level binary classifier from `gold.feature_stop_event`
- alternatives considered:
  - train from `gold.fact_station_hour` first
  - multi-label or multi-class target now
  - skip event-level model and start with heuristic thresholds only
- impact:
  - baseline remains simple and auditable
  - downstream optimization can join predictions directly to event-level candidate rows later
  - feature ownership stays aligned with Gold

### Decision: Label is `is_departure_severe_delay`

- context: Gold already defines one explicit departure-based severe-delay target candidate separate from fallback reporting delay
- choice: use `gold.feature_stop_event.is_departure_severe_delay` as the binary target
- alternatives considered:
  - derive label from `event_delay_min >= 15`
  - use cancellation-inclusive disruption label now
  - use station-hour severe-rate target first
- impact:
  - target semantics stay aligned with project terminology
  - label avoids fallback-metric leakage
  - optimization and dashboard threads can reason about one clear severe-delay definition

### Decision: Feature set stays bounded to current Gold columns only

- context: first baseline should prove usefulness of current Gold layer before inventing rolling windows or historical feature stores
- choice: allowed baseline features are:
  - categorical:
    - `station_id`
    - `train_type`
    - `line_number`
    - `service_class`
    - `day_name`
    - `time_band`

  - numeric:
    - `hour_of_day`
    - `day_of_week`
    - `month`
    - `week_of_year`
    - `arrival_delay_min`
  - boolean:
    - `is_weekend`
    - `is_cancellation`
    - `is_arrival_cancelled`
    - `has_arrival_time_data`

- alternatives considered:
  - station-hour aggregate features now
  - rolling and lagged features now
  - text or embedding features
- impact:
  - implementation can stay local and cheap
  - baseline directly tests current Gold usefulness
  - later feature work remains optional, not prerequisite

### Decision: Leakage columns are explicitly excluded

- context: event-level Gold contains direct target and near-target columns that could cheat the classifier if left in training inputs
- choice: exclude:
  - target:
    - `is_departure_severe_delay`
  - identifiers:
    - `stop_event_key`
    - `journey_id`
    - `station_key`
    - `train_service_key`
    - `date_key`
    - `hour_key`
    - `stop_sequence`
  - direct label-leakage columns:
    - `departure_delay_min`
    - `delay_change_min`
    - `event_delay_min`
    - `has_delay_measurement`
    - `is_delayed`
    - `is_severe_delay`
    - `is_extreme_delay`

    - `is_departure_cancelled`
- alternatives considered:
  - allow direct delay fields to maximize baseline accuracy
  - allow keys and rely on model regularization
- impact:
  - reported model quality better reflects pre-disruption predictive value
  - baseline can support real downstream decision logic rather than hindsight classification

### Decision: First baseline assumes arrival-known, departure-unknown prediction timing

- context: current Gold event rows contain both arrival-side and departure-side fields, but the target is departure severe delay
- choice:
  - prediction moment is after arrival information is available and before departure occurs
  - allow arrival-side state such as `arrival_delay_min`, `is_arrival_cancelled`, and arrival time-data flags
  - exclude departure-side outcome fields and derivatives
- alternatives considered:
  - pre-arrival prediction with no arrival-side fields
  - post-departure hindsight classification with full event fields
- impact:
  - baseline remains useful for operational intervention timing
  - feature boundary is explicit instead of implied

### Decision: Modeling population is explicit and target-known

- context: not every Gold event row represents a valid supervised example for severe departure delay
- choice: eligible modeling row must satisfy:
  - `is_cancellation = false`
  - `departure_delay_min is not null`
  - `is_departure_severe_delay is not null`
- alternatives considered:
  - include canceled rows as negatives
  - include unknown-target rows and impute target
- impact:
  - target semantics remain clean
  - cancellation does not get mislabeled as not-severe-delay
  - class prevalence is computed on valid supervised rows only

### Decision: Use journey-anchor time split

- context: random split would leak future patterns backward and inflate confidence for operational forecasting
- choice:
  - assign each `journey_id` one anchor date from its earliest `service_date`
  - split on ordered unique anchor dates, not raw row percentages
  - train = earliest 70 percent of anchor dates
  - validation = next 15 percent of anchor dates
  - test = final 15 percent of anchor dates
- alternatives considered:
  - random split
  - row-percentage split
  - train/test only with no validation
- impact:
  - validation set can tune threshold without touching test set
  - one journey stays in one split only
  - temporal leakage is reduced
  - implementation stays small

### Decision: Baseline model is one scikit-learn logistic regression pipeline

- context: first model should be interpretable, fast, and easy to rerun locally
- choice:
  - use scikit-learn pipeline
  - one-hot encode categorical features
  - impute missing numeric values with median
  - impute missing categorical values with `missing`
  - impute boolean features with most-frequent value and convert to `0/1`
  - standard-scale numeric features
  - logistic regression with `class_weight = null`
- alternatives considered:
  - XGBoost or LightGBM now
  - tree-only baselines now
  - hand-written heuristic rule only
- impact:
  - minimal implementation surface
  - probability output available immediately
  - downstream threads can compare richer models later

### Decision: Threshold selection happens on validation set only

- context: probability output still needs one operational classification cutoff
- choice:
  - score validation set
  - choose one threshold maximizing F1 for severe-delay class
  - freeze that threshold before evaluating test set
  - fail fast if validation or test lacks either positive or negative examples
- alternatives considered:
  - fixed 0.5 threshold
  - optimize directly on test set
  - multi-threshold policy now
- impact:
  - test set remains honest
  - downstream consumers get one deterministic risk flag
  - threshold policy stays simple for MVP

### Decision: Scored output is one event-level prediction artifact

- context: optimization and dashboard threads need one bounded handoff surface
- choice: produce one scored output with:
  - held-out rows only: `validation` and `test`
  - `stop_event_key`
  - `journey_id`
  - `service_date`
  - `station_key`
  - `station_id`
  - `station_name`
  - `train_service_key`
  - `train_type`
  - `service_class`
  - `is_departure_severe_delay` as actual label when available
  - `predicted_severe_delay_probability`
  - `predicted_severe_delay_flag`
  - `prediction_split` with `validation|test`
  - `model_name`
  - `model_version`
  - `selected_threshold`
  - `scored_at`
- alternatives considered:
  - station-hour scored output first
  - dashboard-only CSV with no join keys
  - prediction artifact with optimizer semantics embedded
- impact:
  - downstream joins stay simple
  - scored artifact remains reusable across consumers
  - later optimization thread can aggregate or filter without retraining

### Decision: Evaluation stays minimal and bounded

- context: first baseline needs evidence of usefulness, not full MLOps framework
- choice: report:
  - class prevalence by split
  - PR-AUC on validation and test
  - ROC-AUC on validation and test
  - precision, recall, and F1 for severe-delay class on validation and test
  - confusion matrix on validation and test
  - naive baseline using training severe-delay prevalence
- alternatives considered:
  - calibration curves and SHAP now
  - no validation metrics beyond accuracy
  - large experiment matrix now
- impact:
  - severe-delay performance becomes visible
  - threshold selection remains auditable
  - implementation stays local and small

## Acceptance Criteria

- local ML baseline target is explicitly defined as `is_departure_severe_delay`
- allowed features and excluded leakage columns are explicit
- train/validation/test split rule is explicit and time-based
- baseline model family and preprocessing steps are explicit
- threshold selection rule is explicit and validation-only
- scored output schema is explicit and joinable downstream
- evaluation metrics are explicit and bounded
- ML layer excludes optimizer policy, dashboard semantics, and advanced modeling work

## Non-Goals

- modify Bronze, Silver, or Gold contracts
- add rolling or lag features beyond current Gold columns
- build station-hour forecasting model
- run hyperparameter sweeps
- define Gurobi optimization candidates or objectives
- define Power BI semantic model or visuals
- implement online inference serving
- implement cloud training or BigQuery parity

## Invariants

- ML baseline must train only from validated Gold inputs
- label semantics must stay departure-based severe delay only
- validation set must be used for threshold/model choice, not test set
- test set must remain untouched until threshold is frozen
- scored output must retain stable join keys back to Gold event rows
- ML layer must not leak optimization or dashboard-specific logic into model artifacts

## Validation Plan

- proof target: training data is derived from Gold-only inputs
  - method: inspection
  - evidence: implementation reads `gold.feature_stop_event` fields only and uses documented allowed feature set

- proof target: leakage columns are excluded from model inputs
  - method: inspection and comparison
  - evidence: feature-preparation code excludes target, keys, and direct label-leakage columns named in this spec

- proof target: train/validation/test boundary is journey-anchor based and reproducible
  - method: comparison
  - evidence: split counts and anchor-date boundaries from scored output or evaluation artifact match documented earliest/middle/latest ordering, and each `journey_id` appears in exactly one split

- proof target: threshold selection does not use test set
  - method: inspection
  - evidence: evaluation artifact records threshold chosen from validation metrics before final test metrics are reported, and run fails when validation/test lack positive or negative examples

- proof target: scored output is downstream-joinable
  - method: inspection
  - evidence: scored artifact includes `stop_event_key`, key descriptors, actual label, predicted probability, predicted flag, split, and model metadata

- proof target: baseline evaluation is bounded but real
  - method: run
  - evidence: evaluation artifact reports class prevalence, PR-AUC, ROC-AUC, precision, recall, F1, confusion matrix, and naive-baseline comparison for validation and test

## Completion Criteria

A specification item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>

