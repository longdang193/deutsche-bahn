---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
name: historical-power-bi-evaluation
parent_thread: deutsche-bahn-decision-dashboard.historical-power-bi-evaluation
parent_spec: docs/superpowers/specs/2026-06-28-12-35-historical-power-bi-evaluation-spec.md
targets:
  - scripts/
  - tests/
  - data/scoped/optimization/final/
  - data/scoped/optimization/frozen_policy.json
  - data/scoped/power_bi/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-evaluation.md
related_features: []
related_stages: []
---

## Goal

Implement one local historical Power BI semantic export build that reads validated final-mode optimization artifacts only, writes one reproducible semantic dataset slice for later Power BI report authoring, preserves descriptive metric semantics, and closes with one bounded dashboard handoff contract for two-page historical evaluation.

## Key Deliverables

### Power BI semantic dataset builder

Create one local build path that reads final optimization artifacts plus frozen policy metadata, validates source contracts, and writes canonical Power BI-ready fact and dimension tables under `data/scoped/power_bi/` with stable grains, join keys, exact output columns, and one source-owned scenario identity.

### Filter-safe metric and schema validation coverage

Add targeted validation that proves fact grains, dimension joins, final/test/single-run invariants, event-to-horizon reconciliation, atomic count preservation, null metric handling, and metadata-level slicer-scope rules remain aligned with final optimization semantics and do not drift into causal or live-operations claims.

### Historical dashboard handoff readiness

Update thread state so downstream Power BI report build work can start from one clear semantic dataset contract, one bounded measure contract, and one explicit two-page MVP dashboard manifest without reopening ML or optimization assumptions.

## Task/Wave Breakdown

### Task 0: Freeze semantic export contract

**Purpose:**
- fix one source-owned semantic export contract before file generation starts

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-12-35-historical-power-bi-evaluation-spec.md`
- Inspect: `data/scoped/optimization/final/event_decision.parquet`
- Inspect: `data/scoped/optimization/final/horizon_summary.parquet`
- Inspect: `data/scoped/optimization/final/evaluation.json`
- Inspect: `data/scoped/optimization/frozen_policy.json`
- Modify: `data/scoped/power_bi/semantic_contract.json`
- Modify: `data/scoped/power_bi/dashboard_mvp_manifest.json`
- Verify: `data/scoped/power_bi/semantic_contract.json`
- Verify: `data/scoped/power_bi/dashboard_mvp_manifest.json`

**Preconditions:**
- current historical Power BI spec is current enough to freeze semantic-export scope
- final optimization artifacts exist and remain validated

**Steps:**
- [ ] Step 1: inspect final optimization artifacts and frozen policy to confirm exact required columns, scenario fields, metric ownership, and semantic-export boundary
- [ ] Step 2: freeze one explicit scenario-identity rule: `scenario_key = frozen_policy.policy_version`
- [ ] Step 3: freeze one explicit scope rule: this plan owns semantic export and dashboard handoff metadata only; actual Power BI report authoring, relationships, DAX measures, slicer interactions, and page behavior validation belong to downstream report-build work
- [ ] Step 4: freeze `semantic_contract.json` as source-owned contract metadata for exporter and tests, including:
  - exact export table list
  - exact output columns
  - key roles
  - column types
  - nullability
  - allowed ranges where applicable
  - report visibility
  - relationship topology
  - measure formulas
  - hidden imported ratio columns marked reconciliation-only
  - date and hour label formats plus sort rules
- [ ] Step 5: freeze `dashboard_mvp_manifest.json` as source-owned handoff metadata for downstream report authoring, including exactly two pages, required visuals, required slicers, allowed fact/dimension fields, and display wording expectations
- [ ] Step 6: record canonical export set as:
  - `power_bi.fact_event_decision.parquet`
  - `power_bi.fact_horizon_summary.parquet`
  - `power_bi.dim_date_hour.parquet`
  - `power_bi.dim_station.parquet`
  - `power_bi.dim_train_service.parquet`
  - `power_bi.dim_scenario.parquet`
  - `power_bi/semantic_contract.json`
  - `power_bi/dashboard_mvp_manifest.json`

**Verification:**
- [ ] inspect `semantic_contract.json` and confirm table list, grains, joins, `scenario_key` rule, exact output columns, types, nullability, visibility, hidden imported ratios, and label sort rules match plan/spec
- [ ] inspect `dashboard_mvp_manifest.json` and confirm exactly two pages are declared

**Exit Criteria:**
- semantic-export and dashboard-handoff contract are frozen enough for implementation without schema, scope, or page-manifest drift

### Task 1: Build local Power BI semantic exporter

**Purpose:**
- create one deterministic export path from final optimization outputs to Power BI-ready facts and dimensions

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-12-35-historical-power-bi-evaluation-spec.md`
- Inspect: `scripts/run_optimization_prototype.py`
- Inspect: `data/scoped/optimization/final/event_decision.parquet`
- Inspect: `data/scoped/optimization/final/horizon_summary.parquet`
- Inspect: `data/scoped/power_bi/semantic_contract.json`
- Inspect: `data/scoped/power_bi/dashboard_mvp_manifest.json`
- Modify: `scripts/build_power_bi_semantic_dataset.py`
- Modify: `data/scoped/power_bi/`
- Verify: `tests/test_build_power_bi_semantic_dataset.py`

