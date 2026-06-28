---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: historical-power-bi-report-build
parent_thread: deutsche-bahn-decision-dashboard.historical-power-bi-report-build
parent_spec: docs/superpowers/specs/2026-06-28-14-25-historical-power-bi-report-build-spec.md
targets:
  - reports/power_bi/historical_evaluation/
  - data/scoped/power_bi/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md
related_features: []
related_stages: []
---

## Goal

Implement one local PBIP historical evaluation report that reads six validated semantic-export parquet tables through one portable root parameter, applies frozen star-schema relationships and current semantic-export measure names, renders exactly two descriptive pages, and closes with structured refresh, portability, and interaction validation evidence tied to one deterministic semantic-export fingerprint.

## Key Deliverables

### Canonical PBIP report project with portable semantic-export binding

Create one repo-tracked Power BI Project under `reports/power_bi/historical_evaluation/` with exactly one canonical entry file named `historical_evaluation.pbip`, one `SemanticExportRoot` parameter, exactly six imported runtime data tables, no imported JSON contract tables, and successful refresh from more than one valid root location by changing only the parameter value.

### Frozen semantic model and two-page report surface

Implement one bounded Power BI semantic model with exactly six authored data tables, no dedicated Measures table, required active one-to-many single-direction relationships, hidden reconciliation-only fields, current exported horizon measure names stored on their owning fact table, event-grain measures stored on `fact_event_decision`, current required slicer fields from handoff contracts, and exactly two visible pages with no hidden tooltip or drillthrough pages.

### Structured validation and thread handoff evidence

Produce one `validation.md` record with deterministic semantic-export fingerprint, exact lineage tuple, toolchain version, static artifact checks, rendered-report interaction checks, and mandatory reconciliation checkpoints, then update thread state so downstream work does not reopen semantic-export or dashboard-contract decisions unless the recorded fingerprint changes.

## Task/Wave Breakdown

### Task 0: Freeze approved authoring inputs

