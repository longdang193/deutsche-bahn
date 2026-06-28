---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: historical-power-bi-report-build
parent_thread: deutsche-bahn-decision-dashboard.historical-power-bi-report-build
targets:
  - data/scoped/power_bi/
  - reports/power_bi/historical_evaluation/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md
related_features: []
related_stages: []
---

## Goal

Define exact local Power BI report-build layer that consumes validated Deutsche Bahn semantic export and produces one repo-tracked historical evaluation report artifact with frozen relationships, portable input binding, current semantic-export measure names, current slicer-field contract, and exactly two descriptive pages.

## Key Deliverables

### Repo-tracked local report artifact contract

Define one concrete local report artifact contract, including report project format, owned file paths, portable semantic-export root binding, runtime parquet inputs, authoring-only JSON inputs, and explicit separation between report build, semantic export, and enterprise deployment concerns.

### Semantic model and visual behavior contract

Define one exact report model contract, including relationship cardinality and direction, visible and hidden fields, horizon-grain versus event-grain measures, slicer synchronization rules, page composition, lineage display, prototype labeling, and descriptive-only wording requirements.

### Validation and closeout boundary

Define one bounded validation contract that proves real report artifact refreshes successfully, preserves semantic-export contracts, and behaves correctly in rendered Power BI while keeping service deployment, refresh automation, and governance concerns out of scope.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- define current report-build boundary, authoring constraints, and downstream validation needs before choosing concrete artifact rules

**Steps:**
- [ ] inspect semantic-export source-of-truth surfaces
- [ ] identify unresolved report artifact and validation edges
- [ ] record affected invariants, manual-check boundaries, and ownership split between export and report authoring

**Verification:**
- [ ] current-state understanding is explicit enough to support concrete report-build decisions

**Exit Criteria:**
- no core report-build decision depends on unstated assumptions

### Wave 2: Decision closure

**Purpose:**
- resolve local report artifact, model, and page-design choices

**Steps:**
- [ ] define major report-build decisions
- [ ] compare alternatives where non-obvious
- [ ] record impact on report files, manual validation flow, and downstream implementation planning

**Verification:**
- [ ] each major report-build question has documented decision or explicit deferral

**Exit Criteria:**
- report-build design is internally coherent and bounded

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare spec for report-authoring implementation handoff by making proof expectations explicit

**Steps:**
- [ ] define artifact-level and rendered-report validation plan
- [ ] confirm invariant preservation strategy between semantic export and report build
- [ ] identify open approval questions or follow-up notes

**Verification:**
- [ ] validation plan proves intended report behavior and contract preservation

**Exit Criteria:**
- spec is ready for implementation planning

## Design Decisions

### Decision: Use PBIP project format as repo-tracked report artifact

- context: this thread must produce real local Power BI report artifact that can be versioned in git and reviewed as source, while PBIX is binary and hard to diff
- choice: require one Power BI Project under `reports/power_bi/historical_evaluation/` with `.pbip` entry file as canonical report artifact
- alternatives considered:
  - commit only `.pbix` file
  - keep report outside repo and track screenshots or notes only
  - stop at semantic-export metadata without real report artifact
- impact:
  - report changes become reviewable and repo-tracked
  - downstream implementation must use local Power BI Desktop workflow that can author PBIP
  - real report validation becomes possible without claiming metadata-only completion

### Decision: Report consumes six runtime parquet tables through one portable root parameter

- context: upstream semantic export owns table shape, scenario identity, hidden imported ratios, and metadata handoff boundaries, but report build must stay portable across machines
- choice:
  - runtime report inputs are only:
    - `fact_event_decision.parquet`
    - `fact_horizon_summary.parquet`
    - `dim_date_hour.parquet`
    - `dim_station.parquet`
    - `dim_train_service.parquet`
    - `dim_scenario.parquet`
  - report defines one Power Query parameter named `SemanticExportRoot`
  - each parquet table path resolves relative to `SemanticExportRoot`
  - `semantic_contract.json` and `dashboard_mvp_manifest.json` are authoring and validation inputs only, not runtime imported tables
- alternatives considered:
  - reconnect report directly to optimization outputs
  - hard-code absolute local paths into report project
  - import JSON contracts as visible report tables
- impact:
  - report stays portable across local machines
  - runtime model stays bounded to six parquet tables
  - JSON contracts remain SSOT for authoring checks without polluting semantic model

