# Bounded Change Thread: Silver Operational Model

## Goal

Transform the validated scoped Bronze Deutsche Bahn slice into one clean Silver operational model with normalized stop-event facts and supporting dimensions so downstream Gold feature work starts from stable, queryable business tables.

## Key Deliverables

### Silver fact and dimension contract

Define one canonical Silver table set for the scoped local slice, including `silver.fact_stop_event`, `silver.dim_station`, `silver.dim_train_service`, `silver.dim_date`, and `silver.dim_hour`, with clear grain, column meaning, and ownership boundaries relative to Bronze.

### Normalization and null-handling rules

Define the bounded normalization rules Silver owns for timestamps, delay fields, station and train-service identity, cancellation semantics, and null behavior so downstream layers do not repeat cleaning logic.

### Downstream handoff boundary

Make the handoff to Gold feature engineering explicit so this thread closes with validated Silver tables rather than leaking feature, ML, optimization, or Power BI logic into the operational-model slice.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [x] confirm in-scope surfaces for Silver fact, dimensions, and normalization rules
- [x] confirm out-of-scope surfaces for Bronze extraction changes, Gold features, ML, optimization, and dashboard semantics
- [x] identify required upstream dependency on validated Bronze outputs
- [x] identify explicit downstream handoff target as Gold feature layer

**Verification:**
- [x] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Silver model definition

**Purpose:**
- define the canonical operational model built from the scoped Bronze slice

**Steps:**
- [x] define grain and required fields for `silver.fact_stop_event`
- [x] define identity and fields for `silver.dim_station`
- [x] define identity and fields for `silver.dim_train_service`
- [x] define `silver.dim_date` and `silver.dim_hour`
- [x] define timestamp, delay, and cancellation normalization rules

**Verification:**
- [x] Silver model is concrete enough to implement without reopening Bronze scope decisions

**Exit Criteria:**
- Silver operational contract is explicit enough for implementation planning

### Wave 3: Validation and handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [x] define Bronze-to-Silver validation expectations
- [x] record deferred items that belong to Gold or later layers
- [x] identify next required artifact as Gold feature-layer thread or Silver spec

**Verification:**
- [x] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to Silver spec, implementation plan, or Gold planning

## Scope

- in scope:
  - `silver.fact_stop_event`
  - `silver.dim_station`
  - `silver.dim_train_service`
  - `silver.dim_date`
  - `silver.dim_hour`
  - normalization rules for timestamps, delay fields, and cancellation semantics
  - Bronze-to-Silver validation criteria for the scoped local slice
- out of scope:
  - Bronze extraction contract changes
  - Gold feature tables
  - ML labels and training
  - candidate generation
  - Gurobi optimization
  - Power BI semantic model
  - BigQuery parity and cloud runtime
- deferred:
  - feature engineering
  - broader station/month expansion
  - cloud-port schema tuning
  - production scheduling

## Dependencies

- upstream:
  - validated local Bronze outputs from `thread-scope-and-bronze-extraction`
  - current architecture, schema, and roadmap docs
- blockers:
  - none, if local Bronze database and validation summary remain available
- downstream handoff:
  - `thread-gold-feature-layer`

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
