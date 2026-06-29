# Validation

## Refresh Validation

- Status: `partial`
- Current state: PBIP source, semantic model source, and report source exist and were updated in repo.
- Remaining manual step: open `reports/power_bi/historical_evaluation/historical_evaluation.pbip` in Power BI Desktop, refresh from the current `SemanticExportRoot`, save, and verify rendered-page behavior.
- Required app: `C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe`
- Power BI Desktop version observed on this machine: `2.155.756.0 (26.06)+7f1da5803bfe48beff98093405280405ddb467dd`
- Canonical entry file: `reports/power_bi/historical_evaluation/historical_evaluation.pbip`
- Root parameter: `SemanticExportRoot`
- Current parameter value: `C:\Users\HOANG PHI LONG DANG\repos\deutsche-bahn\data\scoped\power_bi`
- Second-root refresh check: `pending manual Desktop verification`

## Artifact-Level Validation

### Current Execution Snapshot

- Validation timestamp: `2026-06-29`
- Report commit: `2f25f032e71596b4716485ece910aab496da0870`
- Operating system: `Microsoft Windows`
- Report artifact present: `yes`
- PBIP source updated in repo: `yes`
- PBIX file present: `yes`

### Imported Source Surface

- Imported parquet tables: `6`
- Imported tables:
  - `dim_date_hour.parquet`
  - `dim_scenario.parquet`
  - `dim_station.parquet`
  - `dim_train_service.parquet`
  - `fact_event_decision.parquet`
  - `fact_horizon_summary.parquet`
- Authoring-only JSON contracts present and not imported as runtime tables:
  - `semantic_contract.json`
  - `dashboard_mvp_manifest.json`
- Parameterized data binding confirmed in `expressions.tmdl`: `yes`
- Hidden absolute path outside parameter value: `not detected in TMDL source`

### Current Page Source State

- Visible page count in PBIR source: `3`
- Visible pages in order:
  1. `What Happened`
  2. `Which Events Look Risky`
  3. `Which Events Were Chosen For Review`
- Global visual cross-filter flag patched to `false` in PBIR visual source: `yes`
- Scenario slicers now bind to `scenario_display_name` in PBIR source: `yes`
- Page 2 source now uses pre-decision labels for risk distribution and review-eligibility visuals: `yes`
- Page 3 source now uses chosen-review labels and distinct queue-table binding: `yes`
- Rendered Desktop confirmation of final interactions: `pending`

### Relationship Topology

- Relationship count: `6`
- Active relationships:
  - `fact_event_decision[horizon_id] -> dim_date_hour[horizon_id]` (`ManyToOne`, `OneDirection`)
  - `fact_horizon_summary[horizon_id] -> dim_date_hour[horizon_id]` (`ManyToOne`, `OneDirection`)
  - `fact_event_decision[scenario_key] -> dim_scenario[scenario_key]` (`ManyToOne`, `OneDirection`)
  - `fact_horizon_summary[scenario_key] -> dim_scenario[scenario_key]` (`ManyToOne`, `OneDirection`)
  - `fact_event_decision[station_id] -> dim_station[station_id]` (`ManyToOne`, `OneDirection`)
  - `fact_event_decision[train_service_key] -> dim_train_service[train_service_key]` (`ManyToOne`, `OneDirection`)
- Dimension uniqueness violations:
  - `dim_date_hour[horizon_id]`: `0`
  - `dim_scenario[scenario_key]`: `0`
  - `dim_station[station_id]`: `0`
  - `dim_train_service[train_service_key]`: `0`
- Orphan-key checks:
  - event -> station: `0`
  - event -> train service: `0`
  - event -> horizon: `0`
  - event -> scenario: `0`
  - horizon -> date_hour: `0`
  - horizon -> scenario: `0`

### Current Semantic-Model Additions

- New helper columns added on `fact_event_decision`:
  - `Review Eligibility`
  - `Review Decision`
  - `Actual Outcome`
  - `Predicted Risk Band`
  - `Predicted Risk Band Sort`
