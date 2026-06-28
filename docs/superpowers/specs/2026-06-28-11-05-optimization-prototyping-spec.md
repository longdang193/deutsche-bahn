---
layer: change
artifact_type: spec
status: active
template_id: detailed-specification
name: optimization-prototyping
parent_thread: deutsche-bahn-decision-dashboard.optimization-prototyping
targets:
  - scripts/
  - data/scoped/ml/
  - data/scoped/local_scope_bronze.duckdb
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-prototyping.md
related_features: []
related_stages: []
---

## Goal

Define the exact local optimization prototype built from validated ML scored Deutsche Bahn stop events so the project has one reproducible constrained-selection model, one decision-output contract, and one minimal evaluation bundle ready for historical Power BI evaluation.

## Key Deliverables

### Concrete optimization input contract

Define the exact optimization slice for the scoped local data, including input artifact, allowed columns, decision grain, capacity horizon, and any bounded Gold lookup columns still allowed.

### Baseline optimization model and decision-output contract

Define one bounded local optimization prototype plus one frozen policy artifact and one decision output artifact set, including decision variable semantics, objective value components, constraint fields, and downstream join keys.

### ML-to-optimization validation boundary

Define the exact validation checks that prove the prototype uses validated ML outputs only, preserves held-out historical boundaries, and hands off without leaking dashboard-semantic or production-dispatch logic into the optimization layer.

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

### Decision: Optimization prototype stays event-level and separates development from final evaluation

- context: first optimization lane needs one small, auditable prototype that consumes current ML outputs without reopening Gold or ML design, while preserving held-out evaluation honesty
- choice: optimize over one candidate row per scored stop event from `data/scoped/ml/scored_stop_events.parquet`, with two explicit execution modes:
  - development mode: `prediction_split = 'validation'`
  - final historical evaluation mode: `prediction_split = 'test'`
- alternatives considered:
  - mix `validation` and `test` rows in one optimization run
  - aggregate first to station-hour before optimization
  - optimize directly from Gold without ML scored outputs
- impact:
  - optimization stays aligned with validated ML handoff artifact
  - policy design stays separate from final held-out evaluation
  - downstream dashboard can evaluate frozen optimization outputs on test rows only

### Decision: Objective is risk-priority selection under fixed hourly capacity

- context: project needs one concrete decision policy, not an abstract ranking with no resource boundary, and a daily limit is too weak to represent when review effort is needed
- choice: maximize sum of `predicted_severe_delay_probability` across selected candidate rows subject to horizon-level capacity constraints on `calendar_date + hour_of_day`
- alternatives considered:
  - fixed daily capacity only
  - minimize predicted severe-delay count with richer intervention effect assumptions now
  - station-level budget allocation first
  - unconstrained ranking only
- impact:
  - objective remains simple and reproducible
  - selected rows have clear interpretation: highest predicted-risk events that fit available hourly review slots
  - no unsupported causal impact claim is introduced yet

### Decision: One binary decision variable per stop event

- context: first prototype should preserve identity and traceability of each scored event
- choice: create one binary variable `select_event` for each scored stop event row
- alternatives considered:
  - station-day integer allocation variables first
  - grouped service-level candidate variables first
  - multi-action decision set now
- impact:
  - decision output stays joinable to ML scored rows
  - implementation can use simple mixed-integer or equivalent top-k constrained selection
  - later grouped optimization can derive from this baseline if needed

### Decision: Capacity constraint stays one global per-date-hour limit

- context: current local slice is small and lacks validated intervention-resource truth by station or crew type, but hourly timing still matters more than daily totals
- choice: enforce one integer `capacity_per_hour` applied separately for each `calendar_date + hour_of_day` horizon
- alternatives considered:
  - one global monthly budget only
  - one per-service-date budget only
  - station-specific capacities now
  - train-type-specific capacities now
- impact:
  - constraint surface stays bounded and explicit
  - selected candidates remain interpretable as limited hourly review slots
  - more granular resource models are deferred until real operational data exists

### Decision: Capacity is runtime scenario parameter, not fixed operational truth

