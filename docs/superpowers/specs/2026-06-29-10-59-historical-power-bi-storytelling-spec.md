---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: historical-power-bi-storytelling
parent_thread: deutsche-bahn-decision-dashboard.historical-power-bi-report-build
targets:
  - reports/power_bi/historical_evaluation/
  - data/scoped/power_bi/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-historical-power-bi-report-build.md
related_features: []
related_stages: []
---

## Goal

Define exact Power BI storytelling rewrite for current historical Deutsche Bahn dashboard so user can understand, in plain language, what happened in scoped historical slice, which events looked risky, and which events were chosen for limited review capacity before any cross-policy value-comparison page is added.

## Key Deliverables

### Exact three-page storytelling contract

Define one exact three-page report sequence that starts with operational context, moves to ML risk scoring, then moves to review selection, while preserving current six imported parquet tables and replacing jargon-heavy labels with plain-language report wording.

### Exact visual and measure contract

Define exact report helper fields, DAX measures, visual titles, visual types, field bindings, filter rules, and metadata strip content so two developers would build materially same report pages from current semantic model.

### Clear boundary between explanation and proof

Define explicit wording and scope guardrails so current dashboard explains ML role and Gurobi role without claiming optimizer value against baselines that are not yet imported into current Power BI semantic export.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- define current semantic-export boundary and current dashboard-story gaps before rewriting report story

**Steps:**
- [ ] inspect current six imported Power BI parquet tables and existing report-build contracts
- [ ] identify what plain-language story can be supported without adding new runtime source tables
- [ ] record where current report must explain ML scoring versus limited-slot selection

**Verification:**
- [ ] current-state understanding is explicit enough to freeze page order, measures, and wording

**Exit Criteria:**
- no storytelling decision depends on fields that are absent from current imported semantic export

### Wave 2: Decision closure

**Purpose:**
- resolve exact report structure, labels, and visual behavior

**Steps:**
- [ ] define exact page sequence and page purpose
- [ ] define exact helper fields and DAX measures
- [ ] define exact visual bindings, slicers, metadata-strip behavior, and interaction rules

**Verification:**
- [ ] each required story step has exact visuals and exact measures, not placeholder ideas

**Exit Criteria:**
- report story is concrete enough to implement without reopening page design

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare spec for implementation handoff by making proof and non-goal boundaries explicit

**Steps:**
- [ ] define page-level validation checks
- [ ] define wording and semantics guardrails
- [ ] define deferred items that require expanded semantic export

**Verification:**
- [ ] validation plan proves report tells bounded truthful story from current data only

**Exit Criteria:**
- spec is ready for implementation planning

## Design Decisions

### Decision: Keep storytelling rewrite inside current Power BI semantic export

- context: current report already binds exactly six Power BI parquet tables under `data/scoped/power_bi/`, while cross-policy comparison tables are not yet part of current runtime semantic export
- choice:
  - current storytelling rewrite must use only these imported source tables:
    - `dim_date_hour.parquet`
    - `dim_scenario.parquet`
    - `dim_station.parquet`
    - `dim_train_service.parquet`
    - `fact_event_decision.parquet`
    - `fact_horizon_summary.parquet`
  - local calculated columns, measures, and explicitly listed helper objects are allowed
  - current rewrite must not depend on `policy_comparison.parquet`, `horizon_policy_metrics.parquet`, or development diagnostics
- alternatives considered:
  - add comparison page now and assume future table imports
  - mix current semantic export with direct optimization-final imports in report
  - keep current two-page report and only rename labels
- impact:
  - implementation stays bounded and immediately buildable on current semantic model
  - storytelling improves now without reopening semantic-export contract
  - optimizer-vs-baseline proof stays deferred until comparison tables are exported into Power BI runtime model

### Decision: Replace current two-page descriptive MVP with three-page story

- context: current dashboard does not give enough pre-decision context, so user cannot easily tell what happened before reading chosen-review outputs
- choice:
  - page 1 explains historical operational context
  - page 2 explains ML risk scoring
  - page 3 explains limited-slot review choice
  - this page contract supersedes prior exact two-page storytelling surface from `docs/superpowers/specs/2026-06-28-14-25-historical-power-bi-report-build-spec.md` while keeping same semantic-model and portability assumptions
- alternatives considered:
  - keep two pages and overpack more visuals into each
  - jump directly from operations page to decision page without ML explanation
  - add four-page story including baseline comparison before data is available in current export