- New or updated measures added:
  - `Reviewable Event Count`
  - `Not Reviewable Event Count`
  - `Chosen Event Count`
  - `Reviewable Severe Event Count`
  - `Chosen Severe Event Count`
  - `Average Predicted Risk`
  - `Average Reviewable Predicted Risk`
  - `Scenario Selection Valid`
  - `Latest Optimization At`
  - `Reviewable Share`
  - `Chosen Share Of Reviewable`
  - `Reviewable Severe Share`
  - `Chosen Severe Share`
  - `Chosen Severe Capture`
  - `Chosen Lift Vs Reviewable Base`
  - `Reviewable Risk Rank In Current Filter`
  - `Review Slots`
  - `Unused Review Slots`
- Existing display measures updated for singular scenario state:
  - `Scenario Key Display`
  - `Scenario Name Display`
  - `Model Version Display`
  - `Policy Version Display`
  - `Optimized At Display`

## Independent Source Validation

All values in this section come from parquet-side checks, not Power BI visuals.

### Source Completeness Snapshot

| Table | Row count |
| --- | ---: |
| `fact_event_decision` | 743 |
| `fact_horizon_summary` | 137 |
| `dim_date_hour` | 137 |
| `dim_station` | 41 |
| `dim_train_service` | 108 |
| `dim_scenario` | 1 |

### Canonical Scenario State

| Check | Value |
| --- | --- |
| distinct `scenario_key` in `dim_scenario` | `1` |
| canonical scenario fail-safe expectation | exactly one active scenario required |
| invalid scenario render handling | pending Desktop verification |

### Event and Review Identities

| Check | Source value | Result |
| --- | ---: | --- |
| `Event Count` | 743 | Pass |
| `Reviewable Event Count` | 60 | Pass |
| `Not Reviewable Event Count` | 683 | Pass |
| `Chosen Event Count` | 60 | Pass |
| `Actual Severe Event Count` | 119 | Pass |
| `Reviewable Severe Event Count` | 49 | Pass |
| `Chosen Severe Event Count` | 49 | Pass |
| `Event Count = Reviewable + Not Reviewable` | `743 = 60 + 683` | Pass |
| `Reviewable Event Count = Chosen + Reviewable Not Chosen` | `60 = 60 + 0` | Pass |
| `Chosen Severe Event Count <= Chosen Event Count` | `49 <= 60` | Pass |
| `Chosen Severe Event Count <= Reviewable Severe Event Count` | `49 <= 49` | Pass |
| missing actual outcomes | 0 | Pass |

### Horizon and Capacity Identities

| Check | Source value | Result |
| --- | ---: | --- |
| total review slots | 411 | Pass |
| total unfilled review slots | 351 | Pass |
| horizons violating `capacity_per_hour = selected_event_count + unused_capacity` | 0 | Pass |
| frozen wording for `unused_capacity` | review slots that could not be filled | Pass |

### Ranking Checks

| Check | Source value | Result |
| --- | ---: | --- |
| Top 20 reviewable rows available | 20 | Pass |
| most-selected `train_service_key` sample | `216` with `6` selected rows | Informational |
| sample station for filter check | `Aschaffenburg Hbf` | Informational |

## Pending Desktop Render Validation

The following still require opening the PBIP in Power BI Desktop and checking the rendered report, not only source files.

| Check name | Expected behavior | Status |
| --- | --- | --- |
| Original-root refresh | All 6 parquet tables refresh successfully from current `SemanticExportRoot` | Pending |
| Second-root refresh | Changing only `SemanticExportRoot` refreshes successfully | Pending |
| Scenario slicer UI state | single-select, required, canonical default, no invalid state exposed to user | Pending |
| Metadata strip | reader-facing values only, singular under allowed filters | Pending |
| Page 1 story | no chosen-review visual remains visible | Pending |
| Page 2 Top 20 table | deterministic rendered order, reviewable-only scope, exact row count when available | Pending |
| Page 3 capacity scope | station/train filters do not alter network-capacity visuals | Pending |
| Rendered interaction matrix | slicers behave as planned, visuals do not cross-filter unexpectedly | Pending |
| Final visual titles and wording | plain-language labels with no causal claims | Pending |

## Open Issues

- Blocking for full closeout: Power BI Desktop refresh and rendered-page verification have not been run after the latest PBIP source changes.
- Blocking for full closeout: source-level page rewiring is in place, but Desktop-side visual review is still required against the exact storytelling spec.
- Non-blocking: source-level interaction flag patch is in place, but rendered behavior still needs confirmation in Desktop.
