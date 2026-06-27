---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: gold-feature-layer
parent_thread: deutsche-bahn-decision-dashboard.gold-feature-layer
targets:
  - sql/duckdb/gold/
  - data/scoped/local_scope_bronze.duckdb
  - data/scoped/silver_validation_summary.json
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-gold-feature-layer.md
related_features: []
related_stages: []
---

## Goal

Define the exact Gold feature layer built from the validated local Silver Deutsche Bahn slice so the project has one event-level feature table and one station-hour aggregate table ready for downstream ML, optimization, and Power BI work.

## Key Deliverables

### Concrete Gold table contract

Define the exact Gold outputs for the scoped local slice: `gold.feature_stop_event` and `gold.fact_station_hour`, including grain, key strategy, required columns, and ownership boundaries relative to Silver.

### Bounded feature-engineering ownership

Define the feature logic Gold owns for delay flags, delay buckets, cancellation rollups, calendar slices, and station-hour aggregates so later layers inherit one consistent analytical contract instead of rebuilding features ad hoc.

### Silver-to-Gold validation boundary

Define the exact validation checks that prove Gold preserves Silver event coverage where required, aggregates station-hour facts deterministically, and hands off cleanly to later ML, optimization, and dashboard threads without leaking their logic into Gold.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- define current behavior, boundaries, and design constraints before proposing decisions

**Steps:**
- [ ] inspect current source-of-truth surfaces
- [ ] identify unresolved contract edges
- [ ] record affected invariants, interfaces, and dependency boundaries

**Verification:**
- [ ] current-state understanding is explicit enough to support concrete design decisions

**Exit Criteria:**
- no core design decision depends on unstated assumptions

### Wave 2: Decision closure

**Purpose:**
- resolve design choices and document why chosen shape is preferred

**Steps:**
- [ ] define major design decisions
- [ ] compare alternatives where non-obvious
- [ ] record impact on interfaces, invariants, and downstream implementation

**Verification:**
- [ ] each major design question has a documented decision or explicit deferral

**Exit Criteria:**
- design is internally coherent and bounded

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare the spec for implementation handoff by making proof expectations explicit

**Steps:**
- [ ] define validation plan
- [ ] confirm invariant preservation strategy
- [ ] identify any open approval questions or follow-up notes

**Verification:**
- [ ] validation plan proves intended behavior and contract preservation

**Exit Criteria:**
- spec is ready for approval or implementation planning

## Design Decisions

### Decision: Gold table set is fixed to one event-level feature table plus one station-hour aggregate

- context: scoped local MVP needs one reusable feature surface for detailed analytics and one bounded aggregate for dashboard and forecasting starts
- choice: implement exactly `gold.feature_stop_event` and `gold.fact_station_hour`
- alternatives considered:
  - one Gold aggregate table only
  - many Gold tables for route, destination, and journey now
  - skipping Gold and pushing all feature work into Power BI or notebooks
- impact:
  - Gold stays small and reusable
  - downstream consumers share one feature contract
  - implementation avoids speculative table sprawl

### Decision: `gold.feature_stop_event` grain stays one row per `silver.fact_stop_event`

- context: Silver already preserves one row per scoped Bronze stop event and carries normalized operational fields
- choice: Gold keeps one row per Silver stop event and adds deterministic analytical features without collapsing event coverage
- alternatives considered:
  - aggregate directly to station-hour only
  - collapse by journey and stop sequence
  - build rolling features now
- impact:
  - event-level ML and root-cause analysis remain possible
  - validation can compare row counts directly against Silver
  - station-hour aggregate can be derived deterministically

### Decision: `gold.feature_stop_event` owns only first-pass deterministic features

