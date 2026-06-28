---
artifact_type: bounded_change_thread
thread_id: deutsche-bahn-decision-dashboard.ml-baseline-severe-delay
status: completed
layer: change
template_id: bounded-change-thread
name: thread-ml-baseline-severe-delay
---

# Bounded Change Thread: ML Baseline Severe Delay

## Goal

Turn the validated Gold Deutsche Bahn feature layer into one bounded local ML baseline that predicts severe departure delay risk from historical event features and produces scored outputs plus simple evaluation evidence.

## Key Deliverables

### Local training dataset contract

Define one canonical modeling slice derived from `gold.feature_stop_event`, including exact target, train/validation/test split rule, and allowed feature columns for the first local baseline.

### Baseline model and scored output

Produce one simple local baseline model plus one scored output table or artifact so downstream optimization and dashboard work can consume predicted severe-delay risk without waiting for advanced modeling.

### Validation and handoff boundary

Make model evaluation and downstream handoff explicit so this thread closes with validated baseline predictions rather than leaking optimization-policy, online serving, or dashboard-semantic work into the ML slice.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact ML slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [x] confirm in-scope target, features, split logic, model family, and scored outputs
- [x] confirm out-of-scope optimizer logic, dashboard semantics, and advanced modeling
- [x] identify required upstream dependency on validated Gold outputs
- [x] identify explicit downstream handoff targets for optimization and Power BI threads

**Verification:**
- [ ] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Baseline model definition

**Purpose:**
- define exact baseline ML contract built from the scoped Gold slice

**Steps:**
- [x] define label and allowed feature columns for local baseline training
- [x] define split strategy and minimal evaluation metrics
- [x] define scored output schema for downstream consumers
- [x] define explicit non-goals and deferred modeling work

**Verification:**
- [ ] baseline ML contract is concrete enough to implement without reopening Gold design decisions

**Exit Criteria:**
- baseline ML contract is explicit enough for implementation planning

### Wave 3: Validation and handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [x] define Gold-to-ML validation expectations
- [x] record deferred items that belong to optimization, dashboard, or cloud layers
- [x] identify next required artifact as optimization thread or historical Power BI evaluation thread

**Verification:**
- [ ] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to ML spec, implementation plan, or downstream consumer planning

## Scope

- in scope:
  - local baseline model for severe departure delay risk
  - label derived from `gold.feature_stop_event.is_departure_severe_delay`
  - bounded feature selection from validated Gold tables
  - local split, training, scoring, and evaluation artifacts
  - scored output contract for downstream optimization and dashboard layers
- out of scope:
  - Bronze extraction contract changes
  - Silver or Gold layer redesign
  - Gurobi candidate generation or optimization policy
  - Power BI semantic model, measures, and visuals
  - online inference serving
  - BigQuery parity and cloud runtime
- deferred:
  - advanced models beyond first baseline
  - feature windows and historical lag engineering beyond current Gold fields
  - hyperparameter sweeps and model registry workflow
  - production retraining and orchestration

## Dependencies

- upstream:
  - validated local Bronze outputs from `thread-scope-and-bronze-extraction`
  - validated Silver outputs from `thread-silver-operational-model`
  - validated Gold outputs from `thread-gold-feature-layer`
  - current scoped architecture, schema, and roadmap docs
- blockers:
  - none, if Gold SQL, runner, and validation summary remain current
- downstream handoff:
  - ML detailed spec
  - optimization thread
  - Power BI semantic-model thread

## Completion Criteria

A thread item is considered complete when:

1. all Key Deliverables are satisfied
2. all downstream/child items are terminal
3. every child item is `completed` or `dropped`

Canonical source-of-truth:

<LINK>
- `docs/operating_system/governance/repo-governance.md`
- `scripts/validate_planning_lifecycle.py`
</LINK>


## Execution Outcome

- implemented local runner: `scripts/run_ml_baseline.py`
- produced artifacts:
  - `data/scoped/ml/severe_delay_model.joblib`
  - `data/scoped/ml/scored_stop_events.parquet`
  - `data/scoped/ml/evaluation.json`
- validated contract:
  - target: `is_departure_severe_delay`
  - features: bounded Gold allowlist only
  - split: journey-anchor time split with one `journey_id` in one split only
  - held-out scoring: `validation|test` rows only
  - threshold: validation-selected, frozen before test evaluation
- downstream handoff ready for:
  - optimization prototyping using event-level severe-delay probability
  - historical Power BI evaluation using scored held-out events and evaluation bundle

## Validation Evidence

- train split: 135045 rows, 2905 journeys, anchor dates `2025-03-01` to `2025-03-18`
- validation split: 742 rows, 68 journeys, anchor dates `2025-03-19` to `2025-03-24`
- test split: 743 rows, 112 journeys, anchor dates `2025-03-25` to `2025-03-31`
- selected threshold: `0.4`
- unit test coverage: `tests/test_run_ml_baseline.py`