- impact:
  - user gets explicit before-risk and before-decision context
  - ML and optimizer roles become separate and easier to explain
  - implementation must update current report page count from two to three

### Decision: Use plain-language labels and explicit prototype wording

- context: raw field names and optimization jargon make current dashboard hard to interpret for portfolio readers
- choice:
  - report must use plain-language labels in visuals, cards, and slicers
  - every page must state prototype and historical-evaluation framing
  - report must describe ML as risk scoring and Gurobi as limited-slot selection, not causal intervention
- alternatives considered:
  - expose raw model/optimizer terms directly
  - hide technical lineage completely
  - claim operational impact from current historical replay alone
- impact:
  - report becomes readable to non-technical reviewers
  - CV showcase remains truthful
  - technical lineage still remains visible in metadata strip

### Decision: Derive visible ratio measures from atomic counts instead of surfacing precomputed ratio columns

- context: current facts include ratio-like columns such as `candidate_prevalence`, `precision_at_capacity`, `severe_delay_coverage`, and `lift_over_candidate_prevalence`, but visible report measures must stay filter-aware and plain-language
- choice:
  - keep precomputed ratio columns hidden
  - build visible report measures from atomic event or horizon counts using `DIVIDE`
  - reserve horizon fact for network-wide review-slot and utilization logic only
- alternatives considered:
  - bind cards directly to imported ratio columns
  - use only horizon-summary ratios everywhere
  - duplicate ratio logic in multiple visuals without canonical measure names
- impact:
  - visuals stay stable under filter context
  - report keeps one visible measure definition per concept
  - page-level validation can reconcile counts and ratios cleanly

## Page Contract

### Report-wide constants

- report title: `Historical review-priority prototype`
- report subtitle: `Historical prototype: how to prioritize limited review slots during disruption`
- synced slicers on all pages:
  - `dim_date_hour[calendar_date]`
  - `dim_date_hour[hour_of_day]`
  - `dim_scenario[scenario_display_name]`
- scenario slicer contract:
  - single-select only
  - selection required
  - default to canonical exported scenario
  - every rendered page must contain exactly one active `scenario_key`
- metadata strip contract:
  - visual type: multi-row card
  - one visible value per field only
  - display order:
    - `Scenario` -> `dim_scenario[scenario_display_name]`
    - `Scoring model version` -> `dim_scenario[model_version]`
    - `Selection policy version` -> `dim_scenario[policy_version]`
    - `Optimization timestamp` -> `[Latest Optimization At]`
  - `dim_scenario[scenario_key]` stays in tooltip or technical-details area, not main reader-facing strip
  - if any value is not singular under current filters, display blank and fail validation
- visual interaction contract:
  - slicers drive filtering
  - chart clicks do not cross-filter or cross-highlight other visuals
  - page-local slicers may override report-wide slicers only by narrowing scope, never by changing interaction rules
- all page subtitles or intro text must include:
  - `historical`
  - `prototype`
  - `limited review slots`
  - no causal-effect claim

### Page 1: What Happened

- page title: `What Happened`
- page purpose: explain historical slice before ML score or review choice
- page-local slicers: none
- intro text:
  - `This page shows what happened in selected historical slice.`
  - `It does not show actions taken or value created.`
  - `It shows event volume, severe outcomes, and review-capacity context.`

| Visual Title | Visual Type | Fields / Measures | Visual-Level Filters | Purpose |
| --- | --- | --- | --- | --- |
| `Events in scope` | Card | `[Event Count]` | none | headline size of historical slice |
| `Can be reviewed` | Card | `[Reviewable Event Count]` | none | size of reviewable pool |
| `Actually became severe` | Card | `[Actual Severe Event Count]` | none | realized severe outcome count |
| `Review slots available` | Card | `[Review Slots]` | none | total available network-wide review capacity in filter |
| `Events by hour of day` | Line and clustered column chart | axis `dim_date_hour[hour_label]`; column `[Event Count]`; line `[Actual Severe Event Count]` | none | show overall pressure and severe outcomes by hour |
| `Events by date and hour` | Matrix with conditional formatting | rows `dim_date_hour[date_label]`; columns `dim_date_hour[hour_label]`; values `[Event Count]` | none | show when event volume clustered in time |
| `Severe outcomes by train type` | Clustered bar chart | axis `dim_train_service[train_type]`; values `[Actual Severe Event Count]` | none | show which train types carried more severe outcomes |
| `Events by station` | Clustered bar chart | axis `dim_station[station_name]`; values `[Event Count]` | top N 10 by `[Event Count]` descending | show where event volume was concentrated |

