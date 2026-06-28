---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: historical-power-bi-evaluation
parent_thread: deutsche-bahn-decision-dashboard.historical-power-bi-evaluation
targets:
  - data/scoped/optimization/final/
  - data/scoped/optimization/frozen_policy.json
  - data/scoped/ml/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-evaluation.md
related_features: []
related_stages: []
---

## Goal

Define the exact local historical Power BI evaluation layer built from validated final-mode Deutsche Bahn optimization outputs so the project has one reproducible semantic dataset, one bounded measure contract, and one minimum dashboard contract ready for descriptive historical analysis.

## Key Deliverables

### Concrete historical evaluation dataset contract

Define the exact Power BI input slice for the scoped local data, including source artifacts, table grain, required columns, join keys, scenario metadata, and descriptive-only evaluation boundaries.

### Semantic model and measure contract

Define one bounded semantic model plus one measure contract, including fact and dimension roles, relationships, scenario identity, slicer scope, required DAX-equivalent measures, and null-handling rules.

### Optimization-to-dashboard validation boundary

Define the exact validation checks that prove the dashboard consumes validated final-mode outputs only, preserves descriptive metric semantics, and hands off without leaking live-dispatch, causal-effect, or enterprise BI governance logic into the local evaluation layer.

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

### Decision: Dashboard consumes final-mode optimization artifacts only

- context: historical evaluation must reflect frozen policy results and must not mix development-mode design evidence into downstream dashboard reporting
- choice: Power BI input sources are limited to:
  - `data/scoped/optimization/final/event_decision.parquet`
  - `data/scoped/optimization/final/horizon_summary.parquet`
  - `data/scoped/optimization/final/evaluation.json`
  - `data/scoped/optimization/frozen_policy.json`
- alternatives considered:
  - mix development and final artifacts in one report
  - read optimization development artifacts only
  - re-query Gold or ML tables directly as dashboard facts
- impact:
  - dashboard remains aligned to frozen-policy historical evaluation
  - semantic model stays downstream of optimization contract
  - validation remains simple and auditable

### Decision: Event decision fact is primary fact table

- context: final optimization output already carries row-level candidate, selection, scenario, and realized-label information needed for slicing and descriptive comparison
- choice: use `optimization.event_decision` as primary fact table with one row per scoped scored stop event in final mode
- alternatives considered:
  - horizon summary as only fact table
  - rebuild fact table from ML and optimization sources separately
  - use only selected rows as fact table
- impact:
  - dashboard can compare selected, eligible-not-selected, and ineligible candidates directly
  - table grain remains explicit and stable
  - dimension derivation stays simple

### Decision: Horizon summary stays secondary fact table with atomic counts as semantic source

- context: hourly capacity usage and descriptive counts already exist at horizon level, but precomputed ratio columns are not safe to aggregate under arbitrary Power BI filters
- choice: use `optimization.horizon_summary` as secondary fact table with one row per scoped `calendar_date + hour_of_day` horizon, treating atomic counts as semantic source and imported ratio columns as reconciliation-only fields
- alternatives considered:
  - aggregate stored ratio columns directly in Power BI
  - recompute summary measures from event rows only
  - flatten summary fields onto every event row
- impact:
  - horizon-level counts remain source-owned by optimization outputs
  - Power BI can calculate filter-aware ratios correctly from atomic counts
  - semantic model avoids incorrect totals under multi-hour filters

### Decision: Dimensions are derived locally from stable keys already present in final artifacts

- context: first dashboard lane needs clean slicers and readable labels without reopening upstream data-engineering layers
- choice: derive four local dimensions from final artifacts only:
  - `dim_date_hour` keyed by `horizon_id`
  - `dim_station` keyed by `station_id`
  - `dim_train_service` keyed by `train_service_key`
  - `dim_scenario` keyed by `scenario_key`
- alternatives considered:
  - query Silver or Gold dimensions directly inside dashboard layer
  - keep a single denormalized table only
  - add enterprise-style conformed dimensions now