- context: first prototype needs a stable reproducible budget, but no validated operational resource source exists yet
- choice: define one explicit runtime scenario parameter `capacity_per_hour`, with default prototype value `3`
- alternatives considered:
  - infer capacity from row counts or station frequency
  - hard-code `25` and treat it as stable contract truth
  - tune capacity from dashboard preferences now
- impact:
  - prototype is reproducible and auditable
  - scenario sensitivity can be explored later without changing output shape
  - no fake operational meaning is inferred from historical counts


### Decision: Candidate eligibility is thresholded before optimization

- context: maximizing non-negative probabilities under capacity would otherwise force the prototype to fill slots with low-risk candidates
- choice: define `minimum_candidate_probability` as explicit eligibility threshold, defaulting to the frozen ML-selected threshold from `data/scoped/ml/evaluation.json`, and optimize only rows with `predicted_severe_delay_probability >= minimum_candidate_probability`
- alternatives considered:
  - optimize all candidates regardless of risk level
  - infer threshold from optimization results
  - remove capacity and rank all candidates only
- impact:
  - capacity becomes an upper bound, not a fill requirement
  - very-low-risk rows are excluded before optimization
  - threshold remains documented as prototype eligibility, not causal intervention truth

### Decision: One-per-journey integrity applies within each optimization horizon

- context: multiple risky stops from the same journey in the same hour could waste limited review slots on near-duplicate operational attention
- choice: enforce `at most one selected stop_event_key per journey_id per calendar_date + hour_of_day horizon`
- alternatives considered:
  - no journey integrity rule
  - one selected stop per journey across the entire month
  - station-only uniqueness rule
- impact:
  - selected set is more operationally diverse within each hour
  - optimization gains one meaningful structural rule beyond plain capacity sorting
  - row grain remains event-level and joinable

### Decision: Optimization output is one candidate artifact plus one horizon summary artifact

- context: downstream historical evaluation needs both row-level decisions and compact horizon totals
- choice: produce:
  - one event-level decision artifact with eligible selected and non-selected candidates
  - one date-hour summary artifact with capacity, selected count, unused capacity, selected-risk sum, and realized severe-delay counts
- alternatives considered:
  - summary-only output
  - selected-only rows with no rejected candidates
  - dashboard-specific wide export now
- impact:
  - downstream consumers can audit both chosen and skipped rows
  - historical evaluation stays simple and descriptive
  - output remains reusable across optimization and dashboard threads

### Decision: Gold lookups remain bounded, optional, and row-safe

- context: optimization may need a few descriptive fields beyond current scored artifact, but should not drift back into broad Gold redesign or duplicate candidates
- choice: allow only bounded lookups from validated Gold for descriptive enrichment when missing from scored output:
  - `station_name`
  - `train_service_key`
  - `service_class`
  and allow them only through unique `stop_event_key` joins with mandatory row-count reconciliation
- alternatives considered:
  - no Gold lookups at all
  - unrestricted Gold joins now
  - Silver joins now
- impact:
  - scored artifact remains primary optimization source
  - lookup scope stays narrow and auditable
  - descriptive enrichment cannot change decision grain

### Decision: Historical evaluation stays descriptive, not causal

- context: selected rows come from historical predictions, but no intervention outcome data exists
- choice: evaluate by reporting selected predicted-risk totals and realized severe-delay counts within selected vs non-selected groups, without claiming avoided delays
- alternatives considered:
  - estimate intervention impact now
  - simulate delay reduction using arbitrary effect-size assumptions
  - skip historical evaluation entirely
- impact:
  - evaluation stays honest about what data can support
  - Power BI can compare selected and unselected historical groups descriptively
  - causal optimization remains deferred

## Acceptance Criteria

