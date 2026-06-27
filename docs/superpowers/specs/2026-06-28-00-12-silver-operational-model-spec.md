---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: silver-operational-model
parent_workstream: deutsche-bahn-decision-dashboard
targets:
  - sql/duckdb/silver/
  - data/scoped/local_scope_bronze.duckdb
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-silver-operational-model.md
related_features: []
related_stages: []
---

## Goal

Define the exact Silver operational model built from the validated local Bronze Deutsche Bahn slice so the project has one normalized stop-event fact and one supporting dimension set ready for Gold feature engineering.

## Key Deliverables

### Concrete Silver table contract

Define the exact Silver outputs for the scoped local slice: `silver.fact_stop_event`, `silver.dim_station`, `silver.dim_train_service`, `silver.dim_date`, and `silver.dim_hour`, including grain, key strategy, and core fields.

### Bounded normalization ownership

Define the normalization rules Silver owns for timestamps, delays, cancellations, station identity, and train-service identity so later layers inherit one consistent operational contract instead of repeating data cleaning.

### Bronze-to-Silver validation boundary

Define the exact validation checks that prove Silver preserves Bronze row coverage appropriately, applies only allowed transformations, and is ready to hand off to Gold without reopening Bronze extraction logic.

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

### Decision: Silver table set is fixed to one fact plus four dimensions

- context: scoped local MVP needs a clean analytical contract without overbuilding a warehouse
- choice: implement exactly `silver.fact_stop_event`, `silver.dim_station`, `silver.dim_train_service`, `silver.dim_date`, and `silver.dim_hour`
- alternatives considered:
  - one giant flattened Silver table only
  - extra route, destination, or journey dimensions in first pass
  - skip dimensions and clean only the fact
- impact:
  - Gold layer gets stable joinable tables
  - Silver remains small and focused
  - first implementation avoids speculative dimensions

### Decision: `silver.fact_stop_event` grain stays one row per Bronze raw stop event

- context: Bronze scoped extract already defines one row per stop event within complete journeys touching the selected hub
- choice: Silver keeps one row per Bronze stop record and derives cleaned columns without aggregating or collapsing events
- alternatives considered:
  - aggregate by station-hour in Silver
  - collapse by journey and stop sequence only
  - deduplicate aggressively without evidence
- impact:
  - Silver remains faithful to Bronze coverage
  - Gold can choose later aggregation grain
  - validation can compare row counts directly

### Decision: Silver derives cleaned timestamps and delay fields but preserves raw semantics

- context: Bronze contains planned and changed arrival/departure timestamps plus one generic `delay_in_min`
- choice: Silver normalizes timestamp types and derives:
  - `actual_arrival_ts` from `arrival_change_time`
  - `actual_departure_ts` from `departure_change_time`
  - `planned_arrival_ts` from `arrival_planned_time`
  - `planned_departure_ts` from `departure_planned_time`
  - `arrival_delay_min` when both arrival timestamps exist
  - `departure_delay_min` when both departure timestamps exist
  - `delay_change_min` as `departure_delay_min - arrival_delay_min` when both exist
- alternatives considered:
  - keep only raw timestamp columns and defer all delay logic to Gold
  - overwrite raw provider delay field with recalculated values
- impact:
  - Silver exposes one stable operational contract
  - raw Bronze fields remain untouched upstream
  - Gold avoids repeated timestamp math

### Decision: Cancellation semantics are standardized in Silver

- context: Bronze has one `is_canceled` field and nullable arrival/departure changed timestamps
- choice: Silver defines:
  - `is_cancellation` as normalized boolean from Bronze `is_canceled`
  - `is_arrival_cancelled` equal to `is_cancellation` when arrival side exists
  - `is_departure_cancelled` equal to `is_cancellation` when departure side exists
- alternatives considered:
  - leave one raw cancellation flag only
  - infer separate arrival/departure cancellation independently from null timestamps
- impact:
  - downstream logic gets explicit boolean fields
  - Silver avoids over-claiming semantics that Bronze cannot truly distinguish

### Decision: Silver uses simple deterministic surrogate keys from current scoped data

- context: local MVP needs join stability, but not enterprise key management
- choice:
  - `station_key` derives from distinct normalized station identity
  - `train_service_key` derives from distinct train type plus train number plus line number combination
  - `date_key` uses `YYYYMMDD`
  - `hour_key` uses `HH`
  - `stop_event_key` uses Bronze `id`
- alternatives considered:
  - UUID generation everywhere
  - natural keys only with no dimensions
  - adding dedicated journey dimension now
- impact:
  - joins stay simple
  - key generation remains reproducible
  - later cloud port can preserve logical meanings

### Decision: Station dimension uses `eva` as normalized identity

- context: Bronze has both `eva` and station-name fields, and station naming variants can appear
- choice: `silver.dim_station` uses:
  - `station_id` from `eva`
  - `station_name` as descriptive label, not part of join identity
  - `xml_station_name` preserved as secondary source field