### Page 2: Which Events Look Risky

- page title: `Which Events Look Risky`
- page purpose: explain ML step in plain language before showing chosen review set
- page-local slicers:
  - `dim_train_service[train_type]`
  - `dim_train_service[service_class]`
  - `fact_event_decision[Review Eligibility]`
- intro text:
  - `This page shows model scores, not final review choices.`
  - `Higher score means event looked more likely to become severe in historical replay.`

| Visual Title | Visual Type | Fields / Measures | Visual-Level Filters | Purpose |
| --- | --- | --- | --- | --- |
| `Average predicted risk among reviewable events` | Card | `[Average Reviewable Predicted Risk]` | none | summarize model score level inside reviewable pool |
| `Can be reviewed` | Card | `[Reviewable Event Count]` | none | show candidate pool size for decision step |
| `Share of reviewable events that became severe` | Card | `[Reviewable Severe Share]` | none | show base severe rate inside reviewable pool |
| `Not reviewable` | Card | `[Not Reviewable Event Count]` | none | show events excluded from review queue |
| `Predicted risk by hour of day` | Line chart | axis `dim_date_hour[hour_label]`; values `[Average Reviewable Predicted Risk]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | show when reviewable events looked riskier |
| `Predicted risk distribution` | Clustered column chart | axis `fact_event_decision[Predicted Risk Band]`; values `[Event Count]`; legend `fact_event_decision[Review Eligibility]` | none | show how much of slice falls into each risk band |
| `Average predicted risk by train type` | Clustered bar chart | axis `dim_train_service[train_type]`; values `[Average Reviewable Predicted Risk]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | show which train types looked riskier inside reviewable pool |
| `Highest-risk reviewable events in this filter` | Table | `dim_date_hour[calendar_date]`, `dim_date_hour[hour_of_day]`, `dim_station[station_name]`, `dim_train_service[train_type]`, `dim_train_service[line_number]`, `fact_event_decision[predicted_severe_delay_probability]`, `fact_event_decision[Actual Outcome]`, `[Reviewable Risk Rank In Current Filter]` | `fact_event_decision[is_eligible_candidate] = TRUE()`; `[Reviewable Risk Rank In Current Filter] <= 20`; sort by `[Reviewable Risk Rank In Current Filter]` ascending then `fact_event_decision[stop_event_key]` ascending | show concrete high-risk reviewable events user would inspect next |

### Page 3: Which Events Were Chosen For Review

- page title: `Which Events Were Chosen For Review`
- page purpose: explain limited-slot selection after risk scoring
- page-local slicers:
  - `dim_station[station_name]`
  - `dim_train_service[train_type]`
- page-local interaction exception:
  - station and train slicers affect event-level visuals only
  - station and train slicers do not affect `[Review Slots]`, `[Unused Review Slots]`, or `Review slots used by hour of day`
- intro text:
  - `This page shows which reviewable events were chosen when review slots were limited.`
  - `It describes historical selection only.`
  - `It does not prove delays were prevented.`

| Visual Title | Visual Type | Fields / Measures | Visual-Level Filters | Purpose |
| --- | --- | --- | --- | --- |
| `Chosen for review` | Card | `[Chosen Event Count]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | headline chosen review volume |
| `Unfilled review slots` | Card | `[Unused Review Slots]` | none | show network-wide review slots left unused in selected historical horizons |
| `Share of chosen events that became severe` | Card | `[Chosen Severe Share]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | show severe-hit rate of chosen set |
| `Share of severe reviewable events captured` | Card | `[Chosen Severe Capture]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | show how much severe reviewable outcome was covered |
| `Chosen vs not chosen for review` | Donut chart | legend `fact_event_decision[Review Decision]`; values `[Event Count]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | show split inside reviewable pool |
| `Chosen events by predicted risk band` | Clustered column chart | axis `fact_event_decision[Predicted Risk Band]`; values `[Event Count]`; legend `fact_event_decision[Review Decision]` | `fact_event_decision[is_eligible_candidate] = TRUE()` | show where chosen events came from across score bands |
| `How many review slots were used by hour` | Line and clustered column chart | axis `dim_date_hour[hour_label]`; column `[Chosen Event Count]`; line `[Review Slots]` | none | compare chosen events with network-wide slots by hour |
| `Chosen review queue within each historical horizon` | Table | `dim_date_hour[calendar_date]`, `dim_date_hour[hour_of_day]`, `fact_event_decision[selection_rank]`, `dim_station[station_name]`, `dim_train_service[train_type]`, `dim_train_service[line_number]`, `fact_event_decision[predicted_severe_delay_probability]`, `fact_event_decision[Actual Outcome]`, `fact_event_decision[priority_score]` | `fact_event_decision[selected_for_review] = TRUE()`; sort by `dim_date_hour[calendar_date]` ascending, `dim_date_hour[hour_of_day]` ascending, `fact_event_decision[selection_rank]` ascending, `fact_event_decision[stop_event_key]` ascending | show selected queue within each historical date-hour horizon |