- optimization input artifact is explicitly defined as `data/scoped/ml/scored_stop_events.parquet`
- development mode and final test-evaluation mode are explicitly separated
- decision grain is explicitly defined as one scored stop event row
- objective and hourly capacity constraint are explicit and bounded
- `capacity_per_hour` is explicit runtime scenario parameter with prototype default
- `minimum_candidate_probability` eligibility rule is explicit
- one-per-journey-per-horizon rule is explicit
- allowed lookup columns beyond scored artifact are explicit
- event-level decision output schema is explicit and joinable downstream
- date-hour summary output schema is explicit and bounded
- historical evaluation metrics are explicit, descriptive, and non-causal
- deterministic tie-break rule is explicit
- optimization layer excludes live dispatch, dashboard semantics, and unsupported intervention-effect assumptions

## Non-Goals

- modify Bronze, Silver, Gold, or ML contracts
- retrain ML model or change ML threshold selection
- infer operational intervention effects from current data
- define station-level or crew-level resource models
- optimize network-wide rolling horizons
- define Power BI semantic model or visuals
- implement live dispatch integration
- implement cloud runtime or BigQuery parity

## Risks and Mitigations

- risk: selected rows may be mistaken for proven interventions
  - mitigation: keep objective and evaluation wording explicitly non-causal and descriptive only

- risk: one global hourly capacity still oversimplifies real operations
  - mitigation: mark it as prototype-only and keep capacity as one explicit scenario parameter with later upgrade path

- risk: event-level candidates may overweight dense stations
  - mitigation: preserve horizon summary outputs and defer fairness or station-balance constraints to later bounded threads

- risk: scored artifact currently contains held-out rows only, so optimization volume is small
  - mitigation: keep prototype historical and local-first; expand only after decision contract is validated

- risk: enrichment joins could duplicate candidates
  - mitigation: allow Gold enrichment only by unique `stop_event_key` and fail on row-count mismatch or duplicate keys

## Output Contracts

## Policy Contract

### `optimization.frozen_policy`

One source-owned artifact used by final mode only:

- `policy_version`
- `execution_modes`
- `canonical_probability_field` = `predicted_severe_delay_probability`
- `threshold_source` = `data/scoped/ml/evaluation.json`
- `minimum_candidate_probability`
- `capacity_scenario`
- `capacity_per_hour`
- `constraint_set`
- `tie_break_rule`
- `metric_definitions`
- `model_name`
- `model_version`
- `selected_threshold`
- `frozen_at`

Final mode must read this artifact and must reject policy overrides.

### `optimization.event_decision`

One row per scoped scored stop event in the selected execution mode:

- `optimization_run_id`
- `execution_mode`
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
- `predicted_is_departure_severe_delay`
- `actual_is_departure_severe_delay`
- `prediction_split`
- `is_eligible_candidate`
- `selected_for_review`
- `candidate_priority_rank`
- `selection_rank`
- `priority_score`
- `objective_contribution`
- `eligibility_reason`
- `solver_status`
- `model_name`
- `model_version`
- `selected_threshold`
- `optimized_at`

### `optimization.horizon_summary`

One row per scoped `calendar_date + hour_of_day` horizon, including horizons with zero eligible candidates:

- `optimization_run_id`
- `execution_mode`
- `calendar_date`
- `hour_of_day`
- `horizon_id`
- `capacity_per_hour`
- `candidate_count`
- `eligible_candidate_count`
- `selected_event_count`
- `unused_capacity`
- `selected_probability_score_sum`
- `candidate_prevalence`
- `actual_severe_selected_count`
- `actual_severe_candidate_count`
- `precision_at_capacity`
- `severe_delay_coverage`
- `lift_over_candidate_prevalence`
- `solver_status`
- `model_name`
- `model_version`
- `optimized_at`

## Metric Definitions

- `precision_at_capacity = actual_severe_selected_count / selected_event_count`
  - return `null` when `selected_event_count = 0`
- `severe_delay_coverage = actual_severe_selected_count / actual_severe_candidate_count`
  - return `null` when `actual_severe_candidate_count = 0`
- `lift_over_candidate_prevalence = precision_at_capacity / candidate_prevalence`
  - return `null` when `candidate_prevalence = 0` or `precision_at_capacity` is `null`