- context: local MVP needs stable analytical columns, not model-specific or optimization-specific features yet
- choice: `gold.feature_stop_event` includes:
  - passthrough keys and identifiers:
    - `stop_event_key`
    - `date_key`
    - `hour_key`
    - `station_key`
    - `train_service_key`
    - `service_date`
    - `journey_id`
    - `stop_sequence`
  - dimensional descriptors joined from Silver:
    - `station_id`
    - `station_name`
    - `train_type`
    - `train_number`
    - `line_number`
    - `service_class`
    - `calendar_date`
    - `year`
    - `month`
    - `week_of_year`
    - `day_of_week`
    - `day_name`
    - `is_weekend`
    - `hour_of_day`
    - `time_band`
  - operational passthrough measures:
    - `provider_delay_in_min`
    - `arrival_delay_min`
    - `departure_delay_min`
    - `delay_change_min`
    - `is_cancellation`
    - `is_arrival_cancelled`
    - `is_departure_cancelled`
  - deterministic Gold features:
    - `event_delay_min` = `coalesce(departure_delay_min, arrival_delay_min, provider_delay_in_min)`
    - `has_delay_measurement` = `event_delay_min is not null`
    - `is_delayed` = `event_delay_min > 0`
    - `is_heavy_delay` = `event_delay_min >= 15`
    - `is_extreme_delay` = `event_delay_min >= 30`
    - `is_departure_severe_delay` = `departure_delay_min >= 15`
    - `delay_bucket` with values:
      - `unknown` when `event_delay_min` is null
      - `early_or_on_time` when `event_delay_min <= 0`
      - `minor` when `event_delay_min between 1 and 5`
      - `medium` when `event_delay_min between 6 and 14`
      - `heavy` when `event_delay_min between 15 and 29`
      - `extreme` when `event_delay_min >= 30`
    - `is_active_stop` = `not is_cancellation`
    - `has_arrival_time_data` = `planned_arrival_ts is not null or actual_arrival_ts is not null`
    - `has_departure_time_data` = `planned_departure_ts is not null or actual_departure_ts is not null`
- alternatives considered:
  - no Gold feature flags or buckets
  - model-target labels now
  - rolling and lagged features now
- impact:
  - downstream dashboard and ML baseline work get ready-to-use flags and segments
  - feature logic stays reproducible from Silver only
  - later threads can add richer temporal features without breaking first-pass contract

### Decision: `event_delay_min` uses departure-first fallback

- context: some stop events have departure, arrival, or provider delay values missing independently
- choice: derive `event_delay_min` as `coalesce(departure_delay_min, arrival_delay_min, provider_delay_in_min)`
- alternatives considered:
  - arrival-first fallback
  - provider delay only
  - average of arrival and departure delays
- impact:
  - each stop gets one primary delay measure when available
  - departure-side operational impact is prioritized at station-level decision points
  - null-handling stays deterministic and cheap

### Decision: ML-facing severe-delay label stays departure-only

- context: fallback-based `event_delay_min` is useful for reporting but mixes departure, arrival, and provider semantics
- choice: expose `is_departure_severe_delay` from `departure_delay_min >= 15` and keep it separate from fallback-based delay flags
- alternatives considered:
  - infer ML-ready severe delay from `event_delay_min`
  - omit explicit departure-based label entirely
- impact:
  - downstream ML work gets one clean departure-based target candidate
  - reporting convenience does not silently become training-label semantics

### Decision: `gold.fact_station_hour` grain is one row per `station_key + date_key + hour_key`

- context: first dashboard and forecasting starts need bounded operational aggregation without service-class explosion
- choice: `gold.fact_station_hour` groups `gold.feature_stop_event` by `station_key`, `date_key`, and `hour_key`
- alternatives considered:
  - aggregate by station-date only
  - aggregate by station-hour-service-class
  - aggregate by journey-hour
- impact:
  - Power BI can start with one stable operational fact
  - later threads may add segmented aggregates without rewriting Gold base contract
  - local compute stays small

### Decision: `gold.fact_station_hour` includes deterministic operational aggregate measures only

- context: Gold aggregate should support first dashboard and future forecasting starts without mixing in optimization outputs
- choice: `gold.fact_station_hour` includes:
  - grain keys and descriptors:
    - `station_key`
    - `date_key`
    - `hour_key`
    - `station_id`
    - `station_name`
    - `calendar_date`
    - `year`
    - `month`
    - `week_of_year`
    - `day_of_week`
    - `day_name`
    - `is_weekend`
    - `hour_of_day`
    - `time_band`
  - aggregate counts:
    - `stop_event_count`
    - `measured_delay_event_count`
    - `delayed_event_count`
    - `heavy_delay_event_count`
    - `extreme_delay_event_count`
    - `cancellation_event_count`
    - `arrival_time_data_count`
    - `departure_time_data_count`
  - aggregate rates and measures:
    - `avg_event_delay_min`
    - `max_event_delay_min`
    - `pct_delayed`
    - `pct_cancellation`
    - `pct_heavy_delay`