### Decision: Require successful full refresh before validation or closure

- context: static project files alone do not prove report can load all semantic-export inputs
- choice: this thread is not closable until Power BI Desktop completes one successful refresh of all six parquet tables with no broken source bindings
- alternatives considered:
  - allow static artifact completion without data refresh
  - refresh subset of tables only
  - treat imported metadata as enough proof
- impact:
  - closeout proves report is runnable, not only drafted
  - validation evidence must include refresh success record
  - broken local path binding becomes must-fix, not deferred ambiguity

### Decision: Use one star-schema model with exact exported join keys

- context: dashboard must preserve current semantic-export model exactly; report-build layer should not reinterpret exported identities
- choice: define exact active relationships:
  - `dim_date_hour[horizon_id] -> fact_event_decision[horizon_id]`
  - `dim_date_hour[horizon_id] -> fact_horizon_summary[horizon_id]`
  - `dim_scenario[scenario_key] -> fact_event_decision[scenario_key]`
  - `dim_scenario[scenario_key] -> fact_horizon_summary[scenario_key]`
  - `dim_station[station_id] -> fact_event_decision[station_id]`
  - `dim_train_service[train_service_key] -> fact_event_decision[train_service_key]`
  - every relationship is `one-to-many`
  - every relationship is `single direction` from dimension to fact
  - every relationship is `active`
  - no fact-to-fact relationships
  - no bidirectional relationships
  - no many-to-many relationships
- alternatives considered:
  - rename joins to `date_hour_key` in report-build layer only
  - relate station or train dimensions to horizon fact through denormalized keys
  - flatten into single denormalized report table
- impact:
  - report stays aligned to exported contract
  - time-dimension identity remains stable across export and report build
  - model remains easy to inspect and validate against contract

### Decision: Separate visible labels from hidden traceability fields

- context: event fact physically contains descriptive fields for traceability, but display ownership must remain dimensional to avoid multiple visible sources of truth
- choice: keep duplicated descriptive event-fact fields hidden in report model and expose display labels from dimensions only:
  - station display from `dim_station`
  - train/service display from `dim_train_service`
  - date/hour display from `dim_date_hour`
  - scenario metadata and scenario display fields from `dim_scenario`
- alternatives considered:
  - expose both fact and dimension label fields
  - hide dimensions and display directly from event fact
  - delete traceability fields from event fact in report model
- impact:
  - display semantics stay symmetric and predictable
  - report visuals have one visible owner for each descriptive label
  - report can use `scenario_display_name` in titles or metadata while keeping `scenario_key` as contract field for slicers and joins

### Decision: Keep current semantic-export measure names and separate them by grain

- context: semantic export already freezes horizon measure names in `semantic_contract.json`; report-build layer should not rename them and create a second naming contract
- choice:
  - Page 1 uses current exported horizon measure names:
    - `Selected Events`
    - `Eligible Events`
    - `Candidate Severe Events`
    - `Selected Severe Events`
    - `Candidate Prevalence`
    - `Precision at Capacity`
    - `Severe-Delay Coverage`
    - `Selection Lift`
    - `Capacity Utilization`
  - report may add `Available Capacity`, `Used Capacity`, and `Unused Capacity` only if derived directly from exported horizon counts and kept clearly documented as report-local measures
  - Page 2 uses event-grain measures only, including:
    - `Event Count`
    - `Eligible Event Count`
    - `Selected Event Count`
    - `Actual Severe Event Count`
    - `Selected Severe Event Count`
    - `Average Predicted Severe Probability`
  - imported horizon ratio columns remain hidden and must not be used directly in visuals
- alternatives considered:
  - rename exported horizon measures with `Horizon` prefix in report-build layer only
  - expose imported ratio columns directly
  - reuse horizon measures on station/train visuals
- impact:
  - report stays aligned to current semantic export SSOT
  - page visuals cannot silently mix incompatible grain
  - reconciliation remains direct against exported formulas

### Decision: Freeze slicer scope using current exported slicer fields

- context: manifest and semantic contract already freeze current slicer fields; report-build layer should not invent different required slicer fields
- choice:
  - synchronized across both pages:
    - `calendar_date`
    - `hour_of_day`
    - `scenario_key`
  - page-2 only and not synchronized to page 1:
    - `station_id`
    - `train_service_key`
    - `eligibility_reason`
    - `selected_for_review`
  - page-1 visuals must ignore page-2-only slicers by model topology and interaction settings