**Preconditions:**
- Task 0 complete
- final optimization artifacts and frozen policy remain current

**Steps:**
- [ ] Step 1: add one exporter script `scripts/build_power_bi_semantic_dataset.py` that reads only:
  - `data/scoped/optimization/final/event_decision.parquet`
  - `data/scoped/optimization/final/horizon_summary.parquet`
  - `data/scoped/optimization/final/evaluation.json`
  - `data/scoped/optimization/frozen_policy.json`
  - `data/scoped/power_bi/semantic_contract.json`
  - `data/scoped/power_bi/dashboard_mvp_manifest.json`
- [ ] Step 2: enforce source invariants before any write:
  - exactly one `optimization_run_id` across final event and horizon inputs
  - all event rows have `execution_mode = 'final'`
  - all horizon rows have `execution_mode = 'final'`
  - all event rows have `prediction_split = 'test'`
  - `stop_event_key` unique in event input
  - `horizon_id` unique in horizon input
  - each `horizon_id` maps to exactly one `calendar_date` and one `hour_of_day`
  - `station_id`, `train_service_key`, and `horizon_id` are non-null in required rows
  - frozen policy `policy_version` exists and becomes exported `scenario_key`
  - one consistent source tuple across artifacts for `optimization_run_id`, `policy_version`, `model_name`, `model_version`, `capacity_scenario`, `capacity_per_hour`, `minimum_candidate_probability`, `execution_mode`, and `prediction_split`
- [ ] Step 3: enforce dimension-source consistency before building dimensions:
  - one `station_id` maps to one station attribute set
  - one `train_service_key` maps to one train-service attribute set
  - conflicting descriptive attributes fail validation instead of choosing arbitrarily
- [ ] Step 4: write `power_bi.fact_event_decision.parquet` with exact spec columns only:
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
- [ ] Step 5: use one explicit event-field mapping rule before export:
  - `scenario_key = frozen_policy.policy_version`
  - `service_class = coalesce(service_class_y, service_class_x)` with one local normalization step so join-accident suffixes do not leak past exporter boundary
  - if `station_name` missing, export `Unknown station` without changing `station_id`
  - if train descriptive fields missing, export `Unknown` display labels without changing `train_service_key`
  - descriptive duplicate fields in event fact are marked hidden in `semantic_contract.json`; visible display ownership belongs to dimensions
- [ ] Step 6: write `power_bi.fact_horizon_summary.parquet` with exact spec columns only:
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
- [ ] Step 7: validate per-horizon reconciliation before final write:
  - count of event rows per `horizon_id` equals `candidate_count`
  - count of eligible event rows per `horizon_id` equals `eligible_candidate_count`
  - count of selected event rows per `horizon_id` equals `selected_event_count`
  - count of selected severe event rows per `horizon_id` equals `actual_severe_selected_count`
  - count of severe candidate rows per `horizon_id` equals `actual_severe_candidate_count`
  - sum of `objective_contribution` per `horizon_id` equals `selected_probability_score_sum`
- [ ] Step 8: derive dimensions from approved facts and policy only:
  - `dim_date_hour` from `fact_horizon_summary`, keyed by `horizon_id`, with `calendar_date`, `hour_of_day`, `date_label`, `hour_label`
  - `dim_station` from distinct validated event `station_id`, `station_name`
  - `dim_train_service` from distinct validated event `train_service_key`, `train_type`, `line_number`, `service_class`
  - `dim_scenario` as one row from frozen policy and final evaluation metadata with `scenario_key`, `capacity_scenario`, `capacity_per_hour`, `minimum_candidate_probability`, `model_name`, `model_version`, `selected_threshold`, `policy_version`, `frozen_at`, `scenario_display_name`
- [ ] Step 9: exporter writes data tables only
  - `power_bi.fact_event_decision.parquet`
  - `power_bi.fact_horizon_summary.parquet`
  - `power_bi.dim_date_hour.parquet`
  - `power_bi.dim_station.parquet`
  - `power_bi.dim_train_service.parquet`
  - `power_bi.dim_scenario.parquet`
- [ ] Step 10: exporter validates outputs against frozen `semantic_contract.json` and does not rewrite `semantic_contract.json` or `dashboard_mvp_manifest.json`

**Verification:**
- [ ] run exporter locally and confirm six data artifacts are written under `data/scoped/power_bi/`
- [ ] inspect written facts and confirm row counts match final optimization source tables
- [ ] inspect dimensions and confirm `scenario_key` joins both facts through single-row `dim_scenario`
- [ ] inspect event export and confirm no extra columns beyond frozen contract
- [ ] inspect horizon export and confirm no extra columns beyond frozen contract
- [ ] inspect exporter behavior and confirm contract JSON files are read-only inputs, not rewritten outputs

**Exit Criteria:**
- local semantic dataset exports successfully from final optimization artifacts only with exact schema and frozen handoff metadata

### Task 2: Add contract and reconciliation tests

