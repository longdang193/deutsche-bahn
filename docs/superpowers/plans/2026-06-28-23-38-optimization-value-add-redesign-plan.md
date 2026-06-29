---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: optimization-value-add-redesign
parent_thread: deutsche-bahn-decision-dashboard.optimization-value-add-redesign
parent_spec: docs/superpowers/specs/2026-06-28-22-09-optimization-value-add-redesign-spec.md
targets:
  - scripts/run_optimization_prototype.py
  - tests/test_run_optimization_prototype.py
  - configs/optimization/
  - data/scoped/optimization/
  - data/scoped/power_bi/dashboard_mvp_manifest.json
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-value-add-redesign.md
related_features: []
related_stages: []
---

## Goal

Implement the optimization value-add redesign so the Deutsche Bahn local pipeline produces one deterministic soft station-concentration Gurobi policy, one comparable constrained-greedy baseline, one full policy comparison bundle across fixed capacity scenarios, and one action-oriented downstream handoff that shows whether joint optimization improves the chosen risk-versus-concentration trade-off beyond pure ML ranking.

## Key Deliverables

### Search configuration, frozen policy, and deterministic solver contract

Create one explicit tuning-search configuration artifact in `configs/optimization/` plus one generated frozen-policy artifact in `data/scoped/optimization/`, and update the optimization runner so development tuning, final policy freezing, and final evaluation use separated, reproducible contracts.

### Baseline, scenario, and policy-selection evidence artifacts

Produce deterministic random, ML-first, constrained-greedy, and Gurobi comparisons across capacities `1`, `3`, `5`, and `10`, including optimization-opportunity diagnostics, horizon-level metrics, policy-level summaries, and development tuning evidence.

### Verified optimization-to-dashboard handoff

Update thread state and `data/scoped/power_bi/dashboard_mvp_manifest.json` so downstream dashboard rewrite can explain ML scoring, Gurobi selection, canonical artifact meanings, and station-coverage trade-offs without reopening ML training or BigQuery migration scope.

## Task/Wave Breakdown

### Task 1: Define config, schemas, and solver-status contract