- impact:
  - dashboard can slice cleanly without reopening upstream contracts
  - dimension ownership stays local and reproducible
  - semantic model remains small and bounded

### Decision: Descriptive measure contract uses atomic counts as SSOT and DAX ratios as filter-aware formulas

- context: Power BI must not silently reinterpret undefined optimization metrics, invent causal meaning, or aggregate stored non-additive ratios incorrectly
- choice: required measures are split by ownership:
  - event fact owns event counts, eligibility counts, selected counts by station/train/selection status, and event detail
  - horizon fact owns capacity counts and atomic severe-event counts
  - Power BI measures own filter-aware ratio formulas derived from horizon atomic counts
- alternatives considered:
  - aggregate stored ratio columns directly in visuals
  - recompute new causal metrics in dashboard layer
  - coerce null metrics to zero for visuals
- impact:
  - metric semantics remain stable across visuals and filters
  - null handling stays faithful to optimization output contract
  - dashboard avoids unsupported causal claims and incorrect ratio totals

### Decision: Scenario identity and labeling are explicit and separate

- context: prototype capacity must not be mistaken for actual Deutsche Bahn staffing or operational truth, and human-readable labels are not safe relationship keys
- choice: join both facts and the scenario dimension using `scenario_key = policy_version`, while preserving `capacity_scenario` as user-facing label input to `scenario_display_name` such as `Prototype what-if capacity: 3 per hour`
- alternatives considered:
  - join on `capacity_scenario` directly
  - show only numeric capacity without explanation
  - hide scenario metadata from report consumers
- impact:
  - semantic relationships stay stable across policy revisions
  - dashboard remains honest about prototype status
  - descriptive-only boundary is reinforced in report UX

### Decision: Minimum dashboard contract stays two descriptive pages

- context: first dashboard lane should prove that final-mode outputs are explorable, not become a full storytelling product
- choice: require two minimum pages:
  - page 1: overview and capacity
    - cards for selected rows, selected severe rows, precision at capacity, severe delay coverage, lift, and scenario metadata
    - date-hour capacity usage visual
    - selected vs eligible trend by hour/date
  - page 2: candidate and station analysis
    - selected vs not-selected distribution by station, train type, and selection status
    - risk distribution
    - detailed candidate table with joinable row keys and eligibility reason
- alternatives considered:
  - single-page summary only
  - three or more pages for richer storytelling now
  - candidate table only with no aggregate visuals
- impact:
  - dashboard stays bounded and implementation-ready
  - all key descriptive questions have one minimum answer surface
  - later storytelling pages remain deferred

## Output Contracts

### `power_bi.dim_date_hour`

One row per scoped horizon:

- `horizon_id`
- `calendar_date`
- `hour_of_day`
- `date_label`
- `hour_label`

### `power_bi.dim_station`

One row per station:

- `station_id`
- `station_name`

Unknown station handling:
- if `station_id` is missing, dataset build must fail
- if `station_name` is missing, use `Unknown station` display label without changing `station_id`

### `power_bi.dim_train_service`

One row per train service key:

- `train_service_key`
- `train_type`
- `line_number`
- `service_class`

Unknown train-service handling:
- if `train_service_key` is missing, dataset build must fail
- missing descriptive fields may use `Unknown` display labels without changing key identity

### `power_bi.fact_event_decision`

Primary Power BI fact table sourced from final optimization event decisions, one row per scoped scored stop event:

- `optimization_run_id`
- `execution_mode`
- `scenario_key`
- `capacity_scenario`
- `capacity_per_hour`
- `minimum_candidate_probability`
- `calendar_date`
- `hour_of_day`
- `horizon_id`
- `stop_event_key`
- `journey_id`
- `station_id`
- `station_name`
- `train_type`
- `line_number`
- `train_service_key`
- `service_class`
- `predicted_severe_delay_probability`
- `actual_is_departure_severe_delay`
- `prediction_split`
- `is_eligible_candidate`
- `eligibility_reason`
- `selected_for_review`
- `candidate_priority_rank`
- `selection_rank`
- `priority_score`
- `objective_contribution`
- `solver_status`
- `model_name`
- `model_version`
- `selected_threshold`
- `optimized_at`

