# Bounded Change Thread: Scope And Bronze Extraction

## Goal

Define reproducible project scope for one explicitly selected Deutsche Bahn monthly Parquet file and one explicitly selected hub, then land the resulting complete touching journeys unchanged into Bronze so downstream Silver modeling can start from stable, replayable inputs.

## Key Deliverables

### Scoped extraction contract

Define one canonical scoped extraction contract for the MVP covering one explicitly selected monthly Parquet file, one explicitly selected hub, required columns, complete-journey retention rules, and extraction versioning for local DuckDB execution.

### Bronze landing and manifest shape

Define the Bronze data surfaces and ingestion manifest required to preserve the scoped source records unchanged after extraction, including row-count and scope metadata needed for reproducibility and local validation before Silver handoff.

### Downstream handoff boundary

Make the handoff to the Silver operational-model thread explicit so this thread closes with stable source inputs rather than leaking schema-cleaning or feature logic into the extraction slice.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [x] confirm in-scope surfaces for scope configuration and Bronze landing
- [x] confirm out-of-scope surfaces for Silver, Gold, ML, optimization, and Power BI
- [x] identify required upstream dependency on source dataset availability
- [x] identify explicit downstream handoff target as Silver operational model

**Verification:**
- [x] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Scope contract definition

**Purpose:**
- define the canonical extraction boundary for the MVP dataset

**Steps:**
- [x] define one explicitly selected monthly Parquet file for MVP
- [x] define one explicitly selected hub for MVP
- [x] define complete-journey retention rule for journeys touching the selected hub
- [x] define required source columns only
- [x] define `scope_version` and extraction-query versioning rules

**Verification:**
- [x] scope contract is concrete enough for one local DuckDB extraction and Bronze validation

**Exit Criteria:**
- scope contract is explicit enough to drive one reproducible extract

### Wave 3: Bronze landing contract

**Purpose:**
- define how scoped records land unchanged into Bronze

**Steps:**
- [x] define `bronze.raw_stop_events`
- [x] define `bronze.raw_station_reference`
- [x] define `bronze.raw_ingestion_manifest`
- [x] define immutable-after-extraction rule for Bronze records
- [x] define audit fields for source file, ingestion timestamp, scope version, extraction version, selected hub, and row count

**Verification:**
- [x] Bronze contract preserves selected source rows unchanged after scope cut
- [x] manifest fields are sufficient for replay and local validation

**Exit Criteria:**
- Bronze contract is ready for implementation planning

### Wave 4: Handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [x] record remaining assumptions about source parquet structure
- [x] identify next required artifact as Silver operational-model thread
- [x] capture deferred scale-up work for dynamic month selection, hub ranking, BigQuery parity, and broader scope expansion

**Verification:**
- [x] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to Silver modeling work

## Scope

- in scope:
  - scoped extraction contract for one monthly source file and one selected hub
  - complete-journey retention for journeys touching selected hub
  - Bronze raw landing tables for scoped source data
  - ingestion manifest fields and reproducibility metadata
  - local DuckDB extraction boundary and Silver handoff readiness
- out of scope:
  - Silver cleaning and normalization logic
  - Gold features
  - ML training and scoring
  - candidate generation
  - Gurobi optimization
  - Power BI semantic modeling
  - scheduling and automation
- deferred:
  - dynamic month selection
  - data-driven hub ranking
  - BigQuery parity validation
  - all-station expansion
  - long-history expansion
  - daily or production scheduling

## Dependencies

- upstream:
  - availability of `deutsche-bahn-data` processed parquet source
  - one explicitly selected monthly Parquet file and one explicitly selected hub
  - approved MVP scope assumptions from architecture and roadmap docs
- blockers:
  - none, if source parquet schema is accessible for scoped extraction
- downstream handoff:
  - `thread-silver-operational-model`

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
