---
artifact_type: bounded_change_thread
thread_id: deutsche-bahn-decision-dashboard.gold-feature-layer
status: completed
layer: change
template_id: bounded-change-thread
name: thread-gold-feature-layer
---

# Bounded Change Thread: Gold Feature Layer

## Goal

Transform validated Silver Deutsche Bahn operational tables into one bounded Gold feature layer with event-level and station-hour analytical outputs ready for downstream ML, optimization, and Power BI consumers.

## Key Deliverables

### Gold feature-stop-event contract

Define one canonical event-level Gold table derived from `silver.fact_stop_event` and Silver dimensions, with explicit feature ownership for delay, cancellation, calendar, and service slices.

### Gold station-hour aggregate contract

Define one canonical station-hour aggregate table derived from Gold or Silver event rows so dashboard and downstream forecasting work can consume stable operational aggregates without rebuilding them ad hoc.

### Downstream handoff boundary

Make the handoff explicit from Gold features into later ML, optimization, and Power BI threads so this thread closes with validated Gold tables rather than leaking model-training, optimization-policy, or semantic-model decisions into feature engineering.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact Gold slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [x] confirm in-scope Gold tables, grains, and feature families
- [x] confirm out-of-scope ML training, optimization logic, and Power BI semantic modeling
- [x] identify required upstream dependency on validated Silver outputs
- [x] identify explicit downstream handoff targets for ML baseline, optimization, and dashboard threads

**Verification:**
- [x] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Gold model definition

**Purpose:**
- define exact Gold tables and bounded feature logic built from the scoped Silver slice

**Steps:**
- [x] define grain and required fields for `gold.feature_stop_event`
- [x] define grain and required fields for `gold.fact_station_hour`
- [x] define owned feature families such as delay buckets, cancellation flags, service class slices, calendar slices, and station-hour aggregates
- [x] define explicit non-goals and deferred feature families for later ML and optimization threads

**Verification:**
- [x] Gold model is concrete enough to implement without reopening Bronze or Silver contract decisions

**Exit Criteria:**
- Gold feature contract is explicit enough for implementation planning

### Wave 3: Validation and handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [x] define Silver-to-Gold validation expectations
- [x] record deferred items that belong to ML, optimization, or Power BI layers
- [x] identify next required artifact as Gold spec or downstream consumer thread

**Verification:**
- [x] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to Gold spec, implementation plan, or downstream consumer planning

## Scope

- in scope:
  - `gold.feature_stop_event`
  - `gold.fact_station_hour`
  - bounded feature engineering from validated Silver tables
  - explicit feature definitions for delays, cancellations, service slices, and calendar slices
  - Silver-to-Gold validation criteria for scoped local slice
- out of scope:
  - Bronze extraction contract changes
  - Silver operational-model redesign
  - ML model training, scoring, and evaluation
  - Gurobi candidate generation or optimization policy
  - Power BI semantic model, measures, and visuals
  - BigQuery parity and cloud runtime
- deferred:
  - severe-delay labels if they require separate threshold decision
  - journey-level optimization candidate tables
  - model-ready train/test splits
  - dashboard-specific semantic calculations

## Dependencies

- upstream:
  - validated local Bronze outputs from `thread-scope-and-bronze-extraction`
  - validated Silver outputs from `thread-silver-operational-model`
  - current scoped architecture, schema, and roadmap docs
- blockers:
  - none, if Silver SQL, runner, and validation summary remain current
- downstream handoff:
  - Gold detailed spec
  - ML baseline thread
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
