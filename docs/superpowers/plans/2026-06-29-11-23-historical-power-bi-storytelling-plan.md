---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: historical-power-bi-storytelling
parent_thread: deutsche-bahn-decision-dashboard.historical-power-bi-report-build
parent_spec: docs/superpowers/specs/2026-06-29-10-59-historical-power-bi-storytelling-spec.md
targets:
  - reports/power_bi/historical_evaluation/
  - data/scoped/power_bi/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md
related_features: []
related_stages: []
---

## Goal

Implement the historical Power BI storytelling rewrite on top of the current local PBIP report so the dashboard becomes a clear three-page narrative with single-scenario behavior, exact filter interactions, corrected event-versus-horizon semantics, plain-language labels, and validation evidence that stays truthful under the bounded six-table semantic export.

## Key Deliverables

### Updated PBIP report with three-page storytelling flow

Update the existing report under `reports/power_bi/historical_evaluation/` so it exposes exactly three visible pages named `What Happened`, `Which Events Look Risky`, and `Which Events Were Chosen For Review`, with the visual set, slicer scope, metadata strip, and interaction rules defined by the storytelling spec.

### Corrected semantic model helpers and measures

Implement the required helper columns, report measures, sorting rules, single-select scenario behavior, scenario fail-safe, and network-capacity interaction protections so event-level visuals, horizon-level capacity visuals, and metadata displays remain mathematically consistent under filter context.

### Validation evidence and thread-ready handoff

Update `validation.md` and thread notes with independent parquet-based reconciliation proof, interaction proof, count identities, deterministic ranking checks, relationship-topology checks, and stale-validation boundaries for the storytelling rewrite without reopening upstream semantic-export scope.

## Task/Wave Breakdown

### Task 0: Freeze storytelling inputs, source semantics, and model topology

**Purpose:**
- lock the exact source surfaces for the rewrite, replace the old two-page page contract, and freeze source meanings before report edits begin

**Files:**
- Inspect: `docs/superpowers/specs/2026-06-29-10-59-historical-power-bi-storytelling-spec.md`
- Inspect: `docs/superpowers/plans/2026-06-28-14-47-historical-power-bi-report-build-plan.md`
- Inspect: `data/scoped/power_bi/`
- Verify: `docs/superpowers/specs/2026-06-29-10-59-historical-power-bi-storytelling-spec.md`

**Preconditions:**
- storytelling spec is the latest approved dashboard-story source
- current PBIP report already exists under `reports/power_bi/historical_evaluation/`

**Steps:**
- [ ] Step 1: inspect the storytelling spec and current six imported parquet tables to confirm this rewrite stays inside current semantic export
- [ ] Step 2: treat the older two-page report-build plan as prior context only; do not reuse its two-page page-count contract during implementation
- [ ] Step 3: freeze exact source-table schemas, key ownership, and visible-label ownership for dimensions versus facts
- [ ] Step 4: freeze relationship topology to verify during implementation: dimension-key uniqueness, expected fact foreign keys, active relationship set, and single-direction filter flow
- [ ] Step 5: freeze exact `unused_capacity` semantics from current export, including field name, grain, nullability, and reader-facing wording for the report
- [ ] Step 6: freeze the exact in-scope surfaces for this plan: current PBIP report, model helpers and measures, visible pages, `validation.md`, and thread notes
- [ ] Step 7: record any mismatch between current report artifact and new spec before editing the report itself

**Verification:**
- [ ] inspect current report context and confirm implementation can proceed without changing imported source-table set or upstream optimization artifacts
- [ ] inspect source parquet schemas and confirm relationship topology and `unused_capacity` meaning are explicit enough for downstream validation

**Exit Criteria:**
- execution boundary, source semantics, and model-topology expectations are explicit and the storytelling spec is the only active page-design source of truth

### Task 1: Update semantic model helpers, measures, and display contracts

**Purpose:**
- implement the model-layer logic needed for correct storytelling before rearranging visuals

**Files:**
- Inspect: `data/scoped/power_bi/`
- Modify: `reports/power_bi/historical_evaluation/`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Task 0 complete
- Power BI Desktop authoring workflow available for local PBIP edits

**Steps:**
- [ ] Step 1: confirm the report still imports exactly six parquet source tables through `SemanticExportRoot`
- [ ] Step 2: implement or update helper columns on `fact_event_decision` for `Review Eligibility`, `Review Decision`, `Actual Outcome`, `Predicted Risk Band`, and `Predicted Risk Band Sort`
- [ ] Step 3: implement or update visible report measures from the storytelling spec, including `Average Reviewable Predicted Risk` and `Reviewable Risk Rank In Current Filter`
- [ ] Step 4: add non-reader-facing scenario-state guard logic so scenario-dependent visuals return blank or warning state unless exactly one `scenario_key` is active
- [ ] Step 5: define denominator behavior explicitly for measures that compare chosen rows against the full reviewable pool so later filter interactions cannot silently trivialize them
- [ ] Step 6: apply required sort-by behavior for predicted-risk bands and required format strings for counts, percentages, multiplier lift, and timestamp
- [ ] Step 7: implement metadata-strip behavior so it shows only reader-facing singular values, while `scenario_key` stays out of the main strip
- [ ] Step 8: enforce single-select scenario slicer behavior with required default selection to the canonical exported scenario and hide clear-state affordances where available
- [ ] Step 9: hide imported ratio columns and any duplicated descriptive fields that should not be exposed in the visible report field list