- `candidate_prevalence = actual_severe_candidate_count / eligible_candidate_count`
  - return `null` when `eligible_candidate_count = 0`
- `candidate_priority_rank` means stable risk rank among eligible candidates in the same horizon using `predicted_severe_delay_probability desc, stop_event_key asc`
- `selection_rank` means stable rank among selected candidates in the same horizon using the same ordering
- `priority_score = predicted_severe_delay_probability`
- `objective_contribution = predicted_severe_delay_probability` when `selected_for_review = true`, else `0`

## Invariants

- optimization prototype must consume validated ML scored outputs as primary source
- optimization development mode must use validation rows only; final historical evaluation mode must use test rows only
- optimization must not reintroduce train-split rows
- one `stop_event_key` must map to at most one decision row in output
- one selected-event decision must be binary, not fractional
- selected row count per `calendar_date + hour_of_day` horizon must never exceed configured `capacity_per_hour`
- no more than one candidate from the same `journey_id` may be selected within the same `calendar_date + hour_of_day` horizon
- optimization output must retain stable join keys back to ML scored rows
- final mode must read `optimization.frozen_policy` only and must reject policy overrides
- deterministic tie-break must use `predicted_severe_delay_probability desc, stop_event_key asc`
- historical evaluation must remain descriptive and must not claim causal intervention benefit
- optimization layer must not leak dashboard-specific logic or production-dispatch policy into artifacts

## Validation Plan

- proof target: optimization input is derived from validated ML scored outputs only
  - method: inspection
  - evidence: implementation reads `data/scoped/ml/scored_stop_events.parquet` as primary source and uses only explicitly allowed Gold lookups

- proof target: development and final evaluation modes stay separated
  - method: comparison
  - evidence: development runs contain only `prediction_split = 'validation'`, while final historical evaluation runs contain only `prediction_split = 'test'`

- proof target: candidate eligibility is explicit and enforced
  - method: inspection and run
  - evidence: implementation filters using canonical field `predicted_severe_delay_probability`, with non-null values, `0 <= predicted_severe_delay_probability <= 1`, unique `stop_event_key`, and `predicted_severe_delay_probability >= minimum_candidate_probability`

- proof target: decision grain is one scored stop event row
  - method: comparison
  - evidence: event-level decision artifact row count matches eligible candidate row count and `stop_event_key` is unique

- proof target: hourly capacity constraint is enforced
  - method: run
  - evidence: horizon summary artifact shows `selected_event_count <= capacity_per_hour` for every `calendar_date + hour_of_day` horizon

- proof target: one-per-journey integrity is enforced within each horizon
  - method: run and comparison
  - evidence: no `calendar_date + hour_of_day + journey_id` group contains more than one selected row

- proof target: objective ordering is reproducible
  - method: run and comparison
  - evidence: repeated runs with same inputs and parameters produce identical selected-event set and identical summary totals, using tie-break `predicted_severe_delay_probability desc, stop_event_key asc`

- proof target: enrichment joins preserve row grain
  - method: comparison
  - evidence: candidate count before enrichment matches candidate count after enrichment and no duplicate `stop_event_key` values appear

- proof target: optimization outputs are downstream-joinable
  - method: inspection
  - evidence: `optimization.event_decision` includes `stop_event_key`, horizon fields, prediction fields, decision fields, split metadata, and model metadata

- proof target: historical evaluation stays descriptive
  - method: inspection
  - evidence: `optimization.horizon_summary` reports `precision_at_capacity`, `severe_delay_coverage`, and `lift_over_candidate_prevalence` without any avoided-delay or intervention-effect fields

- proof target: ML threshold and model metadata have one source of truth
  - method: inspection and comparison
  - evidence: implementation reads `selected_threshold`, `model_name`, and `model_version` from `data/scoped/ml/evaluation.json`, and scored-row metadata, when present, matches those values

- proof target: Gurobi optimization matches deterministic reference under frozen constraints
  - method: run and comparison
  - evidence: selected `stop_event_key` set from Gurobi exactly matches selected `stop_event_key` set from deterministic reference selector for the same mode and frozen policy

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