- alternatives considered:
  - replace required scenario field with `scenario_display_name`
  - replace required Page-2 decision field with `decision_status`
  - synchronize all slicers across pages
- impact:
  - report stays aligned to current handoff contracts
  - global horizon page stays semantically correct
  - manual validation has exact expected behavior to prove

### Decision: Build exactly two total report pages from frozen manifest

- context: upstream dashboard manifest already freezes bounded MVP page set and visual groups, but page-count wording must exclude hidden extras
- choice: implement exactly two total report pages:
  - `Overview and Capacity`
  - `Candidate and Station Detail`
  - no hidden tooltip pages
  - no hidden drillthrough pages
  - no extra hidden or visible report pages
- alternatives considered:
  - one page only
  - three or more pages with storytelling expansion now
  - hidden tooltip or drillthrough helper pages
- impact:
  - implementation remains bounded and reviewable
  - report validation can target finite visual surface
  - later storytelling or drillthrough additions remain downstream work

### Decision: Defer report-local `decision_status` grouping until upstream handoff contracts require it

- context: current handoff contracts use `selected_for_review` as decision slicer field and `selected_vs_not_selected_breakdown` as required visual group
- choice:
  - current MVP report contract requires `selected_for_review` support
  - report-local `decision_status` derivation is optional and must not replace current required contract fields in this thread
- alternatives considered:
  - require `decision_status` now even though upstream handoff contracts do not mention it
  - invent dual required decision contracts
- impact:
  - SSOT stays with current semantic-export handoff
  - terminology migration can happen later in one upstream change instead of one report-only change

### Decision: Split validation into artifact-level inspection and rendered-report validation

- context: PBIP is inspectable as source, but slicer interactions and rendered totals still need live Power BI validation
- choice:
  - artifact-level validation covers static report-project contract
  - rendered-report validation covers live refresh, slicer behavior, visuals, and total reconciliation
  - both evidence sets must be recorded in `reports/power_bi/historical_evaluation/validation.md`
- alternatives considered:
  - manual-only validation
  - static-only validation
  - screenshots without structured evidence
- impact:
  - easy checks can be automated later without changing spec contract
  - manual validation stays focused on runtime behavior only
  - evidence stays structured and reviewable

## Output Contracts

### Report project root

`reports/power_bi/historical_evaluation/` must contain:

- one `.pbip` entry file as canonical report-project entrypoint
- repo-tracked Power BI project contents generated by report-authoring workflow
- one Power Query parameter named `SemanticExportRoot`
- `validation.md` with structured validation results, checked date, refresh status, and observed totals/interactions

### Runtime import contract

- imported runtime tables are exactly:
  - `fact_event_decision`
  - `fact_horizon_summary`
  - `dim_date_hour`
  - `dim_station`
  - `dim_train_service`
  - `dim_scenario`
- imported runtime tables all resolve under `SemanticExportRoot`
- `semantic_contract.json` and `dashboard_mvp_manifest.json` may be read during authoring or validation but must not appear as runtime tables in report model

### Relationship contract

- `dim_date_hour` filters both facts on `horizon_id`
- `dim_scenario` filters both facts on `scenario_key`
- `dim_station` filters `fact_event_decision` on `station_id` only
- `dim_train_service` filters `fact_event_decision` on `train_service_key` only
- all relationships are active, one-to-many, single-direction dimension-to-fact
- no inactive alternate relationships
- no fact-to-fact, many-to-many, or bidirectional relationships

### Page 1: `Overview and Capacity`

Purpose:

- show global historical policy performance by date, hour, and scenario

Must contain at minimum:

- cards for `Selected Events`, `Eligible Events`, `Candidate Severe Events`, `Selected Severe Events`
- cards for `Candidate Prevalence`, `Precision at Capacity`, `Severe-Delay Coverage`, `Selection Lift`, and `Capacity Utilization`
- one date-hour capacity trend visual driven from `fact_horizon_summary`
- one small lineage or metadata area showing at minimum:
  - `scenario_key`
  - `scenario_display_name`
  - `model_version`
  - `policy_version`
  - optimization timestamp or equivalent exported optimization run timestamp
- prototype scenario labeling visible in subtitle or metadata area
- slicers for `calendar_date`, `hour_of_day`, and `scenario_key`

Must not contain:

- station slicer
- train-service slicer
- eligibility slicer
- selected-for-review slicer

### Page 2: `Candidate and Station Detail`

Purpose:

- explore event-level predictions, eligibility, selections, stations, and train services

Must contain at minimum:

- one `selected_vs_not_selected_breakdown` visual from `fact_event_decision` using `selected_for_review`
- one station detail table with exactly these minimum columns:
  - dimension-owned station label
  - `Event Count`
  - `Eligible Event Count`
  - `Selected Event Count`
  - `Actual Severe Event Count`
  - `Selected Severe Event Count`
  - `Average Predicted Severe Probability`
- one train-service detail table with exactly these minimum columns:
  - dimension-owned train-service label
  - `Event Count`
  - `Eligible Event Count`
  - `Selected Event Count`
  - `Actual Severe Event Count`
  - `Selected Severe Event Count`
  - `Average Predicted Severe Probability`
- one probability distribution visual with fixed contract:
  - chart type: histogram or column-binned distribution
  - input grain: event fact only
  - x-axis: predicted severe probability bins
  - y-axis: `Event Count`
  - series/grouping: `selected_for_review`
  - null predicted probabilities excluded
- slicers for `calendar_date`, `hour_of_day`, `scenario_key`, `station_id`, `train_service_key`, `eligibility_reason`, and `selected_for_review`

### Slicer synchronization contract

| Slicer | Page 1 | Page 2 | Synchronized |
| --- | --- | --- | --- |
| `calendar_date` | yes | yes | yes |
| `hour_of_day` | yes | yes | yes |
| `scenario_key` | yes | yes | yes |
| `station_id` | no | yes | no |
| `train_service_key` | no | yes | no |
| `eligibility_reason` | no | yes | no |
| `selected_for_review` | no | yes | no |

### Field visibility rules

Report model must keep hidden:

- imported horizon ratio fields:
  - `candidate_prevalence`
  - `precision_at_capacity`
  - `severe_delay_coverage`
  - `lift_over_candidate_prevalence`
- duplicated descriptive event-fact fields used only for traceability
- technical identity fields not intended for report author interaction when matching dimension-owned visible labels
- internal metadata fields not intended for report author interaction

Visible report fields must follow semantic export contract ownership.

### Measure contract

- horizon measures are Page-1 measures and must aggregate from `fact_horizon_summary`
- event measures are Page-2 measures and must aggregate from `fact_event_decision`
- exported horizon measure names must match `semantic_contract.json`
- report-local derived measures must remain clearly documented and must not overwrite exported measure names
- percentage measures must define explicit percentage format strings
- ratio measures must use blank-safe division behavior rather than divide-by-zero errors

### Validation evidence contract

`validation.md` must contain these sections in this order:

1. `Refresh Validation`
2. `Artifact-Level Validation`
3. `Rendered Report Validation`
4. `Reconciliation Checkpoints`
5. `Open Issues`

Each validation row must record at minimum:

- check name
- expected behavior
- observed behavior
- result

## Acceptance Criteria

- one repo-tracked PBIP report project exists under `reports/power_bi/historical_evaluation/`
- report defines portable `SemanticExportRoot` parameter and uses it for all six parquet imports
- report refreshes successfully against all six semantic-export parquet tables
- runtime semantic model contains exactly six parquet tables and no runtime JSON contract tables
- report relationships match semantic export relationship topology exactly, including active state, one-to-many cardinality, and single-direction filtering
- required horizon and event measure families exist with grain-appropriate formulas
- exported horizon measure names match `semantic_contract.json`
- imported horizon ratios are hidden and not used as user-facing measures
- exactly two total report pages exist, both visible, with no hidden tooltip or drillthrough pages
- scenario slicer uses `scenario_key` as required contract field
- station/train descriptive display fields come from dimensions, not visible event-fact duplicates
- Page-2 decision visuals use `selected_for_review` as current required contract field
- page-1 slicers are only date, hour, and scenario
- page-2 station/train/eligibility/selection slicers are not synchronized to page 1
- manual validation confirms page-1 horizon visuals do not change under page-2-only slicer changes
- manual validation confirms date, hour, and scenario slicers filter both facts correctly
- report wording remains descriptive-only and does not claim avoided delays or intervention effects
- `validation.md` records structured refresh, artifact, interaction, and reconciliation evidence

## Non-Goals

