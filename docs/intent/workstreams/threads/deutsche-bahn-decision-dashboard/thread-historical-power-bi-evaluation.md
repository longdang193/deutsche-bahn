---
artifact_type: bounded_change_thread
thread_id: deutsche-bahn-decision-dashboard.historical-power-bi-evaluation
status: active
layer: change
template_id: bounded-change-thread
name: thread-historical-power-bi-evaluation
---

# Bounded Change Thread: Historical Power BI Evaluation

## Goal

Turn validated final-mode ML and optimization artifacts into one bounded historical Power BI evaluation layer that exposes descriptive operational, prediction, and optimization outcomes through a reproducible local semantic dataset and dashboard-ready metric contract.

## Key Deliverables

### Historical evaluation dataset contract

Define one canonical Power BI input slice derived from final-mode optimization artifacts, including required fact tables, dimensions, metric definitions, join keys, scenario metadata, and descriptive-only evaluation boundaries.

### Power BI semantic model and dashboard contract

Produce one bounded semantic-model contract for historical evaluation, including table roles, relationships, required measures, slicers, and minimum visuals needed to inspect selected vs non-selected outcomes.

### Validation and handoff boundary

Make metric semantics, scenario labeling, and downstream handoff explicit so this thread closes with validated historical-evaluation outputs rather than leaking live dispatch, causal intervention claims, or production BI governance into the local dashboard slice.

## Task/Wave Breakdown

### Wave 1: Boundary confirmation

**Purpose:**
- confirm exact historical evaluation slice this bounded thread owns before downstream spec or plan work begins

**Checks:**
- [ ] confirm Power BI input sources, semantic grain, and descriptive evaluation boundary
- [ ] confirm in-scope measures, slicers, and visuals
- [ ] confirm out-of-scope live operations, causal claims, and enterprise BI deployment concerns
- [ ] identify required upstream dependency on validated final-mode optimization artifacts

**Verification:**
- [ ] thread boundary is narrow, defensible, and does not overlap vaguely with adjacent threads

**Exit Criteria:**
- thread scope is stable enough for downstream execution artifacts

### Wave 2: Dashboard contract definition

**Purpose:**
- define exact local historical-evaluation contract built from final-mode ML and optimization outputs

**Steps:**
- [ ] define semantic input tables, dimensions, joins, and scenario labels
- [ ] define required descriptive measures and null-handling rules
- [ ] define minimum dashboard pages or visual groups for historical evaluation
- [ ] define explicit non-goals and deferred reporting work

**Verification:**
- [ ] dashboard contract is concrete enough to implement without reopening optimization or ML design decisions

**Exit Criteria:**
- dashboard contract is explicit enough for implementation planning

### Wave 3: Validation and handoff preparation

**Purpose:**
- prepare this thread for safe downstream specification or implementation planning

**Steps:**
- [ ] define optimization-to-dashboard validation expectations
- [ ] record deferred items that belong to enterprise BI, cloud refresh, or production decision-policy layers
- [ ] identify next required artifact as dashboard spec or packaging/export thread

**Verification:**
- [ ] next downstream artifact entry point is explicit

**Exit Criteria:**
- thread can hand off cleanly to dashboard spec, implementation plan, or downstream consumer planning

## Scope

- in scope:
  - local historical Power BI evaluation over final-mode optimization outputs
  - descriptive comparison of selected vs non-selected candidates
  - explicit scenario labels such as prototype what-if capacity
  - semantic model contract for facts, dimensions, and measures
  - minimum dashboard contract for slicing by date, hour, station, train type, and selection status
- out of scope:
  - Bronze, Silver, Gold, ML, or optimization contract redesign
  - live Deutsche Bahn dispatch decisions
  - causal claims about avoided delays or intervention effectiveness
  - Power BI service deployment, gateway, or scheduled refresh
  - enterprise governance, row-level security, or shared workspace publishing
- deferred:
  - stakeholder-specific storytelling pages
  - advanced drillthrough and bookmark interactions
  - multi-scenario optimization comparisons beyond first what-if scenario
  - production BI refresh and distribution workflows

## Dependencies

- upstream:
  - validated local Bronze outputs from `thread-scope-and-bronze-extraction`
  - validated Silver outputs from `thread-silver-operational-model`
  - validated Gold outputs from `thread-gold-feature-layer`
  - validated ML outputs from `thread-ml-baseline-severe-delay`
  - validated optimization outputs from `thread-optimization-prototyping`
  - current scoped architecture, schema, and roadmap docs
- blockers:
  - none, if final optimization artifacts remain current and joinable
- downstream handoff:
  - dashboard detailed spec
  - optional packaging or export thread

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

## Execution Status

### Semantic Export Complete

Local semantic export is complete and validated.

Artifacts now available under `data/scoped/power_bi/`:
- `fact_event_decision.parquet`
- `fact_horizon_summary.parquet`
- `dim_date_hour.parquet`
- `dim_station.parquet`
- `dim_train_service.parquet`
- `dim_scenario.parquet`
- `semantic_contract.json`
- `dashboard_mvp_manifest.json`

Validated boundary:
- source inputs limited to final optimization artifacts plus frozen policy
- `scenario_key = frozen_policy.policy_version`
- final/test/single-run invariants enforced
- event-to-horizon reconciliation enforced
- imported horizon ratio columns retained as reconciliation-only metadata, not report-visible measures
- dashboard manifest is metadata-only handoff for downstream report authoring

### Downstream Work Still Pending

This thread is not fully closed yet.

Pending downstream work:
- actual Power BI relationships
- DAX measures in report model
- slicer interaction validation in Power BI
- two-page report authoring and visual validation
