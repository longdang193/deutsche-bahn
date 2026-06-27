---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: silver-operational-model
parent_thread: docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-silver-operational-model.md
parent_spec: docs/superpowers/specs/2026-06-28-00-12-silver-operational-model-spec.md
targets:
  - sql/duckdb/silver/
  - scripts/
  - data/scoped/local_scope_bronze.duckdb
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-silver-operational-model.md
related_features: []
related_stages: []
---

## Goal

Implement the local DuckDB Silver operational model on top of the validated Bronze Deutsche Bahn slice, producing one normalized stop-event fact and four supporting dimensions ready for Gold feature engineering.

## Key Deliverables

### Silver schema and load logic

Create DuckDB Silver DDL and transformation SQL for `silver.fact_stop_event`, `silver.dim_station`, `silver.dim_train_service`, `silver.dim_date`, and `silver.dim_hour` from the existing Bronze database.

### Local Silver build and validation

Run the Silver build against the current local Bronze database and produce validation evidence showing row coverage, key table presence, and correctness of the bounded normalization rules.

### Documented Gold handoff readiness

Update the Silver thread state so downstream Gold feature work can start from a clear validated operational model without reopening Bronze assumptions.

## Task/Wave Breakdown

### Task 1: Create Silver schema and transformation contract

**Purpose:**
- encode the approved Silver model into local DuckDB SQL surfaces

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-00-12-silver-operational-model-spec.md`
- Modify: `sql/duckdb/silver/`
- Verify: `sql/duckdb/silver/`

**Preconditions:**
- approved or accepted Silver spec is current
- validated Bronze database exists at `data/scoped/local_scope_bronze.duckdb`

**Steps:**
- [x] Step 1: create Silver schema SQL
- [x] Step 2: add SQL for dimension creation: station, train service, date, and hour
- [x] Step 3: add SQL for `silver.fact_stop_event` with derived timestamp, delay, cancellation, and service-class logic

**Verification:**
- [x] inspect SQL and confirm it implements only Silver-owned normalization and table contracts from the spec

**Exit Criteria:**
- complete local Silver SQL contract exists

### Task 2: Add local Silver build runner

**Purpose:**
- provide one deterministic local execution path for building Silver from Bronze

**Files:**
- Inspect: `scripts/run_scope_and_bronze_extraction.py`
- Modify: `scripts/`
- Verify: `scripts/`

**Preconditions:**
- Task 1 complete
- Python DuckDB runtime is available locally

**Steps:**
- [x] Step 1: create or extend a local Python runner that opens the scoped DuckDB database and executes Silver SQL
- [x] Step 2: keep runner inputs simple and aligned with existing local Bronze artifact paths
- [x] Step 3: emit a compact Silver validation summary artifact for later inspection

**Verification:**
- [x] inspect runner code and confirm it targets the local Bronze-backed DuckDB database and produces Silver outputs plus validation summary

**Exit Criteria:**
- one local repeatable Silver build command exists

### Task 3: Run Silver build and validate outputs

**Purpose:**
- produce the first local Silver operational model and prove it satisfies the bounded spec

**Files:**
- Inspect: `data/scoped/local_scope_bronze.duckdb`
- Inspect: `sql/duckdb/silver/`
- Verify: `data/scoped/`

**Preconditions:**
- Tasks 1 and 2 complete

**Steps:**
- [x] Step 1: execute the local Silver build
- [x] Step 2: collect counts for Bronze raw rows and Silver fact rows
- [x] Step 3: collect dimension counts and sample derived fields for inspection

**Verification:**
- [x] run local checks confirming `silver.fact_stop_event` row count matches `bronze.raw_stop_events`
- [x] inspect samples confirming derived timestamps, delay fields, cancellation fields, and service-class mapping are populated according to spec

**Exit Criteria:**
- local Silver model is built and validated against Bronze

### Task 4: Sync thread state and hand off to Gold

**Purpose:**
- close the Silver bounded slice cleanly and make Gold entry assumptions explicit

**Files:**
- Inspect: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-silver-operational-model.md`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-silver-operational-model.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-silver-operational-model.md`

**Preconditions:**
- Task 3 complete

**Steps:**
- [x] Step 1: mark validated Silver fact, dimensions, and normalization boundaries in the thread
- [x] Step 2: note deferred items remain deferred: Gold features, ML, optimization, Power BI semantics, and cloud parity
- [x] Step 3: make `thread-gold-feature-layer` handoff explicit from the validated Silver contract

**Verification:**
- [x] inspect thread notes and confirm Gold work can start without reopening Silver design decisions

**Exit Criteria:**
- Silver implementation is documented well enough for Gold handoff

## Verification

- run the local Silver build command against `data/scoped/local_scope_bronze.duckdb`
- confirm `silver.fact_stop_event` row count matches `bronze.raw_stop_events`
- confirm all four dimensions exist and are populated
- inspect sample rows showing planned/actual timestamps, derived delays, cancellation flags, and `service_class`

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