### `power_bi.fact_horizon_summary`

Secondary Power BI fact table sourced from final optimization horizon summaries, one row per scoped horizon:

- `optimization_run_id`
- `execution_mode`
- `scenario_key`
- `calendar_date`
- `hour_of_day`
- `horizon_id`
- `capacity_scenario`
- `capacity_per_hour`
- `candidate_count`
- `eligible_candidate_count`
- `selected_event_count`
- `unused_capacity`
- `selected_probability_score_sum`
- `actual_severe_selected_count`
- `actual_severe_candidate_count`
- `candidate_prevalence`
- `precision_at_capacity`
- `severe_delay_coverage`
- `lift_over_candidate_prevalence`
- `solver_status`
- `model_name`
- `model_version`
- `optimized_at`

### `power_bi.dim_scenario`

One row per frozen optimization scenario:

- `scenario_key`
- `capacity_scenario`
- `capacity_per_hour`
- `minimum_candidate_probability`
- `model_name`
- `model_version`
- `selected_threshold`
- `policy_version`
- `frozen_at`
- `scenario_display_name`

## Measure Formulas

Required Power BI measures must use filter-aware formulas from atomic counts:

- `Selected Events = SUM(fact_horizon_summary[selected_event_count])`
- `Eligible Events = SUM(fact_horizon_summary[eligible_candidate_count])`
- `Candidate Severe Events = SUM(fact_horizon_summary[actual_severe_candidate_count])`
- `Selected Severe Events = SUM(fact_horizon_summary[actual_severe_selected_count])`
- `Candidate Prevalence = DIVIDE([Candidate Severe Events], [Eligible Events])`
- `Precision at Capacity = DIVIDE([Selected Severe Events], [Selected Events])`
- `Severe-Delay Coverage = DIVIDE([Selected Severe Events], [Candidate Severe Events])`
- `Selection Lift = DIVIDE([Precision at Capacity], [Candidate Prevalence])`
- `Capacity Utilization = DIVIDE(SUM(fact_horizon_summary[selected_event_count]), SUM(fact_horizon_summary[selected_event_count]) + SUM(fact_horizon_summary[unused_capacity]))`

`DIVIDE` must return blank for zero denominators. Imported ratio columns from `fact_horizon_summary` are reconciliation fields and should be hidden from ordinary report authors.

## Slicer Scope

- `calendar_date`, `hour_of_day`, and `scenario_key` slicers must filter both fact tables
- `station_id`, `station_name`, `train_service_key`, `train_type`, `service_class`, `selection status`, and `eligibility_reason` slicers must filter event-level visuals only
- station and train slicers must not filter global horizon-capacity visuals

## Relationship Topology

The semantic model must use one star-shaped topology:

- `dim_date_hour -> fact_event_decision`
- `dim_date_hour -> fact_horizon_summary`
- `dim_scenario -> fact_event_decision`
- `dim_scenario -> fact_horizon_summary`
- `dim_station -> fact_event_decision`
- `dim_train_service -> fact_event_decision`

Rules:

- all relationships are single-direction `dimension -> fact`
- no fact-to-fact relationship is allowed
- no ambiguous filter path is allowed
- no automatic many-to-many relationship is allowed

## Acceptance Criteria

