---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: optimization-prototyping
parent_thread: deutsche-bahn-decision-dashboard.optimization-prototyping
parent_spec: docs/superpowers/specs/2026-06-28-11-05-optimization-prototyping-spec.md
targets:
  - scripts/
  - data/scoped/ml/
  - data/scoped/local_scope_bronze.duckdb
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-prototyping.md
related_features: []
related_stages: []
---

## Goal

Implement the local optimization prototype on top of the validated ML scored Deutsche Bahn slice, producing one reproducible hourly constrained-selection run, one frozen optimization policy, one mode-separated event-level decision artifact set, and one mode-separated horizon summary artifact set ready for historical Power BI evaluation.

## Key Deliverables

### Optimization candidate builder and execution runner

Create one deterministic local pipeline that reads validated scored ML rows and metadata, separates development and final evaluation modes, applies candidate eligibility and safe enrichment rules, runs both deterministic reference selection and Gurobi optimization with hourly capacity plus one-per-journey integrity, and proves their selected sets match.

### Decision and horizon summary artifacts

Produce mode-separated event-level optimization decision artifacts plus mode-separated date-hour horizon summary artifacts showing eligibility, selected rows, ineligible rows, capacity usage, and descriptive historical evaluation metrics.

### Documented optimization handoff readiness

Update the optimization thread state so downstream historical Power BI evaluation can start from a clear validated decision contract without reopening ML or optimization design assumptions.

## Task/Wave Breakdown

### Task 0: Freeze optimization contract

**Purpose:**
- require stable upstream design and define one frozen optimization policy contract before execution begins

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-11-05-optimization-prototyping-spec.md`
- Modify: `data/scoped/optimization/frozen_policy.json`
- Verify: `data/scoped/optimization/frozen_policy.json`

**Preconditions:**
- accepted optimization spec is current and frozen by Task 0
- validated ML scored outputs and metadata exist

**Steps:**
- [ ] Step 1: freeze decision meaning, execution modes, canonical input fields, horizon definition, threshold source, capacity, constraints, and evaluation metrics
- [ ] Step 2: write one `frozen_policy.json` containing:
  - `execution_modes`
  - `capacity_scenario`
  - `capacity_per_hour`
  - `minimum_candidate_probability`
  - `canonical_probability_field`
  - `threshold_source`
  - `constraint_set`
  - `metric_definitions`
- [ ] Step 3: record that final mode must reject policy overrides and must read frozen values only

**Verification:**
- [ ] inspect frozen policy and confirm every runtime decision needed for final mode is source-owned in one artifact

**Exit Criteria:**
- optimization contract is frozen enough for implementation without policy drift

### Task 1: Build optimization candidate preparation path

**Purpose:**
- encode the approved optimization input contract, execution modes, eligibility rules, and enrichment safety into one local preparation path

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-11-05-optimization-prototyping-spec.md`
- Inspect: `data/scoped/ml/scored_stop_events.parquet`
- Inspect: `data/scoped/ml/evaluation.json`
- Modify: `scripts/run_optimization_prototype.py`
- Verify: `tests/test_run_optimization_prototype.py`

**Preconditions:**
- Task 0 complete
- accepted optimization spec is current and frozen by Task 0
- validated ML outputs exist in `data/scoped/ml/`

**Steps:**
- [ ] Step 1: add one local candidate-preparation path that reads `data/scoped/ml/scored_stop_events.parquet`
- [ ] Step 2: read ML metadata from single source of truth `data/scoped/ml/evaluation.json` and assert:
  - `selected_threshold` exists and `0 <= selected_threshold <= 1`
  - exactly one `model_version` exists in selected scored rows
  - scored-row threshold, when present, matches metadata threshold
- [ ] Step 3: implement explicit execution modes:
  - development mode -> `prediction_split = 'validation'`
  - final mode -> `prediction_split = 'test'`
- [ ] Step 4: implement explicit candidate eligibility rules using canonical field `predicted_severe_delay_probability`:
  - `predicted_severe_delay_probability` is non-null
  - `0 <= predicted_severe_delay_probability <= 1`
  - `predicted_severe_delay_probability >= minimum_candidate_probability`
  - `stop_event_key` is unique
  - required join keys are present
- [ ] Step 5: preserve full scoped row set with explicit `is_eligible_candidate` and `eligibility_reason`, so `scoped rows = eligible rows + ineligible rows`
- [ ] Step 6: implement bounded optional Gold enrichment by unique `stop_event_key` only, with row-count reconciliation and duplicate-key failure
- [ ] Step 7: construct optimization horizon fields from `calendar_date + hour_of_day`

**Verification:**
- [ ] write and run failing-then-passing tests proving split separation, canonical probability field enforcement, metadata-threshold SSOT, eligibility enforcement, unique `stop_event_key`, and row-safe enrichment

**Exit Criteria:**
- one local repeatable candidate-preparation path exists

### Task 2: Add deterministic reference selector and Gurobi runner

**Purpose:**
- provide one deterministic local execution path for constrained selection with stable tie-break behavior and one matching Gurobi optimization path

**Files:**
- Inspect: `data/scoped/ml/evaluation.json`
- Inspect: `data/scoped/optimization/frozen_policy.json`
- Modify: `scripts/run_optimization_prototype.py`
- Modify: `tests/test_run_optimization_prototype.py`
- Verify: `tests/test_run_optimization_prototype.py`

**Preconditions:**
- Task 1 complete
- Python optimization runtime is available locally
- Gurobi runtime is available locally

