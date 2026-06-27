---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: scope-and-bronze-extraction
parent_workstream: deutsche-bahn-decision-dashboard
targets:
  - config/scope.yml
  - data/scoped/
  - sql/duckdb/bronze/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-scope-and-bronze-extraction.md
related_features: []
related_stages: []
---

## Goal

Define exact MVP scope extraction and Bronze landing contract for the Deutsche Bahn decision-dashboard project using one explicitly selected monthly Parquet file and one explicitly selected hub so local DuckDB extraction and Bronze-to-Silver handoff start from one bounded, reproducible source slice.

## Key Deliverables

### Concrete scoped extraction contract

Define one canonical `scope.yml` contract that fixes how the MVP subset is chosen from the provider parquet data, including one explicitly selected monthly Parquet file, one explicitly selected hub, required-column selection, complete-journey retention, and scope versioning.

### Bronze data contract

Define the Bronze tables and ingestion manifest that preserve scoped source rows unchanged after extraction and record enough metadata to support replay, audit, and local validation before Silver handoff.

### Local Bronze handoff boundary

Define a scope and Bronze shape that is intentionally local-first, validates in DuckDB, and hands off cleanly to Silver before dynamic scope selection, BigQuery parity, or broader expansion are introduced.

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

### Decision: MVP scope is fixed by config, not ad hoc filtering

- context: dataset is too large for first-pass local iteration, and repeated manual filtering would make results non-reproducible
- choice: define one canonical `config/scope.yml` file as the only human-owned scope entrypoint for MVP extraction
- alternatives considered:
  - manual notebook filtering per experiment
  - hard-coded filters directly in SQL
  - ingest everything locally and trim later
- impact:
  - extraction logic becomes reproducible
  - Bronze inputs can be replayed
  - first local implementation stays bounded

### Decision: First Bronze implementation uses one explicitly selected monthly Parquet file

- context: first local extraction should minimize moving parts and avoid premature dynamic month logic
- choice: scope config must name exactly one monthly Parquet file for the first local extraction
- alternatives considered:
  - latest three complete months
  - rolling month selection
  - open-ended multi-file window
- impact:
  - local extraction stays simple
  - debugging is bounded to one source artifact
  - dynamic month selection remains deferred

### Decision: First Bronze implementation uses one explicitly selected hub

- context: data-driven hub ranking adds logic and extra validation before first local Bronze run is proven
- choice: scope config must name exactly one hub explicitly for the first local extraction
- alternatives considered:
  - top-20 stations by event count
  - dynamic hub ranking query
  - all stations
- impact:
  - first extraction avoids ranking logic
  - local debugging stays focused on one hub context
  - hub expansion remains later work

### Decision: Bronze retains complete journeys touching selected hub and keeps selected rows unchanged

- context: downstream Silver logic will need journey context, but Bronze should still remain raw for chosen scope
- choice: filter to one selected monthly Parquet file, retain complete journeys touching the selected hub, then land those selected rows unchanged into Bronze with no normalization, deduplication, or business derivation
- alternatives considered:
  - keep hub-stop rows only
  - full raw copy before any filtering
  - cleaning during extraction
- impact:
  - Bronze remains true raw layer for project slice
  - journey context is preserved
  - Silver owns all cleaning

### Decision: Bronze contract includes explicit ingestion manifest

- context: reproducibility and local validation need more than row data alone
- choice: define `bronze.raw_ingestion_manifest` with selected monthly file, source version, scope version, extraction query version, selected hub, required columns, extraction timestamp, and row count
- alternatives considered:
  - rely on folder names only
  - store metadata in README or notebook notes
- impact:
  - each Bronze run is inspectable
  - local validation can replay same bounded sample
  - later scale-up remains governed

### Decision: Required columns are explicitly whitelisted

- context: provider data contains more fields than MVP needs, and carrying unused columns increases storage and ambiguity
- choice: `scope.yml` must enumerate exact columns to extract; Bronze stores only whitelisted columns plus audit metadata
- alternatives considered:
  - select all columns
  - prune columns later in Silver
- impact:
  - smaller local footprint
  - clearer downstream contracts
  - lower migration noise

### Decision: DuckDB is the only execution target for first Bronze implementation