- dashboard input sources are explicitly defined as final optimization artifacts only
- primary fact grain is explicitly defined as one scoped scored stop event row
- secondary fact grain is explicitly defined as one scoped horizon row
- all four local dimensions and their join keys are explicit
- scenario joins use `scenario_key`, not display-only `capacity_scenario`
- required descriptive measures, DAX-equivalent formulas, and null-handling rules are explicit
- event, horizon, and ratio measure ownership is explicit
- slicer scope and relationship topology are explicit
- scenario labeling is explicit and prototype-safe
- minimum dashboard page contract is explicitly two pages
- dashboard layer excludes live dispatch, causal claims, and enterprise deployment concerns

## Non-Goals

- modify Bronze, Silver, Gold, ML, or optimization contracts
- recalculate optimization metrics differently from final artifacts
- infer avoided delays or intervention effectiveness
- create Power BI service deployment, gateway, or refresh workflows
- add row-level security, workspace governance, or enterprise publishing
- design executive storytelling pages beyond the minimum descriptive contract

## Risks and Mitigations

- risk: report consumers may confuse prototype scenario outputs with operational truth
  - mitigation: require explicit prototype scenario labeling on scenario cards and page subtitles

- risk: dashboard measures may drift from optimization semantics
  - mitigation: keep atomic counts source-owned by final optimization outputs and derive filter-aware ratios from those counts using fixed formulas only

- risk: null metrics could be silently coerced to zero in visuals
  - mitigation: define null-preserving measure behavior explicitly and test it in the semantic dataset layer

- risk: duplicated logic across event and horizon facts could create inconsistent totals
  - mitigation: keep event-level detail in primary fact and horizon metrics in secondary fact, with symmetric join keys and no hidden recomputation

## Invariants

- dashboard must consume final-mode optimization outputs only
- dashboard must not mix development and final artifacts in one evaluation surface
- one `stop_event_key` must map to at most one event fact row
- one `horizon_id` must map to at most one horizon summary row
- semantic dataset must preserve descriptive-only evaluation semantics and must not claim causal intervention benefit
- scenario metadata must remain stable and source-owned by `optimization.frozen_policy`
- `scenario_key` must remain stable and unique for the single frozen final policy used by the dataset
- null metric semantics from final optimization outputs must remain null in downstream semantic logic unless the spec explicitly defines a safe display transformation
- dashboard layer must not leak live-dispatch, enterprise BI deployment, or production policy logic into the local evaluation surface

## Validation Plan

- proof target: dashboard input is derived from final optimization outputs only
  - method: inspection
  - evidence: implementation reads only final optimization artifacts plus `optimization.frozen_policy`, with no development artifacts or upstream Gold/ML tables as dashboard facts

- proof target: event fact grain is stable and unique
  - method: comparison
  - evidence: `power_bi.fact_event_decision` row count matches final event decision row count and `stop_event_key` is unique

- proof target: horizon fact grain is stable and unique
  - method: comparison
  - evidence: `power_bi.fact_horizon_summary` row count matches final horizon summary row count and `horizon_id` is unique

- proof target: scenario metadata stays source-owned and joinable
  - method: inspection and comparison
  - evidence: `power_bi.dim_scenario` contains one row matching `optimization.frozen_policy` and joins cleanly to both fact tables through `scenario_key`

- proof target: descriptive measures preserve upstream semantics under filter context
  - method: comparison
  - evidence: dashboard semantic dataset reproduces final optimization counts and filter-aware ratio formulas from horizon atomic counts without causal reinterpretation

- proof target: null metric handling is explicit and preserved
  - method: inspection and run
  - evidence: horizons with null `precision_at_capacity`, `severe_delay_coverage`, or `lift_over_candidate_prevalence` remain null in semantic outputs rather than being silently coerced to zero

- proof target: filter-context behavior is explicit and safe
  - method: run and inspection
  - evidence: one-date, one-hour, one-date-hour, one-station, one-train-type, and selection-status filtered checks reconcile correctly, and station/train slicers do not alter global capacity visuals

- proof target: minimum dashboard contract is complete and bounded
  - method: inspection
  - evidence: implementation exposes exactly two pages with required slicers and visuals, and every visual depends only on approved fact and dimension fields

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
