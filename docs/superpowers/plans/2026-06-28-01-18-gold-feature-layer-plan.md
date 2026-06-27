---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: gold-feature-layer
parent_thread: deutsche-bahn-decision-dashboard.gold-feature-layer
parent_spec: docs/superpowers/specs/2026-06-28-01-16-gold-feature-layer-spec.md
targets:
  - sql/duckdb/gold/
  - scripts/
  - data/scoped/local_scope_bronze.duckdb
  - data/scoped/silver_validation_summary.json
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-gold-feature-layer.md
related_features: []
related_stages: []
---

## Goal

Implement the local DuckDB Gold feature layer on top of the validated Silver Deutsche Bahn slice, producing one event-level feature table and one station-hour aggregate table ready for downstream ML, optimization, and Power BI work.

## Key Deliverables

### Gold schema and transformation logic

Create DuckDB Gold DDL and transformation SQL for `gold.feature_stop_event` and `gold.fact_station_hour` from the existing Silver database surfaces.

### Local Gold build and validation

Run the Gold build against the current local DuckDB database and produce validation evidence showing Silver row preservation, deterministic feature derivation, and correct station-hour aggregation.

### Documented downstream handoff readiness

Update the Gold thread state so downstream ML, optimization, and dashboard work can start from a clear validated Gold feature contract without reopening Bronze or Silver assumptions.

## Task/Wave Breakdown

### Task 1: Create Gold schema and feature SQL

**Purpose:**
- encode the approved Gold feature model into local DuckDB SQL surfaces

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-01-16-gold-feature-layer-spec.md`
- Modify: `sql/duckdb/gold/`
- Verify: `sql/duckdb/gold/`

**Preconditions:**
- approved or accepted Gold spec is current
- validated Silver outputs exist in `data/scoped/local_scope_bronze.duckdb`

**Steps:**
- [x] Step 1: create Gold schema SQL
- [x] Step 2: add SQL for `gold.feature_stop_event` with Silver joins, delay fallback, delay flags, and delay buckets
- [x] Step 3: add SQL for `gold.fact_station_hour` with deterministic grouped counts, averages, maxima, and rate columns

**Verification:**
- [x] inspect SQL and confirm it implements only Gold-owned feature and aggregate logic from the spec

**Exit Criteria:**
- complete local Gold SQL contract exists

### Task 2: Add local Gold build runner

**Purpose:**
- provide one deterministic local execution path for building Gold from Silver

**Files:**
- Inspect: `scripts/run_silver_operational_model.py`
- Modify: `scripts/`
- Verify: `scripts/`

**Preconditions:**
- Task 1 complete
- Python DuckDB runtime is available locally

**Steps:**
- [x] Step 1: create or extend a local Python runner that opens the scoped DuckDB database and executes Gold SQL
- [x] Step 2: keep runner inputs simple and aligned with existing local Silver-backed DuckDB artifact paths
- [x] Step 3: emit a compact Gold validation summary artifact for later inspection

**Verification:**
- [x] inspect runner code and confirm it targets the local Silver-backed DuckDB database and produces Gold outputs plus validation summary

**Exit Criteria:**
- one local repeatable Gold build command exists

### Task 3: Run Gold build and validate outputs

**Purpose:**
- produce the first local Gold feature layer and prove it satisfies the bounded spec

**Files:**
- Inspect: `data/scoped/local_scope_bronze.duckdb`
- Inspect: `sql/duckdb/gold/`
- Verify: `data/scoped/`

**Preconditions:**
- Tasks 1 and 2 complete

**Steps:**
- [x] Step 1: execute the local Gold build
- [x] Step 2: collect counts for Silver event rows and Gold event rows
- [x] Step 3: collect station-hour aggregate counts and sampled feature/aggregate rows for inspection

**Verification:**
- [x] run local checks confirming `gold.feature_stop_event` row count matches `silver.fact_stop_event`
- [x] run local checks confirming `gold.fact_station_hour` row count matches distinct `station_key, date_key, hour_key` combinations from `gold.feature_stop_event`
- [x] inspect samples confirming `event_delay_min`, flags, buckets, aggregate counts, averages, and rates are populated according to spec

**Exit Criteria:**
- local Gold model is built and validated against Silver

### Task 4: Sync thread state and hand off downstream

**Purpose:**
- close the Gold bounded slice cleanly and make downstream entry assumptions explicit

**Files:**
- Inspect: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-gold-feature-layer.md`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-gold-feature-layer.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-gold-feature-layer.md`

**Preconditions:**
- Task 3 complete

**Steps:**
- [x] Step 1: mark validated Gold event and station-hour tables plus bounded feature rules in the thread
- [x] Step 2: note deferred items remain deferred: rolling features, ML labels, optimization outputs, dashboard semantics, and cloud parity
- [x] Step 3: make ML baseline, optimization, and Power BI downstream handoffs explicit from the validated Gold contract

**Verification:**
- [x] inspect thread notes and confirm downstream work can start without reopening Gold design decisions

**Exit Criteria:**
- Gold implementation is documented well enough for downstream handoff

## Verification

- run the local Gold build command against `data/scoped/local_scope_bronze.duckdb`
- confirm `gold.feature_stop_event` row count matches `silver.fact_stop_event`
- confirm `gold.fact_station_hour` row count matches distinct station-hour combinations from event-level Gold
- inspect sample rows showing `event_delay_min`, delay flags, delay buckets, and station-hour aggregate measures

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