- context: first implementation should validate local extraction and Silver handoff before cloud duplication
- choice: DuckDB is the only execution target for the first Bronze implementation; BigQuery parity is explicitly deferred until after local extraction and Silver handoff are validated
- alternatives considered:
  - BigQuery first
  - parallel local and cloud implementation from start
- impact:
  - faster early iteration
  - lower initial validation burden
  - cloud migration remains future bounded work

### Decision: This spec stops at Bronze and hands off to Silver

- context: scope creep from extraction into modeling would blur ownership and slow delivery
- choice: this spec does not define normalization, feature logic, ML labels, candidate generation, optimization, or dashboard modeling
- alternatives considered:
  - fold Silver design into same spec
  - define end-to-end pipeline in one implementation artifact
- impact:
  - bounded thread stays clean
  - next spec/plan entrypoint is explicit

## Acceptance Criteria

- a canonical `scope.yml` contract is defined with one monthly source file, one selected hub, complete-journey retention, and column-selection rules
- MVP month scope is fixed to one explicitly selected monthly Parquet file
- MVP hub scope is fixed to one explicitly selected hub
- Bronze landing is defined as complete journeys touching that hub with selected rows unchanged after extraction
- `bronze.raw_stop_events`, `bronze.raw_station_reference`, and `bronze.raw_ingestion_manifest` are explicitly defined
- manifest fields are sufficient to replay the exact extraction run
- DuckDB-first local validation is explicit
- downstream handoff to Silver operational modeling is explicit
- dynamic month selection, data-driven hub ranking, BigQuery parity, and broader scope expansion are explicitly deferred

## Non-Goals

- define Silver normalization logic
- define feature engineering
- define severe-delay label implementation
- define ML training pipeline
- define candidate generation rules beyond noting future handoff
- define Gurobi formulation
- define Power BI semantic model
- define dynamic month selection
- define data-driven hub ranking
- define BigQuery parity process
- define production scheduling or orchestration

## Invariants

- Bronze must preserve scoped selected source records unchanged after extraction
- first Bronze scope must come from one selected monthly file and one selected hub
- Bronze must retain complete journeys touching selected hub
- all scope selection must be reproducible from one human-owned scope contract plus one extraction query version
- selected hub and selected monthly file for one extraction run must be recorded in the manifest
- Silver owns all normalization, deduplication, and business derivation after Bronze
- MVP scope must remain small enough for local DuckDB iteration

## Risks and Mitigations

### Risk: Single selected hub may not generalize

- mitigation:
  - treat first implementation as local validation slice
  - defer broader scope expansion explicitly

### Risk: Provider schema drift may break scoped extraction

- mitigation:
  - require extraction-query versioning
  - require manifest row counts and selected columns
  - keep Bronze raw and minimal so failure surfaces early

### Risk: Complete-journey retention may increase row count more than expected

- mitigation:
  - keep to one monthly file and one hub
  - record final row count in manifest
  - validate local DuckDB footprint before expansion

### Risk: Future dynamic scope logic may change business meaning

- mitigation:
  - freeze first implementation as baseline
  - defer dynamic month selection and hub ranking until Bronze and Silver handoff are validated

## Validation Plan

- proof target: scoped extraction contract is concrete and reproducible
  - method: inspection
  - evidence: spec-defined `scope.yml` fields and explicit selection rules are sufficient to rerun same extract

- proof target: Bronze preserves selected rows unchanged after scope cut
  - method: inspection and comparison
  - evidence: Bronze contract contains no normalization or derived business columns beyond audit metadata

- proof target: complete journey context is preserved for scoped hub slice
  - method: inspection
  - evidence: scope contract states that journeys touching selected hub are retained completely

- proof target: manifest is sufficient for replay and audit
  - method: inspection
  - evidence: manifest fields include selected monthly file, selected hub, scope, query version, timestamp, and row count

- proof target: first implementation stays locally bounded and explicit
  - method: inspection
  - evidence: spec fixes one monthly file, one hub, complete-journey retention, and defers dynamic selection and parity work

- proof target: downstream handoff is bounded
  - method: inspection
  - evidence: Non-Goals and invariants clearly assign Silver and later layers outside this spec

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