**Verification:**
- [ ] inspect the report model and confirm required helper columns, measures, guard logic, sorts, and format strings match the storytelling spec and Task 0 freezes
- [ ] confirm the model still uses exactly six imported source tables and no unapproved helper table was added

**Exit Criteria:**
- report model is ready for page authoring with stable helper logic and no unresolved semantic contradictions

### Task 2: Rebuild pages to match the three-page story

**Purpose:**
- replace the old two-page surface with the exact three-page narrative contract

**Files:**
- Modify: `reports/power_bi/historical_evaluation/`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Task 1 complete
- all required measures and helper columns already exist in the model

**Steps:**
- [ ] Step 1: create or rename visible pages so final page order is exactly `What Happened`, `Which Events Look Risky`, and `Which Events Were Chosen For Review`
- [ ] Step 2: implement Page 1 visuals and remove any chosen-review visual from this page, including the old used-versus-unused capacity donut
- [ ] Step 3: implement Page 2 visuals with reviewable-risk framing and deterministic Top 20 reviewable event table behavior
- [ ] Step 4: define Top 20 behavior exactly: exclude non-reviewable rows, use unique deterministic rank, return exactly 20 rows when at least 20 reviewable rows exist, and keep row order stable under identical filter state
- [ ] Step 5: implement Page 3 visuals with chosen-review framing, chosen-vs-not-chosen split, network-capacity cards, and horizon-local chosen queue ordering
- [ ] Step 6: apply plain-language titles, intro text, tooltip wording, and subtitle wording from the spec on all pages
- [ ] Step 7: use dimension fields for visible descriptive labels where the spec requires dimension ownership
- [ ] Step 8: confirm there are exactly three visible pages and no hidden tooltip or drillthrough pages are carrying stale logic from the prior report version

**Verification:**
- [ ] inspect the rendered report and confirm each page contains the exact visual set, titles, field bindings, and ranking behavior required by the spec
- [ ] confirm Page 1 is purely pre-decision, Page 2 is scoring-only, and Page 3 is selection-focused

**Exit Criteria:**
- visible report surface matches the three-page storytelling contract exactly

### Task 3: Freeze interactions and filter-scope behavior

**Purpose:**
- make report behavior deterministic under slicers and visual clicks, especially where event-grain and horizon-grain measures coexist

**Files:**
- Modify: `reports/power_bi/historical_evaluation/`
- Verify: `reports/power_bi/historical_evaluation/`

**Preconditions:**
- Task 2 complete

**Steps:**
- [ ] Step 1: sync report-wide slicers for date, hour, and scenario across all pages
- [ ] Step 2: apply page-local slicers exactly as defined by the spec for Pages 2 and 3
- [ ] Step 3: disable chart-to-chart cross-filtering and cross-highlighting so slicers remain the only interaction driver unless the spec explicitly allows otherwise
- [ ] Step 4: enforce the Page 3 interaction exception: station and train slicers must narrow event-level visuals but must not change `[Review Slots]`, `[Unused Review Slots]`, or `How many review slots were used by hour`
- [ ] Step 5: confirm chosen-vs-not-chosen visuals operate only inside the reviewable pool and do not reclassify ineligible events through interaction side effects
- [ ] Step 6: confirm any status-filter or helper-state filtering used inside tables or charts cannot corrupt headline ratio denominators
- [ ] Step 7: verify metadata-strip singular behavior under all allowed slicer combinations
- [ ] Step 8: document a page-by-page interaction matrix in `validation.md` so later refreshes can re-check exact source-to-target behavior

**Verification:**
- [ ] inspect and manually test slicers and visual interactions to confirm station/train filters do not corrupt network-capacity visuals
- [ ] inspect and manually test scenario behavior to confirm invalid scenario state yields blank or warning behavior instead of duplicated counts

**Exit Criteria:**
- interaction behavior is deterministic and semantically correct under all supported filters

### Task 4: Refresh, reconcile independently, and record validation evidence

**Purpose:**
- prove the rewritten report refreshes and remains truthful against current exported data using evidence independent from Power BI visuals themselves

**Files:**
- Modify: `reports/power_bi/historical_evaluation/validation.md`
- Verify: `reports/power_bi/historical_evaluation/validation.md`
- Verify: `reports/power_bi/historical_evaluation/`
- Verify: `data/scoped/power_bi/`

**Preconditions:**
- Task 3 complete
- report saves cleanly in PBIP format after page and model changes
- local external query path is available for parquet validation, preferably DuckDB