**Purpose:**
- lock exact upstream inputs and fail early on contract drift before PBIP work starts

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-14-25-historical-power-bi-report-build-spec.md`
- Inspect: `data/scoped/power_bi/semantic_contract.json`
- Inspect: `data/scoped/power_bi/dashboard_mvp_manifest.json`
- Inspect: `data/scoped/power_bi/`
- Verify: `docs/superpowers/specs/2026-06-28-14-25-historical-power-bi-report-build-spec.md`
- Verify: `data/scoped/power_bi/semantic_contract.json`
- Verify: `data/scoped/power_bi/dashboard_mvp_manifest.json`

**Preconditions:**
- approved historical Power BI report-build spec is current
- semantic-export parquet inputs and authoring contracts already exist under `data/scoped/power_bi/`

**Steps:**
- [ ] Step 1: inspect semantic-export folder and confirm six runtime parquet inputs exist alongside authoring-only JSON contracts
- [ ] Step 2: verify frozen contract consistency across approved spec, `semantic_contract.json`, and `dashboard_mvp_manifest.json` for page count, slicer scope, relationship topology, field visibility, exported measure names, and scenario labeling
- [ ] Step 3: fail Task 0 if those frozen sources disagree instead of recording new decisions in a second source of truth
- [ ] Step 4: freeze one deterministic fingerprint recipe: SHA-256 over the exact bytes of the six parquet files plus `semantic_contract.json` and `dashboard_mvp_manifest.json`, using lexicographic relative-path order
- [ ] Step 5: freeze exact report-build scope: PBIP project, portable binding, model, pages, validation record, and thread-state update only

**Verification:**
- [ ] inspect source artifacts and confirm implementation can start without reopening semantic-export or spec decisions
- [ ] inspect frozen contracts and confirm fingerprint recipe and report-build boundary are explicit

**Exit Criteria:**
- approved upstream contracts are mutually consistent and frozen enough for direct implementation

### Task 1: Scaffold canonical PBIP project and portable data binding

**Purpose:**
- create repo-tracked report project with exact file name, portable import root, and bounded runtime table list

**Files:**
- Inspect: `data/scoped/power_bi/`
- Modify: `reports/power_bi/historical_evaluation/`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Task 0 complete
- local Power BI Desktop workflow available for PBIP authoring

**Steps:**
- [ ] Step 1: create canonical PBIP project root under `reports/power_bi/historical_evaluation/` with exactly one entry file named `historical_evaluation.pbip`
- [ ] Step 2: define one Power Query parameter named `SemanticExportRoot`
- [ ] Step 3: bind exactly six runtime parquet tables through `SemanticExportRoot`
- [ ] Step 4: ensure `semantic_contract.json` and `dashboard_mvp_manifest.json` are not imported as runtime model tables
- [ ] Step 5: ensure no user-specific absolute path remains outside the `SemanticExportRoot` parameter value
- [ ] Step 6: disable Power BI Auto date/time for this project so authored-table count stays stable
- [ ] Step 7: persist report-project source files in repo-tracked form only

**Verification:**
- [ ] inspect PBIP source and confirm `historical_evaluation.pbip` is the only `.pbip` entry file
- [ ] inspect PBIP source and confirm `SemanticExportRoot` exists and all six parquet imports resolve from it
- [ ] inspect project source and confirm no hidden absolute local path remains outside the parameter value
- [ ] inspect project settings and confirm Auto date/time is disabled

**Exit Criteria:**
- PBIP project exists with one canonical entry file and portable parameterized runtime binding

### Task 2: Implement semantic model contracts

**Purpose:**
- encode exact relationships, field visibility, types, current contract fields, and grain-safe measures in the Power BI model

**Files:**
- Inspect: `data/scoped/power_bi/semantic_contract.json`
- Modify: `reports/power_bi/historical_evaluation/`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Task 1 complete
- semantic contract remains source of truth for keys, visibility, and exported horizon formulas

**Steps:**
- [ ] Step 1: create active one-to-many single-direction relationships exactly as frozen in spec and semantic contract, using `horizon_id` for `dim_date_hour` joins
- [ ] Step 2: keep model shape to exactly six authored data tables and do not add a dedicated Measures table
- [ ] Step 3: hide imported horizon ratio columns, hidden traceability duplicates, and non-author-facing technical fields
- [ ] Step 4: expose dimension-owned visible labels only, while keeping current required slicer field `scenario_key`
- [ ] Step 5: keep current decision-contract field `selected_for_review` as required report field for this thread
- [ ] Step 6: implement current exported horizon measures on `fact_horizon_summary` using the exact names frozen in `semantic_contract.json`
- [ ] Step 7: implement required event-grain measures on `fact_event_decision`
- [ ] Step 8: assign explicit data types, sort behavior, and format strings, including `hour_label` sorted by `hour_of_day`
- [ ] Step 9: if report-local helper fields are added, keep them additive only and do not replace exported keys, slicer fields, or horizon measure names

**Verification:**
- [ ] inspect model relationships and confirm no inactive, bidirectional, many-to-many, or fact-to-fact relationships exist
- [ ] inspect model structure and confirm exactly six authored data tables exist with no dedicated Measures table
- [ ] inspect fields and confirm visible labels come from dimensions and hidden imported ratios remain non-visible
- [ ] inspect measures and confirm exported horizon measure names match `semantic_contract.json` exactly and event measures stay separate
- [ ] inspect model types, sort behavior, and format strings against frozen contract

**Exit Criteria:**
- semantic model matches frozen contract and cannot silently mix global horizon and event-detail logic

### Task 3: Author exactly two report pages

**Purpose:**
- build bounded descriptive dashboard surface with fixed slicer behavior and visual contracts

**Files:**
- Inspect: `data/scoped/power_bi/dashboard_mvp_manifest.json`
- Modify: `reports/power_bi/historical_evaluation/`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Task 2 complete
- required measures and visible fields already exist

**Steps:**
- [ ] Step 1: create Page 1 `Overview and Capacity` with only date, hour, and scenario slicers plus required horizon KPI cards, trend visual, and lineage area
- [ ] Step 2: create Page 2 `Candidate and Station Detail` with `selected_vs_not_selected_breakdown`, station table, train-service table, probability distribution visual, and page-2-only slicers
- [ ] Step 3: configure slicer synchronization so date, hour, and `scenario_key` sync across both pages while station, train service, eligibility, and `selected_for_review` remain page-2-only
- [ ] Step 4: confirm no hidden tooltip, drillthrough, or extra pages remain in project
- [ ] Step 5: keep titles, subtitles, and labels descriptive-only with no causal or avoided-delay claims

**Verification:**
- [ ] inspect report pages and confirm exactly two total visible pages exist
- [ ] inspect slicer placement and sync settings against frozen contract
- [ ] inspect page visuals and confirm Page 1 uses exported horizon measures while Page 2 uses event measures

**Exit Criteria:**
- report surface is bounded, semantically correct, and aligned to frozen MVP manifest

### Task 4: Refresh, validate, and record evidence

**Purpose:**
- prove real report artifact loads, travels, behaves, and reconciles against one exact semantic export

**Files:**
- Modify: `reports/power_bi/historical_evaluation/validation.md`
- Verify: `reports/power_bi/historical_evaluation/validation.md`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Tasks 1 through 3 complete
- Power BI Desktop can run full refresh locally

**Steps:**
- [ ] Step 1: compute and record semantic-export fingerprint using the frozen SHA-256 recipe
- [ ] Step 2: record validation context in `validation.md`: fingerprint, `optimization_run_id`, `execution_mode`, `prediction_split`, `policy_version`, `model_version`, `scenario_key`, `validated_at`, `report_commit`, Power BI Desktop version, PBIP project format, and operating system
- [ ] Step 3: run one successful full refresh covering all six parquet tables from the original `SemanticExportRoot`
- [ ] Step 4: point `SemanticExportRoot` to a second valid root containing the same frozen inputs, refresh again, and confirm no per-query edits are required
- [ ] Step 5: record `Artifact-Level Validation` evidence for canonical `.pbip` file name, exact six authored data tables, `SemanticExportRoot`, relationship topology, hidden-field contracts, types, sort rules, format strings, and page count
- [ ] Step 6: record post-refresh lineage and completeness evidence: one consistent lineage tuple, `scenario_count = 1`, `execution_mode = final`, `prediction_split = test`, and reconciled event, horizon, station, train-service, date-hour, and scenario counts against parquet inputs
- [ ] Step 7: record `Rendered Report Validation` evidence for slicer synchronization, page-1 immunity to page-2-only slicers, visible descriptive wording, and probability/table behavior
- [ ] Step 8: record mandatory `Reconciliation Checkpoints` with source value, report value, difference, and result for at least:
  - full-period selected count
  - full-period precision at capacity
  - one selected date horizon checkpoint
  - one selected date-hour horizon checkpoint
  - full-period event count
  - one station event count
  - one train-service selected event count
  - one selected-vs-not-selected distribution checkpoint
- [ ] Step 9: record unresolved items under `Open Issues` only when they are explicit non-blocking deferrals

**Verification:**
- [ ] inspect `validation.md` and confirm all required sections exist with expected versus observed evidence
- [ ] inspect report and confirm both refresh runs completed without broken source bindings
- [ ] inspect `validation.md` and confirm zero unresolved failures for refresh, relationships, measure formulas, page count, slicer behavior, reconciliation, and descriptive wording

**Exit Criteria:**
- validation evidence proves report is runnable, portable across root change, semantically aligned to export contract, and free of blocking correctness failures

### Task 5: Sync thread state and preserve invalidation boundary

**Purpose:**
- close implementation with explicit thread evidence and clear stale-validation rules

**Files:**
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md`