## Measure Contract

### Helper semantic fields

Create these report helper columns on `fact_event_decision`.

```DAX
Review Eligibility =
IF (
    fact_event_decision[is_eligible_candidate],
    "Can be reviewed",
    "Not reviewable"
)

Review Decision =
SWITCH (
    TRUE (),
    NOT fact_event_decision[is_eligible_candidate], "Not reviewable",
    fact_event_decision[selected_for_review], "Chosen for review",
    "Not chosen for review"
)

Actual Outcome =
SWITCH (
    TRUE (),
    ISBLANK ( fact_event_decision[actual_is_departure_severe_delay] ), "Outcome unavailable",
    fact_event_decision[actual_is_departure_severe_delay], "Became severe",
    "Did not become severe"
)

Predicted Risk Band =
VAR p = fact_event_decision[predicted_severe_delay_probability]
RETURN
SWITCH (
    TRUE (),
    ISBLANK ( p ), "Unknown",
    p < 0.10, "00-10%",
    p < 0.20, "10-20%",
    p < 0.30, "20-30%",
    p < 0.40, "30-40%",
    p < 0.50, "40-50%",
    p < 0.60, "50-60%",
    p < 0.70, "60-70%",
    p < 0.80, "70-80%",
    p < 0.90, "80-90%",
    "90-100%"
)

Predicted Risk Band Sort =
VAR p = fact_event_decision[predicted_severe_delay_probability]
RETURN
IF (
    ISBLANK ( p ),
    99,
    MIN ( 10, INT ( p * 10 ) + 1 )
)
```

Set `fact_event_decision[Predicted Risk Band]` to sort by `fact_event_decision[Predicted Risk Band Sort]`.

### Canonical measures

Create visible report measures with these exact names.

```DAX
Event Count =
COUNTROWS ( fact_event_decision )

Reviewable Event Count =
CALCULATE (
    [Event Count],
    fact_event_decision[is_eligible_candidate] = TRUE ()
)

Not Reviewable Event Count =
[Event Count] - [Reviewable Event Count]

Chosen Event Count =
CALCULATE (
    [Event Count],
    fact_event_decision[selected_for_review] = TRUE ()
)

Actual Severe Event Count =
CALCULATE (
    [Event Count],
    fact_event_decision[actual_is_departure_severe_delay] = TRUE ()
)

Reviewable Severe Event Count =
CALCULATE (
    [Event Count],
    fact_event_decision[is_eligible_candidate] = TRUE (),
    fact_event_decision[actual_is_departure_severe_delay] = TRUE ()
)

Chosen Severe Event Count =
CALCULATE (
    [Event Count],
    fact_event_decision[selected_for_review] = TRUE (),
    fact_event_decision[actual_is_departure_severe_delay] = TRUE ()
)

Average Predicted Risk =
AVERAGE ( fact_event_decision[predicted_severe_delay_probability] )

Average Reviewable Predicted Risk =
CALCULATE (
    [Average Predicted Risk],
    fact_event_decision[is_eligible_candidate] = TRUE ()
)

Review Slots =
SUM ( fact_horizon_summary[selected_event_count] ) +
SUM ( fact_horizon_summary[unused_capacity] )

Unused Review Slots =
SUM ( fact_horizon_summary[unused_capacity] )

Capacity Utilization =
DIVIDE ( [Chosen Event Count], [Review Slots] )

Reviewable Share =
DIVIDE ( [Reviewable Event Count], [Event Count] )

Chosen Share Of Reviewable =
DIVIDE ( [Chosen Event Count], [Reviewable Event Count] )

Reviewable Severe Share =
DIVIDE ( [Reviewable Severe Event Count], [Reviewable Event Count] )

Chosen Severe Share =
DIVIDE ( [Chosen Severe Event Count], [Chosen Event Count] )

Chosen Severe Capture =
DIVIDE ( [Chosen Severe Event Count], [Reviewable Severe Event Count] )

Chosen Lift Vs Reviewable Base =
DIVIDE ( [Chosen Severe Share], [Reviewable Severe Share] )

Latest Optimization At =
MAX ( fact_event_decision[optimized_at] )

Reviewable Risk Rank In Current Filter =
VAR CurrentProbability = MAX ( fact_event_decision[predicted_severe_delay_probability] )
RETURN
IF (
    MAX ( fact_event_decision[is_eligible_candidate] ) <> TRUE (),
    BLANK (),
    RANKX (
        FILTER (
            ALLSELECTED ( fact_event_decision[stop_event_key] ),
            CALCULATE ( MAX ( fact_event_decision[is_eligible_candidate] ) ) = TRUE ()
        ),
        CALCULATE ( MAX ( fact_event_decision[predicted_severe_delay_probability] ) ),
        CurrentProbability,
        DESC,
        DENSE
    )
)
```