**Purpose:**
- separate experiment configuration from generated frozen policy and freeze exact implementation contracts before touching solver logic

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-22-09-optimization-value-add-redesign-spec.md`
- Inspect: `data/scoped/optimization/frozen_policy.json`
- Modify: `scripts/run_optimization_prototype.py`
- Modify: `configs/optimization/optimization_policy_search_config.json`
- Verify: `configs/optimization/optimization_policy_search_config.json`

**Preconditions:**
- patched redesign spec is current and accepted as implementation source
- validated ML scored outputs and current optimization artifacts exist

**Steps:**
- [ ] Step 1: verify plan/spec contract alignment for output artifact names, grains, required fields, and null semantics before code changes begin
- [ ] Step 2: define one supporting search-config artifact `configs/optimization/optimization_policy_search_config.json` containing:
  - canonical tuning capacity `3`
  - `preferred_station_load_per_station_hour` candidate grid
  - positive penalty candidate grid
  - diagnostic zero-penalty value
  - scenario capacities
  - deterministic winner-selection rule
  - random-baseline seed setting
  - development allowed solver statuses
  - final allowed solver statuses
- [ ] Step 3: define one generated frozen-policy shape that contains only selected final values and provenance, not the search grid
- [ ] Step 4: define solver write-gate contract in code/config:
  - solver seed
  - infeasible behavior
  - time-limit-with-incumbent behavior
  - allowed statuses for development artifact writing
  - allowed statuses for final artifact writing
- [ ] Step 5: record invariant that `minimum_candidate_probability = selected_threshold` in this thread and frozen final lambda must be positive

**Verification:**
- [ ] inspect search config and frozen-policy shapes and confirm configuration and generated evidence are no longer mixed
- [ ] confirm there is no ambiguous `model_name` / `model_version` meaning left in the contracts
- [ ] confirm solver determinism and allowed-status rules are explicit before implementation proceeds

**Exit Criteria:**
- configuration, frozen-policy, and determinism contracts are explicit enough for runner implementation without SSOT drift

### Task 2: Implement shared candidate core and optimization-opportunity diagnostics

**Purpose:**
- implement one shared candidate/metric core and measure whether data actually contains situations where joint optimization could matter

**Files:**
- Inspect: `scripts/run_optimization_prototype.py`
- Inspect: `data/scoped/ml/scored_stop_events.parquet`
- Inspect: `data/scoped/ml/evaluation.json`
- Modify: `scripts/run_optimization_prototype.py`
- Verify: `tests/test_run_optimization_prototype.py`

**Preconditions:**
- Task 1 complete
- current ML split and threshold contract still valid

**Steps:**
- [ ] Step 1: keep current candidate preparation path, split discipline, and one-per-journey semantics, but add explicit per-horizon `feasible_selection_target`
- [ ] Step 2: change hard selection rule from `<= capacity` to exact target equality per horizon, with `candidate_shortage_count` derived only from candidate shortage
- [ ] Step 3: implement shared selected-set-derived station-excess helpers so concentration reporting never depends on raw solver variable values alone
- [ ] Step 4: add optimization-opportunity diagnostics for every horizon:
  - eligible event count
  - distinct eligible journey count
  - distinct station count
  - maximum candidate count at one station
  - whether station excess could activate
  - whether capacity binds
- [ ] Step 5: persist `data/scoped/optimization/development/opportunity_diagnostics.parquet`
- [ ] Step 6: preserve current split isolation and downstream join fields while adding these diagnostics

**Verification:**
- [ ] run local checks confirming every horizon satisfies `selected_event_count = feasible_selection_target`
- [ ] run local checks confirming any `unused_capacity` comes only from candidate shortage
- [ ] inspect opportunity diagnostics and confirm they identify how often station concentration and binding conditions can actually occur

**Exit Criteria:**
- shared candidate core and opportunity evidence exist before policy tuning begins

### Task 3: Implement comparable policies on top of shared core

**Purpose:**
- implement fair like-for-like policies that differ by algorithm, not by hidden contract changes

**Files:**
- Inspect: `scripts/run_optimization_prototype.py`
- Modify: `scripts/run_optimization_prototype.py`
- Verify: `tests/test_run_optimization_prototype.py`

**Preconditions:**
- Task 2 complete
- shared feasible-target and station-excess helpers exist

**Steps:**
- [ ] Step 1: implement deterministic `ml_first` on same eligible pools and exact feasible targets
- [ ] Step 2: implement deterministic seeded `random` policy with row-order-invariant candidate handling
- [ ] Step 3: implement `constrained_greedy` using the same marginal objective inputs as Gurobi:
  - same probability field
  - same preferred station load
  - same lambda
  - same exact feasible target
  - same hard constraints
- [ ] Step 4: implement Gurobi objective with positive station-excess penalty, exact feasible target, and accepted solver-status handling
- [ ] Step 5: confirm all policy outputs share one exact grain and metric core

**Verification:**
- [ ] inspect policy logic and confirm constrained greedy and Gurobi use the same trade-off inputs
- [ ] confirm random baseline is stable across repeated runs and input row reorderings
- [ ] confirm capacity `1` produces Gurobi/ML-first equivalence apart from deterministic ties

**Exit Criteria:**
- comparable policy family is complete enough for tuning and final evaluation

### Task 4: Run development tuning and generate frozen policy

**Purpose:**
- select one final positive-penalty policy deterministically on validation data only and persist auditable selection evidence

**Files:**
- Inspect: `configs/optimization/optimization_policy_search_config.json`
- Modify: `scripts/run_optimization_prototype.py`
- Modify: `data/scoped/optimization/development/tuning_search_results.parquet`
- Modify: `data/scoped/optimization/frozen_policy.json`
- Verify: `data/scoped/optimization/frozen_policy.json`

**Preconditions:**
- Task 3 complete
- policy family and shared metrics are stable

**Steps:**
- [ ] Step 1: run development tuning only at canonical capacity `3`
- [ ] Step 2: evaluate `preferred_station_load_per_station_hour in {1, 2}` against positive penalty candidates `{0.05, 0.10, 0.20}` while still running `0.00` as diagnostic benchmark only
- [ ] Step 3: aggregate tuning metrics with one deterministic rule owned in the search config, including explicit metric aggregation method and tie-break order
- [ ] Step 4: persist `data/scoped/optimization/development/tuning_search_results.parquet` showing every tried parameter pair and its aggregated metrics
- [ ] Step 5: generate `frozen_policy.json` from the winning positive-penalty configuration only, with provenance back to the development tuning artifact and source validation metadata
- [ ] Step 6: confirm final mode will load only generated frozen policy and never rerun tuning

**Verification:**
- [ ] run development tuning twice and confirm same metrics, same winner, and same frozen parameters except timestamp
- [ ] inspect frozen policy and confirm it contains selected final values only, not search-grid configuration
- [ ] confirm `lambda = 0.00` never enters frozen final policy candidate set

**Exit Criteria:**
- one deterministic frozen final policy exists and has auditable tuning provenance

### Task 5: Run final scenarios and write redesigned artifacts

**Purpose:**
- execute final-mode evaluation under frozen policy and persist artifact family used by downstream dashboard rewrite

**Files:**
- Inspect: `data/scoped/optimization/`
- Modify: `scripts/run_optimization_prototype.py`
- Verify: `data/scoped/optimization/`

**Preconditions:**
- Task 4 complete
- generated frozen policy exists and passes provenance checks

**Steps:**
- [ ] Step 1: run final mode on test data only using generated frozen policy
- [ ] Step 2: execute all four policies for capacities `1`, `3`, `5`, and `10`
- [ ] Step 3: write canonical primary artifacts for frozen Gurobi at capacity `3` only:
  - `event_decision.parquet`
  - `horizon_summary.parquet`
  - `evaluation.json`
- [ ] Step 4: write comparison artifacts across all policies and capacities:
  - `horizon_policy_metrics.parquet`
  - `policy_comparison.parquet`
- [ ] Step 5: compute canonical-capacity pairwise diagnostics for:
  - Gurobi vs ML-first
  - Gurobi vs constrained greedy
- [ ] Step 6: preserve documented formulas, descriptive null-handling, and downstream joinability assumptions

**Verification:**
- [ ] inspect output schemas and confirm required fields, grains, uniqueness keys, and null semantics align with spec
- [ ] confirm `policy_comparison.parquet` includes predictive and operational metrics together
- [ ] confirm `evaluation.json` no longer reduces policy difference to one global boolean
- [ ] confirm final outputs are not written for disallowed solver statuses

**Exit Criteria:**
- redesigned optimization artifact family is written and suitable for dashboard rewrite handoff

### Task 6: Update downstream handoff and leave focused checks behind

**Purpose:**
- leave one small but strong verification net behind and update thread state for downstream planning

**Files:**
- Inspect: `tests/test_run_optimization_prototype.py`
- Modify: `tests/test_run_optimization_prototype.py`
- Modify: `data/scoped/power_bi/dashboard_mvp_manifest.json`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-value-add-redesign.md`
- Verify: `data/scoped/power_bi/dashboard_mvp_manifest.json`