**Preconditions:**
- Task 4 complete
- semantic-export fingerprint is unchanged since validation
- no blocking validation failures remain

**Steps:**
- [ ] Step 1: update thread status and notes with PBIP artifact completion, fingerprint, refresh success, validation evidence, and exact page/model boundaries delivered
- [ ] Step 2: record invalidation rule: any change to semantic-export or authoring-contract fingerprint requires refresh, artifact-level validation, and rendered-report revalidation before completion claims remain valid
- [ ] Step 3: keep non-goals explicit: Power BI service deployment, gateway scheduling, enterprise governance, live operations integration, causal claims, and multi-page expansion remain out of scope
- [ ] Step 4: confirm downstream readers can start from thread, spec, validation record, and PBIP artifact without reopening frozen model-contract decisions unless fingerprint changes

**Verification:**
- [ ] inspect thread notes and confirm delivery claims match `validation.md`, actual PBIP artifact, and recorded fingerprint only

**Exit Criteria:**
- thread state reflects completed bounded report-build work and preserves correct stale-validation boundary

## Verification

- inspect `reports/power_bi/historical_evaluation/` and confirm exactly one repo-tracked entry file named `historical_evaluation.pbip` exists
- inspect PBIP source and confirm `SemanticExportRoot` binds exactly six parquet runtime tables and excludes imported JSON contract tables
- confirm no hidden absolute local path remains outside the parameter value
- confirm Auto date/time is disabled and runtime model has exactly six authored data tables with no dedicated Measures table
- confirm relationships are active one-to-many single-direction only and use current exported keys
- confirm imported horizon ratios and duplicated traceability labels remain hidden
- confirm required scenario and decision slicer fields remain `scenario_key` and `selected_for_review`
- confirm exported horizon measure names match `semantic_contract.json`
- confirm types, sort behavior, and format strings match frozen contract
- confirm exactly two visible pages exist and no hidden tooltip or drillthrough pages remain
- confirm Page 1 uses exported horizon measures only and Page 2 uses event-grain visuals and measures
- confirm `validation.md` records fingerprint, exact lineage tuple, two successful refreshes under different root locations, artifact checks, rendered-report checks, and mandatory reconciliation checkpoints
- confirm Task 5 is not executed while any blocking validation failure remains
- confirm thread state says report-build complete without claiming service deployment, live decision support, or causal intervention impact

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