**Purpose:**
- prove semantic export stays reproducible, filter-scope-contract-safe, and aligned with optimization outputs

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-28-12-35-historical-power-bi-evaluation-spec.md`
- Inspect: `data/scoped/power_bi/semantic_contract.json`
- Inspect: `data/scoped/power_bi/dashboard_mvp_manifest.json`
- Modify: `tests/test_build_power_bi_semantic_dataset.py`
- Verify: `tests/test_build_power_bi_semantic_dataset.py`

**Preconditions:**
- Task 1 complete

**Steps:**
- [ ] Step 1: add tests proving input and fact grain invariants:
  - all exported rows use one `scenario_key`
  - exported `scenario_key` equals `frozen_policy.policy_version`
  - `stop_event_key` unique in event fact
  - `horizon_id` unique in horizon fact
  - exported row counts equal final optimization row counts
  - all exported event rows keep `execution_mode = 'final'` and `prediction_split = 'test'`
- [ ] Step 2: add tests proving dimension contracts:
  - one-row `dim_scenario`
  - every fact row joins to scenario
  - every event row joins to station and train-service dimensions
  - every event and horizon row joins to `dim_date_hour`
  - `dim_station.station_id` unique
  - `dim_train_service.train_service_key` unique
  - `dim_date_hour.horizon_id` unique
  - `dim_scenario.scenario_key` unique
- [ ] Step 3: add tests proving reconciliation and consistency:
  - event-to-horizon counts reconcile for candidates, eligible rows, selected rows, selected severe rows, and severe candidate rows
  - objective contribution sums reconcile to horizon selected probability sums
  - model, capacity, threshold, and run metadata stay consistent across event fact, horizon fact, evaluation metadata, and frozen policy
- [ ] Step 4: add tests proving metric semantics:
  - atomic counts match final horizon summary
  - null `precision_at_capacity`, `severe_delay_coverage`, and `lift_over_candidate_prevalence` remain null
  - `semantic_contract.json` measure formulas match spec exactly
  - imported horizon ratio columns are marked hidden/reconciliation-only in `semantic_contract.json`
  - no derived metric claims causal benefit or avoided delay
- [ ] Step 5: add tests proving slicer-scope and dashboard-handoff metadata contract:
  - station and train-service slicers are event-fact only in metadata contract
  - date, hour, and scenario slicers apply to both facts in metadata contract
  - no fact-to-fact relationship is declared
  - `dashboard_mvp_manifest.json` declares exactly two pages with spec-required visual groups only
  - tests are labeled metadata contract checks, not actual Power BI interaction tests
- [ ] Step 6: add tests proving display-field metadata rules:
  - duplicated descriptive fields on event fact are hidden in semantic contract
  - display ownership for station/train descriptors points to dimensions
  - `date_label` is display-only
  - `hour_label` sorts by `hour_of_day`

**Verification:**
- [ ] run `pytest tests/test_build_power_bi_semantic_dataset.py -q`

**Exit Criteria:**
- semantic export and dashboard-handoff contracts are covered by executable tests and metadata checks

### Task 3: Generate final artifacts and sync thread state

**Purpose:**
- persist validated semantic-export artifacts and hand off cleanly to downstream report build

**Files:**
- Inspect: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-evaluation.md`
- Modify: `data/scoped/power_bi/`
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-evaluation.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-evaluation.md`

**Preconditions:**
- Tasks 1 and 2 complete

**Steps:**
- [ ] Step 1: run final exporter against current final optimization artifacts and persist refreshed semantic-export data tables only
- [ ] Step 2: keep frozen `semantic_contract.json` and `dashboard_mvp_manifest.json` as handoff inputs for later report authoring and validate them against actual outputs
- [ ] Step 3: update thread status with completed semantic export, validated joins, final/test/single-run boundary, reconciliation status, measure boundary, and explicit note that report authoring remains downstream
- [ ] Step 4: keep deferred items explicit: real Power BI report authoring, Power BI service deployment, enterprise governance, live dispatch integration, causal claims, and multi-scenario expansion

**Verification:**
- [ ] inspect thread notes and confirm downstream dashboard build can start from exported Power BI dataset and frozen dashboard MVP manifest only
- [ ] inspect thread notes and confirm this plan does not claim actual Power BI relationships, DAX, slicer interactions, or page behavior have been validated yet

**Exit Criteria:**
- historical Power BI semantic export is complete and handoff to downstream report build is explicit

## Verification

- run `python scripts/build_power_bi_semantic_dataset.py`
- run `pytest tests/test_build_power_bi_semantic_dataset.py -q`
- inspect `data/scoped/power_bi/` and confirm six exported data tables match frozen contract
- confirm exported facts match final optimization row counts, preserve final/test invariants, and preserve null ratio semantics
- confirm per-horizon event-to-summary reconciliation passes
- confirm `semantic_contract.json` encodes only approved descriptive measures, slicer-scope metadata, relationship topology, hidden imported ratios, field visibility, types, nullability, and label sort rules
- confirm `dashboard_mvp_manifest.json` encodes exactly two pages with approved slicers and visual groups only
- confirm thread state says semantic export complete and report authoring pending

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