### Measure formatting

- format as whole number:
  - `[Event Count]`
  - `[Reviewable Event Count]`
  - `[Not Reviewable Event Count]`
  - `[Chosen Event Count]`
  - `[Actual Severe Event Count]`
  - `[Reviewable Severe Event Count]`
  - `[Chosen Severe Event Count]`
  - `[Review Slots]`
  - `[Unused Review Slots]`
  - `[Reviewable Risk Rank In Current Filter]`
- format as percentage with one decimal:
  - `[Average Predicted Risk]`
  - `[Average Reviewable Predicted Risk]`
  - `[Capacity Utilization]`
  - `[Reviewable Share]`
  - `[Chosen Share Of Reviewable]`
  - `[Reviewable Severe Share]`
  - `[Chosen Severe Share]`
  - `[Chosen Severe Capture]`
- format as multiplier with one decimal and `x` suffix:
  - `[Chosen Lift Vs Reviewable Base]`
- format as date-time:
  - `[Latest Optimization At]`

## Wording Guardrails

- use `Can be reviewed` instead of `Eligible`
- use `Chosen for review` instead of `Selected`
- use `Predicted risk` instead of `Probability score`
- use `Review slots` instead of `Capacity scenario` in visual titles
- use `Became severe` instead of `Actual severe delay label`
- use `Historical prototype` and `historical replay` in explanatory text
- do not say:
  - `impact`
  - `avoided delays`
  - `caused improvement`
  - `proved optimizer value`
- when mentioning ML:
  - say `model score`
  - say `predicted risk`
  - do not say `decision`
- when mentioning Gurobi:
  - say `limited-slot review choice`
  - say `chosen review queue`
  - do not say `best action` without baseline-comparison evidence
- when describing `Unused Review Slots` in report copy:
  - say `unfilled review slots in selected historical horizons`
  - do not claim station-specific slot shortage from this metric

## Invariants

- report must continue to use current six imported Power BI parquet tables only
- report may add only explicitly defined local helper columns and measures from this spec
- report must preserve portable `SemanticExportRoot` binding and current relationship topology
- report must expose exactly three visible pages in this storytelling rewrite
- page order must remain:
  - `What Happened`
  - `Which Events Look Risky`
  - `Which Events Were Chosen For Review`
- scenario context must remain single-select
- page 1 must not use chosen-review visuals as primary story
- page 2 must explain ML scoring before any chosen-review table is shown
- page 3 must explain limited-slot choice without claiming causal operational improvement
- network-wide horizon-capacity visuals must not become station-specific or train-specific through slicer interactions
- visible measures must have one canonical definition each
- imported ratio columns must remain hidden from final visible field list
- metadata strip must remain visible on all pages
- report must stay truthful under date, hour, station, and train-type filters according to the interaction rules in this spec

## Validation Plan

- proof target: new story is implementable from current semantic export only
  - method: inspection
  - evidence: every page visual and every measure in this spec binds only to current six imported parquet tables and helper semantic fields defined here

- proof target: scenario context is single-select
  - method: inspection and run
  - evidence: scenario slicer is single-select, required, defaults to canonical scenario, and every rendered page shows exactly one active `scenario_key`