- modify semantic-export table contracts, scenario identity, or upstream optimization outputs
- rename exported keys, slicer fields, or horizon measure names in report-build layer only
- create Power BI service deployment, gateway, scheduled refresh, or workspace automation
- add row-level security, enterprise governance, or publication workflows
- infer causal intervention benefit or avoided-delay claims
- expand beyond two MVP pages in this thread
- automate Power BI UI interaction testing beyond bounded validation record

## Risks and Mitigations

- risk: report authoring may drift from semantic-export contract
  - mitigation: use semantic contract and manifest as authoring inputs and validate report against them explicitly

- risk: imported horizon ratios may be exposed and misused in visuals
  - mitigation: require them hidden and validate that visible ratio measures use atomic counts only

- risk: station or train slicers may accidentally affect capacity visuals
  - mitigation: freeze exact slicer synchronization rules and validate rendered interactions explicitly

- risk: report-only renaming could create conflicting contracts
  - mitigation: keep current exported keys, slicer fields, and exported horizon measure names unchanged in this thread

- risk: binary-only report artifacts would weaken reviewability
  - mitigation: require PBIP project format as canonical repo-tracked artifact

- risk: report could overclaim prototype value
  - mitigation: require explicit prototype scenario labeling, lineage area, and descriptive-only wording on both pages

## Invariants

- report must consume semantic-export artifacts only
- report must not reconnect directly to upstream optimization or ML artifacts
- runtime report model must contain exactly six authored data tables
- report relationship topology must remain identical to semantic export contract
- imported horizon ratio columns must remain hidden and reconciliation-only
- visible descriptive labels must come from dimensions, not duplicated event-fact display fields
- scenario identity remains `scenario_key`
- Page-1 and Page-2 required slicer fields remain aligned to current exported handoff contracts
- page-1 horizon visuals must remain filterable only by date, hour, and scenario
- page-2-only slicers must not affect page-1 horizon visuals
- report must expose exactly two total pages in this thread
- report must preserve descriptive-only semantics and must not claim intervention effectiveness
- manual validation evidence must exist before this thread is closed

## Validation Plan

- proof target: report artifact is repo-tracked and local
  - method: inspection
  - evidence: PBIP project exists under `reports/power_bi/historical_evaluation/` with `validation.md`

- proof target: report binds inputs through portable root parameter
  - method: inspection
  - evidence: report project defines `SemanticExportRoot` and each imported parquet source resolves from it

- proof target: report refreshes successfully
  - method: run
  - evidence: `validation.md` records one successful full refresh for all six parquet tables

- proof target: runtime model contains only six authored data tables
  - method: inspection
  - evidence: report model table list includes only six parquet imports and excludes JSON contracts as runtime tables

- proof target: relationship topology matches semantic export contract
  - method: inspection and comparison
  - evidence: report model relationship definitions match `semantic_contract.json` exactly for keys, cardinality, direction, and active state

- proof target: DAX measures preserve intended grain and formulas
  - method: inspection and comparison
  - evidence: report measure definitions match exported horizon formulas from `semantic_contract.json` where applicable and implement required event-grain measures from this spec

- proof target: imported horizon ratios are hidden and not exposed as report measures
  - method: inspection
  - evidence: report field visibility matches semantic export hidden-field contract

- proof target: page composition stays bounded
  - method: inspection
  - evidence: report contains exactly two total visible pages and required visual groups from `dashboard_mvp_manifest.json`

- proof target: slicer synchronization matches frozen contract
  - method: run and inspection
  - evidence: `validation.md` records that date, hour, and scenario slicers filter both pages, while station/train/eligibility/selection slicers affect page 2 only

- proof target: page-1 horizon visuals stay global under page-2-only slicers
  - method: run and inspection
  - evidence: `validation.md` records unchanged page-1 horizon KPI values under station, train, eligibility, and selected-for-review slicer changes

- proof target: page-2 event totals reconcile to semantic export
  - method: comparison
  - evidence: `validation.md` records selected checkpoints where event-level report totals match `fact_event_decision.parquet`

- proof target: page-1 horizon totals reconcile to semantic export
  - method: comparison
  - evidence: `validation.md` records selected checkpoints where horizon-level report totals match `fact_horizon_summary.parquet`

- proof target: report wording remains descriptive-only
  - method: inspection
  - evidence: report titles, subtitles, metadata area, and scenario labels contain prototype/descriptive wording and no avoided-delay or intervention-effect claims

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