**Steps:**
- [ ] Step 1: run a full local refresh against the current `SemanticExportRoot`
- [ ] Step 2: record artifact-level evidence that the report still binds only to the approved six parquet imports and contains no machine-specific absolute data path outside parameterized binding
- [ ] Step 3: calculate expected checkpoint values independently from parquet exports using DuckDB or equivalent source-side query path, not from a second Power BI visual
- [ ] Step 4: record rendered-report evidence for exact page count, page order, metadata strip, single-scenario behavior, disabled cross-highlight behavior, and relationship-topology checks
- [ ] Step 5: record reconciliation checkpoints for `[Event Count]`, `[Reviewable Event Count]`, `[Chosen Event Count]`, `[Actual Severe Event Count]`, `[Review Slots]`, and `[Unused Review Slots]`
- [ ] Step 6: record measure-identity checks including:
  - `[Event Count] = [Reviewable Event Count] + [Not Reviewable Event Count]`
  - `[Reviewable Event Count] = [Chosen Event Count] + [Reviewable Not-Chosen Event Count]` if implemented directly or derivable from source rows
  - `[Chosen Severe Event Count] <= [Chosen Event Count]`
  - `[Chosen Severe Event Count] <= [Reviewable Severe Event Count]`
- [ ] Step 7: record filter-sensitive checkpoints proving station/train slicers do not change network-capacity visuals while event-level visuals narrow correctly
- [ ] Step 8: record deterministic ranking checks for `Predicted Risk Band` ordering, Top 20 reviewable events, exact row count when eligible, tie handling, and chosen queue ordering by date, hour, rank, and `stop_event_key`
- [ ] Step 9: record scenario fail-safe checks for no scenario, one scenario, and attempted invalid scenario restoration state
- [ ] Step 10: record missing-outcome behavior and any zero-denominator cases for `DIVIDE`-based measures
- [ ] Step 11: record any non-blocking follow-up items under an explicit `Open Issues` or `Deferred` section only if they are outside the bounded storytelling rewrite

**Verification:**
- [ ] inspect `validation.md` and confirm every spec proof target has matching evidence from independent source calculations or an explicit bounded deferral
- [ ] confirm there are no unresolved blocking failures for refresh, relationships, filtering, ranking, page count, wording, or portability

**Exit Criteria:**
- validation evidence proves the storytelling rewrite is runnable, correct, portable, and ready for thread closeout or execution follow-up

### Task 5: Update thread evidence and stale-validation boundary

**Purpose:**
- sync bounded-thread state to the new storytelling rewrite so later work does not rely on the superseded two-page story

**Files:**
- Modify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md`
- Verify: `docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md`

**Preconditions:**
- Task 4 complete
- no blocking validation failures remain

**Steps:**
- [ ] Step 1: update thread notes to reference the storytelling spec and this implementation plan as the active story layer for the report
- [ ] Step 2: record delivered outcomes: three-page narrative, single-scenario behavior, corrected interaction rules, independent parquet-based validation evidence, and relationship-topology checks
- [ ] Step 3: record stale-validation rule: any change to imported Power BI parquet tables, helper columns, measures, relationships, visual bindings, interactions, scenario defaults, or Power BI Desktop version requires refresh and revalidation before renewed completion claims
- [ ] Step 4: keep non-goals explicit: no baseline-comparison page, no service deployment, no causal impact claim, and no semantic-export expansion in this thread

**Verification:**
- [ ] inspect thread notes and confirm they match the implemented report and `validation.md` without restating outdated two-page behavior

**Exit Criteria:**
- thread state points future execution to the current storytelling rewrite rather than the superseded two-page story

## Verification

- inspect `reports/power_bi/historical_evaluation/` and confirm the PBIP report still binds exactly six parquet source tables through `SemanticExportRoot`
- confirm no machine-specific absolute data path remains outside the parameterized binding
- confirm the report exposes exactly three visible pages in the required order and no hidden report pages carry stale dashboard logic
- confirm the scenario slicer is single-select, required, and defaults to the canonical scenario
- confirm invalid scenario state yields blank or warning behavior rather than duplicated counts
- confirm the metadata strip shows only the specified reader-facing values and remains singular under allowed filters
- confirm relationship topology matches Task 0 freezes for key uniqueness, active links, and filter direction
- confirm Page 1 contains no chosen-review visual
- confirm Page 2 Top 20 logic is deterministic, row-order invariant, limited to reviewable events, and returns exactly 20 rows when available
- confirm Page 3 station/train filters do not alter network-capacity visuals
- confirm `Review Decision`, `Actual Outcome`, `Predicted Risk Band`, and ranking logic match the storytelling spec exactly
- confirm lift displays as multiplier, not percentage
- confirm `validation.md` records independent parquet-based reconciliation, measure identities, ranking checks, interaction checks, portability checks, and missing-outcome behavior
- confirm thread notes reference the storytelling rewrite as the current report story contract

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
