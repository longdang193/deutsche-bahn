---
artifact_type: bounded_change_thread
thread_id: deutsche-bahn-decision-dashboard.optimization-value-add-redesign
status: active
layer: change
template_id: bounded-change-thread
name: thread-optimization-value-add-redesign
---

# Bounded Change Thread: Optimization Value-Add Redesign

## Goal

Redesign the local Deutsche Bahn optimization and evaluation layer so Gurobi solves a real operational trade-off beyond pure probability ranking, produces defensible baseline comparisons, and hands downstream Power BI a clearer action-oriented policy story before any BigQuery migration work starts.

## Key Deliverables

### Optimization policy redesign contract

Define one bounded optimization redesign that keeps the current event-level candidate grain but replaces ranking-equivalent selection with a soft station-concentration trade-off under fixed hourly review capacity.

### Baseline and scenario comparison bundle

Produce one reproducible evaluation bundle that compares random selection, ML-first ranking, constrained greedy selection, and Gurobi on the same candidate pools and fixed capacity scenarios.

### Downstream action-handoff boundary

Make the optimization outputs, metrics, and wording handoff explicit so downstream dashboard work can explain ML, Gurobi, and operator actions without reopening ML training, Bronze/Silver/Gold design, or BigQuery architecture.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact redesign slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [ ] confirm current optimization prototype is mathematically equivalent to ML-first under current constraints
- [ ] confirm in-scope redesign surfaces: objective, constraints, baselines, evaluation artifacts, and dashboard handoff semantics
- [ ] confirm out-of-scope ML retraining, BigQuery migration, and Power BI implementation details
- [ ] identify required upstream dependency on current scored ML outputs and current optimization artifacts

**Verification:**
- [ ] thread boundary is narrow, defensible, and does not overlap vaguely with ML or report-build lanes

**Exit Criteria:**
- redesign scope is stable enough for downstream spec work

### Wave 2: Redesign contract definition

**Purpose:**
- define exact optimization-value-add redesign contract built from scored ML outputs

**Steps:**
- [ ] define bounded objective and constraint redesign
- [ ] define exact baseline policy set and fixed comparison scenarios
- [ ] define exact output artifacts and downstream handoff semantics
- [ ] define explicit non-goals and deferred optimization ideas

**Verification:**
- [ ] redesign contract is concrete enough to implement without reopening ML or report-build scope

**Exit Criteria:**
- redesign contract is explicit enough for implementation planning

### Wave 3: Validation and handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification and execution

**Steps:**
- [ ] define proof expectations for optimization-value-add claims
- [ ] record deferred items for dashboard build and BigQuery migration
- [ ] identify next required artifact as detailed redesign spec and implementation plan

**Verification:**
- [ ] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to detailed spec and implementation planning

## Scope

- in scope:
  - current local optimization prototype redesign in `scripts/run_optimization_prototype.py`
  - event-level selection objective and constraint redesign
  - reproducible policy baselines and scenario comparison artifacts
  - action-oriented optimization output and evaluation contracts for downstream dashboard work
- out of scope:
  - Bronze, Silver, Gold, or ML feature redesign
  - model retraining or probability recalibration
  - Power BI page layout, visual implementation, or semantic model authoring
  - BigQuery migration, orchestration, or cloud runtime
  - live Deutsche Bahn dispatch integration
- deferred:
  - service-priority weights without justified business weighting source
  - corridor minimum constraints or network-wide fairness constraints
  - rolling-horizon or stochastic multi-scenario online optimization
  - human intervention cost modeling that allows intentionally unused capacity

## Dependencies

- upstream:
  - validated ML scored outputs from `thread-ml-baseline-severe-delay`
  - current optimization outputs from `thread-optimization-prototyping`
  - current historical Power BI report artifact and dashboard-contract docs for downstream wording alignment
- blockers:
  - none for spec work
- downstream handoff:
  - detailed optimization redesign spec
  - optimization redesign implementation plan
  - later dashboard rewrite thread or spec that consumes the new comparison and action outputs

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


## Execution Notes

- implemented deterministic search config under configs/optimization/optimization_policy_search_config.json
- implemented canonical frozen Gurobi outputs at capacity 3 plus cross-policy comparison artifacts
- kept service weights, corridor constraints, intervention cost modeling, and BigQuery migration deferred
