---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: scope-and-bronze-extraction
parent_thread: docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-scope-and-bronze-extraction.md
parent_spec: docs/superpowers/specs/2026-06-27-18-40-scope-and-bronze-extraction-spec.md
targets:
  - config/scope.yml
  - data/scoped/
  - sql/duckdb/bronze/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-scope-and-bronze-extraction.md
related_features: []
related_stages: []
---

## Goal

Implement the first local DuckDB scope-and-Bronze pipeline for one explicitly selected monthly Parquet file and one explicitly selected hub, preserving complete journeys touching that hub and producing replayable Bronze inputs ready for Silver handoff.

## Key Deliverables

### Scoped extraction configuration and bounded source slice

Create the human-owned scope configuration and extraction logic that select one monthly Parquet source, one explicit hub, the required columns, and complete journeys touching that hub.

### Bronze raw tables and ingestion manifest

Create the local DuckDB Bronze load that writes scoped source rows unchanged into Bronze tables and records extraction metadata in an ingestion manifest.

### Local validation and Silver handoff readiness

Validate row preservation, manifest completeness, and bounded local footprint so the Bronze outputs are ready for Silver modeling without changing extraction semantics.

## Task/Wave Breakdown

### Task 1: Define scope contract

**Purpose:**
- establish one canonical local scope contract before any Bronze load work begins

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-27-18-40-scope-and-bronze-extraction-spec.md`
- Modify: `config/scope.yml`
- Verify: `config/scope.yml`

**Preconditions:**
- approved or accepted scope-and-Bronze spec is current
- one monthly Parquet source file has been chosen
- one hub has been chosen

**Steps:**
- [x] Step 1: create `config/scope.yml` with fields for selected monthly file, selected hub, required columns, complete-journey retention rule, `scope_version`, and extraction query version
- [x] Step 2: ensure config shape is human-editable and does not embed Silver or feature logic
- [x] Step 3: verify config values map directly to the spec decisions without adding dynamic month or ranking behavior

**Verification:**
- [x] inspect `config/scope.yml` and confirm it captures one file, one hub, required columns, and version fields only

**Exit Criteria:**
- one canonical scope contract exists and is sufficient to drive extraction

### Task 2: Implement scoped extraction query

**Purpose:**
- create deterministic extraction logic for complete journeys touching the selected hub

**Files:**
- Inspect: `config/scope.yml`
- Modify: `sql/duckdb/bronze/`
- Verify: `sql/duckdb/bronze/`

**Preconditions:**
- Task 1 complete
- source parquet schema is inspectable from local DuckDB

**Steps:**
- [x] Step 1: add DuckDB SQL that reads the selected monthly Parquet file and isolates all journeys touching the selected hub
- [x] Step 2: project only required columns plus load audit metadata needed for Bronze
- [x] Step 3: keep extraction logic free of normalization, deduplication, aggregation, or feature derivation

**Verification:**
- [x] inspect Bronze SQL and confirm it filters by selected file and selected hub, retains complete touching journeys, and adds no business derivations

**Exit Criteria:**
- deterministic scoped extraction logic exists for the first local Bronze run

### Task 3: Create Bronze table contract and manifest load

**Purpose:**
- land scoped raw rows and audit metadata into replayable Bronze structures

**Files:**
- Inspect: `sql/duckdb/bronze/`
- Modify: `sql/duckdb/bronze/`
- Verify: `sql/duckdb/bronze/`

**Preconditions:**
- Task 2 complete

**Steps:**
- [x] Step 1: create Bronze DDL or load SQL for `bronze.raw_stop_events`
- [x] Step 2: create Bronze DDL or load SQL for `bronze.raw_station_reference` if station reference is required by scoped run
- [x] Step 3: create Bronze DDL or load SQL for `bronze.raw_ingestion_manifest` including selected file, selected hub, scope version, extraction query version, extraction timestamp, and row count

**Verification:**
- [x] inspect Bronze SQL and confirm raw rows stay unchanged after scope cut
- [x] inspect manifest SQL and confirm required replay metadata is captured

**Exit Criteria:**
- Bronze load contract is fully represented in local DuckDB SQL

### Task 4: Run local Bronze extraction and validate bounded outputs

**Purpose:**
- produce first local scoped Bronze dataset and confirm it is small, replayable, and faithful to the spec

**Files:**
- Inspect: `config/scope.yml`
- Inspect: `sql/duckdb/bronze/`
- Verify: `data/scoped/`

**Preconditions:**
- Tasks 1 through 3 complete
- local DuckDB runtime is available

**Steps:**
- [x] Step 1: execute scoped extraction against chosen monthly Parquet file
- [x] Step 2: load Bronze raw tables and ingestion manifest
- [x] Step 3: collect row counts, sample records, and manifest values for local validation

**Verification:**
- [x] run local DuckDB checks confirming Bronze row count is non-zero and manifest row count matches loaded scoped data
- [x] inspect samples confirming complete journeys touching selected hub are present

**Exit Criteria:**
- first local Bronze run completes and produces bounded replayable outputs

### Task 5: Document validation result and hand off to Silver

**Purpose:**
- close extraction work cleanly and make Silver entry assumptions explicit

**Files:**
- Inspect: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-scope-and-bronze-extraction.md`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-scope-and-bronze-extraction.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-scope-and-bronze-extraction.md`

**Preconditions:**
- Task 4 complete

**Steps:**
- [x] Step 1: record any validated assumptions about source schema, selected hub coverage, and Bronze row footprint in the thread or checkpoint notes
- [x] Step 2: note deferred items remain deferred: dynamic month selection, hub ranking, BigQuery parity, and scope expansion
- [x] Step 3: make Silver operational-model handoff explicit with confirmed Bronze inputs

**Verification:**
- [x] inspect thread notes and confirm downstream Silver work can start without reopening Bronze scope decisions

**Exit Criteria:**
- Bronze implementation is documented well enough for Silver handoff

## Verification

- run local DuckDB Bronze extraction for the chosen monthly file and selected hub
- confirm `bronze.raw_ingestion_manifest` metadata matches the executed scope
- inspect sampled scoped rows to confirm complete journeys touching the hub are preserved
- confirm no Silver-style normalization or derived business fields were added during Bronze load

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