- alternatives considered:
  - sum-only aggregate table
  - dashboard measures only in Power BI
  - service-class split in first pass
- impact:
  - dashboard and exploratory notebooks can use one curated aggregate fact
  - ML forecasting starts have ready hourly targets
  - aggregate remains deterministic from event-level Gold

### Decision: Gold excludes rolling windows, labels, predictions, and optimization outputs

- context: Gold should be analytical feature layer, not mixed feature store plus ML plus decision engine
- choice: Gold must not include:
  - rolling 3/6/24-hour features
  - lag features across prior stations or prior hours
  - severe-delay training labels beyond fixed flags and buckets above
  - prediction scores
  - recommended actions
  - optimizer candidate sets or chosen allocations
- alternatives considered:
  - add forecasting labels now
  - add optimization candidate features now
  - merge Gold with ML prep layer
- impact:
  - layer ownership stays clean
  - next threads can focus on ML and optimization with stable upstream inputs

## Acceptance Criteria

- `gold.feature_stop_event` and `gold.fact_station_hour` are explicitly defined
- `gold.feature_stop_event` grain remains one row per `silver.fact_stop_event`
- `gold.fact_station_hour` grain remains one row per `station_key + date_key + hour_key`
- `event_delay_min`, delay flags, and delay buckets use explicit deterministic rules
- Gold feature and aggregate tables can be derived from validated Silver tables only
- Gold excludes ML labels, prediction scores, optimizer outputs, and Power BI-only semantics
- Silver-to-Gold validation checks are explicit
- handoff to ML, optimization, and dashboard threads is explicit

## Non-Goals

- modify Bronze extraction logic
- redesign Silver operational tables
- build ML training datasets or splits
- train, score, or evaluate models
- define Gurobi candidate generation or optimization objective contracts
- define Power BI semantic model, DAX measures, or visuals
- define BigQuery parity or cloud runtime

## Invariants

- Gold must not drop Silver stop-event rows without explicit documented rule
- `gold.feature_stop_event` must remain one row per Silver stop event
- `gold.fact_station_hour` must be reproducible from `gold.feature_stop_event` only
- all Gold feature logic must be deterministic and reproducible from Silver
- Gold must not mutate Silver source-of-truth fields in place
- Gold must own analytical feature engineering only, not ML scoring or optimization decisions

## Risks and Mitigations

### Risk: Delay bucket thresholds may not match later business expectations

- mitigation:
  - keep threshold logic explicit in Gold
  - use simple 5/15/30 minute boundaries now
  - revisit in later ML or dashboard threads only when real consumer need appears

### Risk: Departure-first delay fallback may bias some arrival-heavy use cases

- mitigation:
  - preserve `arrival_delay_min`, `departure_delay_min`, and `provider_delay_in_min` alongside `event_delay_min`
  - let later consumers choose alternate measures when needed

### Risk: Station-hour aggregate may be too coarse for service-specific dashboards

- mitigation:
  - keep station-hour base fact narrow now
  - defer segmented aggregate tables until real dashboard or forecasting demand proves need

### Risk: Null-heavy delay data may weaken rates and averages

- mitigation:
  - expose `measured_delay_event_count`
  - compute percentages from explicit counts
  - preserve `unknown` bucket instead of forcing imputation

## Validation Plan

- proof target: Gold event table preserves Silver stop-event coverage
  - method: comparison
  - evidence: `count(*)` of `gold.feature_stop_event` matches `silver.fact_stop_event` for current scoped slice

- proof target: Gold aggregate table preserves station-hour grouping deterministically
  - method: comparison
  - evidence: `count(*)` of `gold.fact_station_hour` matches distinct `station_key, date_key, hour_key` combinations from `gold.feature_stop_event`

- proof target: Gold feature logic follows explicit deterministic rules
  - method: inspection and sample comparison
  - evidence: sampled rows show `event_delay_min`, flags, and buckets derived only from Silver columns using documented fallback rules

- proof target: Gold aggregate measures are reproducible from event-level Gold
  - method: comparison
  - evidence: sampled grouped recomputation from `gold.feature_stop_event` matches stored `gold.fact_station_hour` counts, averages, and rates

- proof target: Gold handoff stays bounded
  - method: inspection
  - evidence: Gold schema contains no prediction scores, optimization outputs, or dashboard-only semantic fields

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