**Steps:**
- [ ] Step 1: implement runtime parameters from frozen policy with bounded defaults:
  - `execution_mode = development`
  - `capacity_scenario = hourly_capacity_3`
  - `capacity_per_hour = 3`
  - `minimum_candidate_probability = selected_threshold from ML metadata`
- [ ] Step 2: implement deterministic reference selection ordered by:
  - `predicted_severe_delay_probability desc`
  - `stop_event_key asc`
- [ ] Step 3: implement journey representative logic within each horizon so lower-priority same-journey rows keep explicit non-selected or ineligible status with reason
- [ ] Step 4: build Gurobi binary-selection model with:
  - binary decision variable per eligible candidate row
  - objective `maximize sum(predicted_severe_delay_probability * x_i)`
  - hourly capacity constraint
  - one-per-journey-per-horizon constraint
- [ ] Step 5: run deterministic reference selector and Gurobi, then assert identical selected sets
- [ ] Step 6: record decision fields, candidate priority rank, selection rank, objective contribution, solver status, and run metadata in memory before persistence
- [ ] Step 7: ensure actual historical labels are attached only after selection and never influence candidate filtering or solver inputs

**Verification:**
- [ ] write and run failing-then-passing tests proving hourly capacity, one-per-journey integrity, stable tie-break behavior, no-label-leakage, repeatable selection on identical inputs, and Gurobi/reference equality

**Exit Criteria:**
- one local repeatable optimization command exists with matching deterministic and Gurobi results

### Task 3: Emit development and final optimization artifacts with descriptive evaluation evidence

**Purpose:**
- produce optimization outputs for both frozen-policy development and final evaluation modes and prove the bounded optimization spec is satisfied

**Files:**
- Modify: `data/scoped/optimization/`
- Modify: `scripts/run_optimization_prototype.py`
- Verify: `data/scoped/optimization/development/`
- Verify: `data/scoped/optimization/final/`

**Preconditions:**
- Tasks 1 and 2 complete

**Steps:**
- [ ] Step 1: execute the local optimization build in development mode and persist:
  - `data/scoped/optimization/development/event_decision.parquet`
  - `data/scoped/optimization/development/horizon_summary.parquet`
  - `data/scoped/optimization/development/evaluation.json`
- [ ] Step 2: persist `data/scoped/optimization/frozen_policy.json` as required input for final mode
- [ ] Step 3: execute the local optimization build in final mode using test rows only and persist:
  - `data/scoped/optimization/final/event_decision.parquet`
  - `data/scoped/optimization/final/horizon_summary.parquet`
  - `data/scoped/optimization/final/evaluation.json`
- [ ] Step 4: write event-level decision rows for full scoped rows, including eligible and ineligible candidates, join keys, prediction fields, decision fields, solver metadata, execution-mode metadata, and `eligibility_reason`
- [ ] Step 5: write horizon summary rows with capacity usage, unused capacity, selected-risk totals, realized severe-delay totals, `precision_at_capacity`, `severe_delay_coverage`, and `lift_over_candidate_prevalence`, using `null` for undefined ratios instead of silent zero
- [ ] Step 6: include explicit development/final metadata and reconciliation fields so later historical Power BI evaluation can compare frozen-policy runs cleanly

**Verification:**
- [ ] run local checks confirming development artifacts contain only validation rows and final artifacts contain only test rows
- [ ] run local checks confirming final mode refuses policy overrides and requires `frozen_policy.json`
- [ ] run local checks confirming each horizon respects `capacity_per_hour`
- [ ] run local checks confirming each horizon has at most one selected row per `journey_id`
- [ ] run local checks confirming `scoped rows = eligible rows + ineligible rows`
- [ ] inspect event decision artifacts confirming required output fields, stable rank semantics, and row mapping back to scored ML rows
- [ ] inspect horizon summary artifacts confirming descriptive metrics, null edge-case handling, and no causal-intervention fields
- [ ] run reconciliation confirming `sum(objective_contribution) = solver objective value`

**Exit Criteria:**
- development and final optimization prototype artifacts are written, separated, and evidenced

### Task 4: Sync thread state and hand off downstream

**Purpose:**
- close the optimization prototype slice cleanly and make downstream entry assumptions explicit

**Files:**
- Inspect: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-prototyping.md`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-prototyping.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-prototyping.md`

**Preconditions:**
- Task 3 complete
- final mode artifacts exist under `data/scoped/optimization/final/`

**Steps:**
- [ ] Step 1: mark validated development mode, final mode, frozen policy, eligibility boundary, hourly capacity, one-per-journey rule, and output artifacts in the thread
- [ ] Step 2: note deferred items remain deferred: richer resource models, causal intervention effects, dashboard semantics, and cloud runtime
- [ ] Step 3: make historical Power BI evaluation handoff explicit from final-mode optimization outputs only

**Verification:**
- [ ] inspect thread notes and confirm downstream historical evaluation can start without reopening optimization design decisions

**Exit Criteria:**
- optimization prototype implementation is documented well enough for downstream handoff

## Verification

- run the local optimization prototype command in development and final modes against `data/scoped/ml/scored_stop_events.parquet`
- confirm development mode uses validation rows only and final mode uses frozen-policy test rows only
- confirm ML metadata is single source of truth for threshold and model metadata checks
- confirm candidate eligibility, unique `stop_event_key`, row-safe enrichment, and full scoped-row auditability are enforced
- confirm hourly capacity and one-per-journey integrity are enforced
- confirm Gurobi selected set matches deterministic reference selected set
- inspect development and final event decision and horizon summary artifacts for required fields, descriptive metrics, and null edge-case handling
- run targeted tests for split separation, tie-break determinism, capacity enforcement, one-per-journey integrity, no-label-leakage, and solver/reference equality

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