- proof target: page order tells pre-decision then decision story
  - method: inspection
  - evidence: rendered report contains exactly three visible pages in required order and page 1/page 2 contain no chosen-review queue visual or chosen-vs-not-chosen visual

- proof target: plain-language wording is consistent
  - method: inspection
  - evidence: titles, slicers, cards, and intro text use required wording guardrails and avoid banned claims

- proof target: visible counts reconcile to current facts
  - method: comparison
  - evidence: selected checkpoints in `validation.md` show `[Event Count]`, `[Reviewable Event Count]`, `[Chosen Event Count]`, `[Actual Severe Event Count]`, `[Review Slots]`, and `[Unused Review Slots]` match source facts under allowed filter behavior

- proof target: station and train slicers do not corrupt network-capacity visuals
  - method: run and comparison
  - evidence: under one-station and one-train filters, `[Review Slots]`, `[Unused Review Slots]`, and `How many review slots were used by hour` remain unchanged while event-level visuals narrow correctly

- proof target: visible ratio measures are filter-aware
  - method: comparison
  - evidence: selected checkpoints in `validation.md` show `[Reviewable Severe Share]`, `[Chosen Severe Share]`, `[Chosen Severe Capture]`, and `[Chosen Lift Vs Reviewable Base]` recompute correctly under at least global, one-date, and one-station filters

- proof target: predicted risk bands sort correctly
  - method: inspection and run
  - evidence: risk-band visuals render left-to-right from `00-10%` through `90-100%` with `Unknown` last if present

- proof target: top-risk table is deterministic
  - method: inspection and run
  - evidence: `Highest-risk reviewable events in this filter` uses `[Reviewable Risk Rank In Current Filter] <= 20`, excludes non-reviewable events, and sorts deterministically by rank then `stop_event_key`

- proof target: chosen queue ordering is truthful
  - method: inspection and run
  - evidence: chosen queue sorts by date, hour, selection rank, and `stop_event_key`, and is labeled as queue within each historical horizon rather than global queue

- proof target: metadata strip remains truthful
  - method: comparison
  - evidence: displayed `scenario_display_name`, `model_version`, `policy_version`, and `[Latest Optimization At]` match filtered source rows and remain singular under current filter context

- proof target: missing outcomes do not become observed negatives
  - method: run and inspection
  - evidence: rows with blank `actual_is_departure_severe_delay` display `Outcome unavailable`, and denominator behavior remains explicit through `DIVIDE`-based measures

- proof target: deferred optimizer-vs-baseline claim remains absent
  - method: inspection
  - evidence: report contains no page or annotation claiming Gurobi beat random, ML-first, or constrained-greedy policies inside current six-table export

## Acceptance Criteria

- one new storytelling spec exists under `docs/superpowers/specs/` for current Power BI report rewrite
- spec defines exact visible page count, page names, page order, and page purpose
- spec defines exact visual title, visual type, field binding, and filter rule for each page visual
- spec defines exact helper columns and exact DAX measures with stable names
- spec defines single-select scenario behavior and exact visual interaction rules for horizon-capacity visuals
- spec defines plain-language wording rules that separate ML scoring from limited-slot review choice
- spec defines clear deferral boundary for optimizer-vs-baseline proof page until semantic export expands

## Non-Goals

- importing `policy_comparison.parquet` or `horizon_policy_metrics.parquet` into current report in this spec
- proving Gurobi beats baselines inside current report version
- changing upstream Bronze, Silver, Gold, ML, optimization, or Power BI semantic-export contracts
- redesigning PBIP portability, refresh workflow, or report relationship topology
- adding Power BI service deployment, row-level security, or enterprise sharing flows
- making live operational claims from historical replay

## Risks and Mitigations

- risk: user may still assume chosen queue proves optimizer value
  - mitigation: keep comparison claims out of current report and defer them explicitly to later semantic-export expansion

- risk: too many visuals may reintroduce clutter
  - mitigation: keep exact three-page sequence and limit each page to one intro area, four cards, and four chart/table visuals

- risk: ratio measures may diverge from visible counts under filters
  - mitigation: define visible ratios from canonical count measures only and validate global plus filtered checkpoints

- risk: station or train filters may be misread as local slot capacity views
  - mitigation: freeze interaction rules so network-capacity visuals ignore station and train slicers and label those visuals as network-wide

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