**Preconditions:**
- Tasks 1 through 5 complete

**Steps:**
- [ ] Step 1: add focused tests for:
  - exact feasible target fill
  - zero-penalty diagnostic not eligible as frozen final policy
  - constrained-greedy marginal-score symmetry
  - capacity-one invariance
  - deterministic tie handling
  - random row-order invariance
  - zero-denominator metric null behavior
  - Gurobi accepts concentration when probability gain exceeds penalty
  - Gurobi diversifies when probability gain is smaller than penalty
  - solver-status handling for optimal, incumbent-with-time-limit, infeasible, and unexpected failure cases
- [ ] Step 2: run redesigned optimization flow in development and final modes and persist refreshed artifacts
- [ ] Step 3: update `dashboard_mvp_manifest.json` with current optimization semantics, canonical artifact meanings, and wording guardrails
- [ ] Step 4: update thread notes with implemented redesign scope, frozen policy, baseline set, capacity scenario bundle, station-concentration proxy assumption, and downstream dashboard meaning
- [ ] Step 5: record deferred work explicitly:
  - service weights
  - corridor constraints
  - intervention cost modeling
  - BigQuery migration

**Verification:**
- [ ] run targeted optimization tests successfully
- [ ] inspect dashboard manifest and thread notes and confirm downstream dashboard rewrite can start without reopening optimization contract questions

**Exit Criteria:**
- redesign implementation is validated and downstream handoff is explicit

## Verification

- run redesigned optimization build in development and final modes and confirm split separation remains intact
- confirm every horizon satisfies exact feasible selection count and shortage-only unused capacity semantics
- confirm frozen final policy uses positive station penalty and records diagnostic zero-penalty benchmark separately
- confirm random, ML-first, constrained greedy, and Gurobi are all present for capacities `1`, `3`, `5`, and `10`
- confirm constrained greedy and Gurobi use the same marginal trade-off inputs
- inspect `configs/optimization/optimization_policy_search_config.json`, `frozen_policy.json`, `event_decision.parquet`, `horizon_summary.parquet`, `horizon_policy_metrics.parquet`, `policy_comparison.parquet`, `development/opportunity_diagnostics.parquet`, `development/tuning_search_results.parquet`, `evaluation.json`, and `dashboard_mvp_manifest.json` for required fields and diagnostics
- run targeted tests for fill invariant, zero-penalty policy rejection, capacity-one equivalence, row-order invariance, deterministic ties, solver-status handling, and zero-denominator metric behavior

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








