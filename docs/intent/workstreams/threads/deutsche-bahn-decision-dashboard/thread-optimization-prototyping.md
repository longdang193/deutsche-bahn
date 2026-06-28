---
artifact_type: bounded_change_thread
thread_id: deutsche-bahn-decision-dashboard.optimization-prototyping
status: completed
layer: change
template_id: bounded-change-thread
name: thread-optimization-prototyping
---

# Bounded Change Thread: Optimization Prototyping

## Goal

Turn validated event-level severe-delay predictions into one bounded local optimization prototype that ranks or selects candidate interventions under explicit capacity constraints, producing reproducible decision outputs for later historical Power BI evaluation.

## Key Deliverables

### Optimization dataset contract

Define one canonical optimization input slice derived from `data/scoped/ml/scored_stop_events.parquet`, including required columns, decision grain, optimization horizon, capacity assumptions, and any additional lookup fields pulled from validated Gold tables.

### Local optimization prototype and decision output

Produce one bounded local optimization run that converts predicted severe-delay risk into candidate actions or prioritized selections, writes one decision-output artifact, and makes constraint usage explicit.

### Validation and handoff boundary

Make objective, constraints, assumptions, and downstream handoff explicit so this thread closes with validated optimization-ready outputs rather than leaking dashboard-semantic work, cloud orchestration, or production dispatch policy into the prototype.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact optimization slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [x] confirm optimization input source, decision grain, and historical evaluation boundary
- [x] confirm in-scope objective, capacity constraints, and decision outputs
- [x] confirm out-of-scope live dispatch, production policy, and dashboard semantics
- [x] identify required upstream dependency on validated ML scored outputs

**Verification:**
- [ ] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Optimization contract definition

**Purpose:**
- define exact local optimization contract built from scored ML outputs

**Steps:**
- [x] define optimization input schema and any Gold lookup joins still allowed
- [x] define objective function, decision variables, and capacity constraints
- [x] define optimization output schema for downstream consumers
- [x] define explicit non-goals and deferred optimization work

**Verification:**
- [ ] optimization contract is concrete enough to implement without reopening ML or Gold design decisions

**Exit Criteria:**
- optimization contract is explicit enough for implementation planning

### Wave 3: Validation and handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [x] define ML-to-optimization validation expectations
- [x] record deferred items that belong to dashboard, cloud, or production policy layers
- [x] identify next required artifact as historical Power BI evaluation thread

**Verification:**
- [ ] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to optimization spec, implementation plan, or downstream consumer planning

## Scope

- in scope:
  - local optimization prototype over scored event-level severe-delay risk
  - decision grain based on held-out scored stop events or simple grouped candidates
  - explicit capacity-constrained prioritization or selection logic
  - local objective and constraint definition
  - decision-output contract for historical analysis and later dashboard consumption
- out of scope:
  - Bronze, Silver, Gold, or ML contract redesign
  - advanced feature engineering or model retraining
  - live Deutsche Bahn dispatch integration
  - Power BI semantic model, measures, and visuals
  - cloud scheduling, APIs, or production serving
- deferred:
  - multi-objective optimization beyond first bounded prototype
  - network-wide rolling horizon optimization
  - live intervention feedback loops
  - production approval workflows and human-in-the-loop tooling

## Dependencies

- upstream:
  - validated local Bronze outputs from `thread-scope-and-bronze-extraction`
  - validated Silver outputs from `thread-silver-operational-model`
  - validated Gold outputs from `thread-gold-feature-layer`
  - validated ML outputs from `thread-ml-baseline-severe-delay`
  - current scoped architecture, schema, and roadmap docs
- blockers:
  - none, if scored ML outputs remain current and joinable
- downstream handoff:
  - optimization detailed spec
  - historical Power BI evaluation thread

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


## Execution Outcome

- implemented local runner: `scripts/run_optimization_prototype.py`
- implemented contract tests: `tests/test_run_optimization_prototype.py`
- produced frozen policy:
  - `data/scoped/optimization/frozen_policy.json`
- produced development artifacts:
  - `data/scoped/optimization/development/event_decision.parquet`
  - `data/scoped/optimization/development/horizon_summary.parquet`
  - `data/scoped/optimization/development/evaluation.json`
- produced final artifacts:
  - `data/scoped/optimization/final/event_decision.parquet`
  - `data/scoped/optimization/final/horizon_summary.parquet`
  - `data/scoped/optimization/final/evaluation.json`
- validated contract:
  - development mode uses validation rows only
  - final mode uses test rows only and requires frozen policy
  - canonical probability field normalized to `predicted_severe_delay_probability`
  - threshold source of truth is `data/scoped/ml/evaluation.json`
  - Gurobi selected set matches deterministic reference selected set
  - hourly capacity and one-per-journey constraints are enforced
  - evaluation remains descriptive only
- downstream handoff ready for:
  - historical Power BI evaluation using final-mode event decisions and horizon summaries

## Validation Evidence

- frozen threshold: `0.4`
- capacity scenario: `hourly_capacity_3`
- development mode selected rows: `45`
- final mode selected rows: `60`
- development horizons: `212`
- final horizons: `137`
- development Gurobi/reference selected-set match: `true`
- final Gurobi/reference selected-set match: `true`
- unit test coverage: `tests/test_run_optimization_prototype.py`