- alternatives considered:
  - station name only
  - XML station name only
- impact:
  - stable operational identity comes from `eva`
  - display remains human-readable

### Decision: Train service dimension stays minimal

- context: current scoped MVP does not need richer service modeling yet
- choice: `silver.dim_train_service` includes:
  - `train_service_key`
  - `train_type`
  - `train_number`
  - `line_number`
  - `service_class`
  - train-service identity stays `train_type + train_number + line_number` for this scoped slice
- alternatives considered:
  - route and destination dimensions now
  - no train-service dimension
- impact:
  - later Gold and Power BI work can slice by service
  - dimension remains bounded

### Decision: `service_class` is normalized from `train_type`

- context: downstream risk and reporting likely need a coarse service bucket
- choice: derive `service_class` with simple deterministic mapping:
  - long-distance: `ICE`, `IC`, `EC`, `NJ`, `RJ`, `TGV`, `FLX`
  - regional: `RE`, `RB`, `IRE`, `MEX`
  - local/urban: `S`, `U`, `STR`, `Bus`, `Tram`
  - other: fallback
- alternatives considered:
  - no service class at Silver
  - more detailed taxonomy now
- impact:
  - one consistent high-level bucket exists early
  - mapping stays easy to revise later

### Decision: Silver excludes feature and ML fields

- context: Silver should be operational model, not mixed warehouse plus feature store
- choice: Silver must not include rolling windows, model labels, prediction scores, candidate actions, or optimizer outputs
- alternatives considered:
  - add convenience feature columns directly in Silver
  - merge Silver and Gold in one step
- impact:
  - layer ownership remains clear
  - Gold feature logic has clean upstream contract

## Acceptance Criteria

- `silver.fact_stop_event`, `silver.dim_station`, `silver.dim_train_service`, `silver.dim_date`, and `silver.dim_hour` are explicitly defined
- `silver.fact_stop_event` grain remains one row per Bronze raw stop event
- Silver derives planned/actual timestamps and delay fields with explicit null-handling rules
- Silver standardizes cancellation fields without changing Bronze raw semantics
- station identity, train-service identity, date, and hour key rules are explicit
- `service_class` mapping is explicit and deterministic
- Silver excludes Gold, ML, optimization, and dashboard-semantic fields
- Bronze-to-Silver validation checks are explicit
- handoff to Gold feature engineering is explicit

## Non-Goals

- modify Bronze extraction logic
- build Gold feature tables
- define severe-delay labels
- define ML training or scoring
- define candidate generation
- define Gurobi optimization contracts
- define Power BI semantic model
- define BigQuery parity or cloud runtime

## Invariants

- Silver must not drop scoped Bronze rows without explicit documented rule
- Silver must not mutate Bronze raw source-of-truth fields in place
- `silver.fact_stop_event` must remain one row per Bronze stop event
- all normalization rules must be deterministic and reproducible from Bronze
- Silver must own operational cleaning only, not feature engineering
- Gold must be able to aggregate from Silver without reconstructing raw semantics

## Risks and Mitigations

### Risk: Provider `delay_in_min` may not match recalculated arrival or departure delays exactly

- mitigation:
  - preserve provider `delay_in_min` in Silver as source field
  - derive arrival and departure delay fields separately rather than overwriting source field

### Risk: Cancellation semantics may be over-inferred

- mitigation:
  - keep separate normalized fields simple and tied to Bronze `is_canceled`
  - avoid inventing richer arrival/departure cancellation semantics in first pass

### Risk: Service-class mapping may misclassify edge train types

- mitigation:
  - keep mapping explicit and deterministic
  - route unknown values to `other`
  - revise only when real downstream need appears

### Risk: Missing timestamps create sparse delay fields

- mitigation:
  - document null-handling explicitly
  - allow nullable derived delay fields rather than forcing imputation in Silver

## Validation Plan

- proof target: Silver fact preserves Bronze scoped row coverage
  - method: comparison
  - evidence: `count(*)` of `silver.fact_stop_event` matches `bronze.raw_stop_events` for first local slice unless documented exception exists

- proof target: Silver table set is structurally complete
  - method: inspection
  - evidence: implementation exposes exactly one fact and four dimensions named in this spec

- proof target: derived delay fields follow explicit deterministic rules
  - method: inspection and sample comparison
  - evidence: sampled rows show planned/actual timestamps and derived arrival/departure delays computed from Bronze timestamps only

- proof target: cancellation semantics remain bounded
  - method: inspection
  - evidence: Silver cancellation fields map directly from Bronze `is_canceled` without undocumented inference

- proof target: Gold handoff stays clean
  - method: inspection
  - evidence: Silver schema contains no rolling features, labels, scores, candidates, or optimizer fields

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
