---
layer: change
artifact_type: spec
status: proposed
template_id: detailed-specification
name: optimization-value-add-redesign
parent_thread: deutsche-bahn-decision-dashboard.optimization-value-add-redesign
targets:
  - scripts/run_optimization_prototype.py
  - tests/test_run_optimization_prototype.py
  - configs/optimization/
  - data/scoped/optimization/
  - data/scoped/power_bi/
  - docs/intent/workstreams/threads/deutsche-bahn-decision-dashboard/thread-optimization-value-add-redesign.md
related_features: []
related_stages: []
---

## Goal

Define exact redesign of local Deutsche Bahn optimization layer so Gurobi solves real bounded operational trade-off beyond pure ML ranking, produces reproducible baseline and capacity comparisons, and hands downstream dashboard work one action-oriented policy story before any BigQuery migration begins.

## Key Deliverables

### Redefined optimization policy contract

Define one bounded local Gurobi policy that keeps current event-level candidate grain and current hourly review capacity framing, but replaces ranking-equivalent selection with soft station-concentration trade-off while preserving current ML split discipline and current downstream join keys.

### Baseline and scenario evaluation contract

Define one exact baseline and scenario comparison bundle that measures random selection, ML-first ranking, constrained greedy selection, and Gurobi under same candidate pools, same capacities, same tie-break rules, and same final held-out evaluation boundary.

### Action-oriented downstream handoff contract

Define one exact output and wording handoff contract so downstream Power BI work can explain what ML predicts, what Gurobi decides, what simple baselines do instead, and what operator trade-offs change when review capacity changes.

## Task/Wave Breakdown

### Wave 1: Source-first analysis

**Purpose:**
- define current optimization behavior, equivalence edges, and downstream story gaps before proposing redesign decisions

**Steps:**
- [ ] inspect current optimization runner, frozen policy, evaluation artifact, and downstream Power BI handoff surfaces
- [ ] identify where current formulation is equivalent to deterministic ML-first ranking
- [ ] record affected invariants, output contracts, and downstream dashboard semantics

**Verification:**
- [ ] current-state understanding is explicit enough to support concrete redesign decisions

**Exit Criteria:**
- no core redesign decision depends on unstated assumptions

### Wave 2: Decision closure

**Purpose:**
- resolve bounded optimization, baseline, and evaluation redesign choices

**Steps:**
- [ ] define major redesign decisions for objective, constraints, baselines, scenario bundle, and downstream handoff surface
- [ ] compare alternatives where non-obvious
- [ ] record impact on scripts, tests, output artifacts, config ownership, and downstream dashboard handoff

**Verification:**
- [ ] each major redesign question has documented decision or explicit deferral

**Exit Criteria:**
- redesign is internally coherent and bounded

### Wave 3: Validation and approval readiness

**Purpose:**
- prepare spec for implementation handoff by making proof expectations explicit

**Steps:**
- [ ] define validation plan for optimization-value-add and output-contract preservation
- [ ] confirm invariant preservation strategy
- [ ] identify open approval questions or follow-up notes

**Verification:**
- [ ] validation plan proves intended behavior and contract preservation

**Exit Criteria:**
- spec is ready for implementation planning

## Design Decisions

### Decision: Keep event-level candidate grain and held-out split boundary unchanged

- context: current ML and optimization layers already hand off one scored row per   `stop_event_key`, preserve `journey_id` uniqueness constraints, and separate
  `development = validation` from `final = test`; redesign should increase
  decision value without reopening upstream contracts
- choice:
  - retain event-level candidate grain from `data/scoped/ml/scored_stop_events.parquet`
  - retain current execution-mode split rule:
    - `development` uses `prediction_split = 'validation'`
    - `final` uses `prediction_split = 'test'`
  - retain current downstream canonical outputs:
    - `event_decision.parquet` contains only frozen `gurobi_soft_station_penalty` rows at canonical capacity `3`
    - `horizon_summary.parquet` contains only frozen `gurobi_soft_station_penalty` rows at canonical capacity `3`
    - `evaluation.json` summarizes frozen canonical policy plus pairwise comparison diagnostics
  - retain comparison outputs for multi-policy and multi-capacity evaluation:
    - `horizon_policy_metrics.parquet`
    - `policy_comparison.parquet`
    - `development/opportunity_diagnostics.parquet`
    - `development/tuning_search_results.parquet`
- alternatives considered:
  - redesign at station-hour or corridor-hour aggregate grain
  - reopen ML split logic or train new model first
  - mix validation and test rows during redesign tuning
- impact:
  - optimization redesign stays source-compatible with current ML and dashboard handoff surfaces
  - held-out evaluation discipline remains intact
  - downstream report rebuild is not required to understand redesign contract

### Decision: Replace ranking-equivalent objective with soft station-concentration penalty objective

- context: current prototype maximizes only `predicted_severe_delay_probability` under hourly capacity and one-per-journey rules, which is mathematically equivalent to deterministic top-probability selection; that gives Gurobi no visible job beyond sorting
- choice:
  - define binary decision variable `x_i = 1` when event `i` is selected for review
  - define nonnegative station-hour excess variable `u_{s,h}` for preferred station load overflow
  - for each horizon `h`, define `feasible_selection_target_h` as:

    ```text
    min(
      capacity_per_hour,
      number of distinct eligible journey_id values remaining in horizon h after candidate preparation
    )
    ```

  - maximize:

    ```text
    sum(prob_i * x_i) - lambda * sum(u_s_h)
    ```

  - define station excess as:

    ```text
    u_s_h >= sum(x_i for events at station s in hour h) - preferred_station_load_per_station_hour
    u_s_h >= 0
    ```

  - compute reported station concentration metrics from selected set after optimization, not from raw solver variable values alone
  - keep service-priority weight at `1.0` for all events in this thread
- alternatives considered:
  - keep pure probability objective
  - add service weights now and claim optimization value from weighted ranking alone
  - use hard station cap as first redesign
  - allow under-filling capacity without explicit review cost
- impact:
  - Gurobi now solves real joint trade-off between risk capture and station workload concentration
  - weighted ranking remains explicitly deferred until justified business weighting source exists
  - station concentration reporting remains stable even when diagnostic `lambda = 0.00` is evaluated

### Decision: Keep hard constraints minimal, but make per-horizon selection target exact

- context: MVP should stay easy to explain and safe to validate; too many hard business rules can create infeasibility or visibly bad forced picks, but policy-driven under-filling would contradict intended constrained-review story
- choice:
  - keep only these hard constraints:
    - exact feasible selection count per horizon
    - eligibility
    - one selected event per `journey_id` within one `calendar_date + hour_of_day` horizon
    - binary selection
  - implement exact selection rule:

    ```text
    sum(x_i for events in horizon h) = feasible_selection_target_h
    ```

  - define candidate-shortage diagnostic as:

    ```text
    candidate_shortage_h = capacity_per_hour - feasible_selection_target_h
    ```

  - do not add hard station cap in this thread
  - do not add corridor minimums, fairness minimums, or unused-capacity review cost in this thread
- alternatives considered:
  - hard station cap
  - corridor minimum coverage constraints
  - review-cost objective term that permits intentional unused capacity
- impact:
  - all policies select same feasible number of events in each horizon
  - any `unused_capacity` metric now means candidate shortage only, not optimizer choice
  - concentration trade-off remains visible without frequent infeasibility or obviously weak forced picks

### Decision: Tune only preferred station load and penalty weight on validation, then freeze one final policy

- context: redesign needs sensitivity evidence and frozen final policy, but large search grid would be overkill for this project stage
- choice:
  - canonical tuning input config lives at `configs/optimization/optimization_policy_search_config.json`
  - in `development` mode at canonical capacity `3`, evaluate this bounded grid:
    - `preferred_station_load_per_station_hour in {1, 2}`
    - `diagnostic_station_excess_penalty_lambda = 0.00`
    - `eligible_frozen_station_excess_penalty_lambdas in {0.05, 0.10, 0.20}`
  - treat `lambda = 0.00` as diagnostic benchmark only, not as eligible frozen Gurobi policy
  - compare positive-penalty candidates against `lambda = 0.00` benchmark and record when they yield identical selected sets
  - select one canonical positive-penalty pair with this deterministic ordering, using metrics aggregated over all validation horizons at canonical capacity `3`:
    1. maximize `selected_severe_event_count`
    2. maximize `severe_delay_coverage`
    3. minimize `station_concentration_excess_total`
    4. maximize `distinct_stations_covered`
    5. prefer smaller positive `station_excess_penalty_lambda`
    6. prefer smaller `preferred_station_load_per_station_hour`
  - freeze chosen values in `frozen_policy.json`
  - run `final` mode only with frozen values
- alternatives considered:
  - manual policy selection from charts only
  - larger hyperparameter sweep
  - freeze arbitrary values without development comparison
- impact:
  - policy selection remains reproducible and bounded
  - validation split owns tuning while test split remains held out
  - redesign cannot silently collapse back to pure ranking in frozen final mode

### Decision: Keep canonical config in `configs/` and generated evidence in `data/scoped/optimization/`

- context: runtime configuration and generated run artifacts have different ownership; mixing them in `data/scoped/optimization/` would weaken SSOT and make reruns harder to reason about
- choice:
  - keep human-owned search config in `configs/optimization/optimization_policy_search_config.json`
  - keep generated `frozen_policy.json`, development evidence, and final evaluation artifacts under `data/scoped/optimization/`
  - keep search grid values out of generated `frozen_policy.json`
- alternatives considered:
  - store search config beside generated outputs in `data/scoped/optimization/`
  - duplicate search grid into both config and frozen policy
- impact:
  - one clear input SSOT exists for tuning configuration
  - generated artifacts remain disposable and auditable outputs

### Decision: Add constrained greedy baseline to isolate optimization value from rule value

- context: comparing only random, ML-first, and Gurobi is not enough; if Gurobi improves over ML-first, that improvement may come from station-load rule rather than optimization itself
- choice:
  - compare exactly four policies:
    - `random`
    - `ml_first`
    - `constrained_greedy`
    - `gurobi_soft_station_penalty`
  - define each on same eligible candidate pool, same `feasible_selection_target_h`, same one-per-journey rule, same preferred station load, same penalty parameter, and same deterministic event key tie-break where applicable
  - define `constrained_greedy` as comparable marginal-objective heuristic:
    1. remove candidates from already-selected journeys in horizon
    2. for each remaining candidate, compute `delta_u_i`, increase in station excess created by selecting that candidate next
    3. compute:

       ```text
       marginal_score_i = predicted_severe_delay_probability_i - lambda * delta_u_i
       ```

    4. select candidate with highest `marginal_score_i`
    5. break ties by `predicted_severe_delay_probability desc, stop_event_key asc`
    6. repeat until `feasible_selection_target_h` is reached
- alternatives considered:
  - compare only random, ML-first, and Gurobi
  - compare weighted ranking without justified weights
  - use lexicographic station-avoidance greedy that does not optimize same trade-off as Gurobi
- impact:
  - policy comparisons can better separate predictive ranking, simple rule application, and joint optimization value
  - differences between constrained greedy and Gurobi are more plausibly attributable to optimizer search quality rather than different objective definitions

### Decision: Add fixed capacity scenario bundle for action-oriented trade-off analysis

- context: project needs operator and recruiter value, not one frozen metric at one capacity; strongest bounded action story is how outcomes change when review capacity changes
- choice:
  - compute policy comparisons for fixed capacities `{1, 3, 5, 10}`
  - keep `capacity_per_hour = 3` as canonical frozen-policy and primary output capacity for main action queue
  - use same frozen station-load and penalty parameters across all scenario capacities in final evaluation
  - record scenario diagnostics for each capacity:
    - `binding_horizon_count`
    - `binding_horizon_rate`
    - `candidate_shortage_horizon_count`
    - `candidate_shortage_horizon_rate`
    - `median_feasible_selection_target`
  - treat capacity `1` as explicit invariant check because station concentration cannot occur there when `preferred_station_load_per_station_hour >= 1`
- alternatives considered:
  - single-capacity evaluation only
  - unconstrained wide parameter grid over many capacities
  - full stochastic scenario tree or rolling-horizon redesign
- impact:
  - downstream dashboard can answer `what if capacity changes?` directly
  - weak or non-binding capacity scenarios become measurable rather than assumed useful
  - BigQuery migration remains safely deferred until local decision story is useful

### Decision: Keep dashboard implementation downstream, but update one real handoff manifest here

- context: user pain is that dashboard does not yet tell people what ML does, what Gurobi does, or what action follows; optimization layer should hand off right fields and metrics, but not own Power BI page build
- choice:
  - this thread owns output metrics and policy semantics plus one downstream handoff manifest update
  - downstream wording should frame:
    - ML as risk scoring
    - Gurobi as constrained selection
    - dashboard as action and trade-off explanation
  - this thread updates `data/scoped/power_bi/dashboard_mvp_manifest.json` so downstream build reads current optimization semantics from real handoff surface
  - this thread does not modify PBIP files or visual layout
- alternatives considered:
  - redesign optimization and Power BI artifact in one thread
  - keep current opaque output names and push all interpretation downstream later
- impact:
  - optimization output contract becomes useful for later dashboard rewrite
  - report-build lane stays bounded and implementation-focused

## Output Contracts

### Search configuration contract

`configs/optimization/optimization_policy_search_config.json` must include at minimum:

- `optimization_policy_name`
- `optimization_policy_version`
- `canonical_tuning_capacity_per_hour`
- `scenario_capacities`
- `preferred_station_load_per_station_hour_candidates`
- `diagnostic_station_excess_penalty_lambda`
- `eligible_frozen_station_excess_penalty_lambdas`
- `winner_selection_rule`
- `random_seed`
- `development_allowed_solver_statuses`
- `final_allowed_solver_statuses`

Rules:

- this file is canonical human-owned runtime config for this thread
- `scenario_capacities` must be exactly `[1, 3, 5, 10]`
- `diagnostic_station_excess_penalty_lambda` must be `0.00`
- `eligible_frozen_station_excess_penalty_lambdas` must contain only positive values
- `development_allowed_solver_statuses` must be exactly `['OPTIMAL', 'TIME_LIMIT_WITH_INCUMBENT']`
- `final_allowed_solver_statuses` must be exactly `['OPTIMAL', 'TIME_LIMIT_WITH_INCUMBENT']`
- `TIME_LIMIT_WITH_INCUMBENT` means solver hit time limit but returned feasible incumbent and complete selected set

### Frozen policy contract

`data/scoped/optimization/frozen_policy.json` must include at minimum:

- `optimization_policy_name`
- `optimization_policy_version`
- `execution_modes`
- `solver_name`
- `solver_version`
- `canonical_probability_field`
- `threshold_source`
- `selected_threshold`
- `minimum_candidate_probability`
- `scoring_model_name`
- `scoring_model_version`
- `capacity_scenario`
- `capacity_per_hour`
- `preferred_station_load_per_station_hour`
- `diagnostic_station_excess_penalty_lambda`
- `eligible_frozen_station_excess_penalty_lambdas`
- `frozen_station_excess_penalty_lambda`
- `feasible_selection_rule`
- `constraint_set`
- `baseline_policies`
- `tie_break_rule`
- `scenario_capacities`
- `metric_definitions`
- `frozen_at`

Rules:

- `optimization_policy_name` must identify Gurobi policy explicitly
- `baseline_policies` must be exactly `random`, `ml_first`, `constrained_greedy`, `gurobi_soft_station_penalty`
- `scenario_capacities` must be exactly `[1, 3, 5, 10]`
- `minimum_candidate_probability` must equal `selected_threshold` in this thread
- `diagnostic_station_excess_penalty_lambda` must be `0.00`
- `frozen_station_excess_penalty_lambda` must be one of positive eligible frozen lambdas and must be `> 0`
- service weighting must remain explicit as uniform or absent in this thread; no hidden business weight lookup is allowed
- generated frozen policy must not duplicate search grid candidate arrays except positive eligible lambda list and scenario capacities needed for provenance

### Primary event decision contract

`data/scoped/optimization/<mode>/event_decision.parquet` remains one row per scored stop event for frozen `gurobi_soft_station_penalty` at canonical capacity `3` and must include exactly these minimum fields:

- `optimization_run_id`
- `execution_mode`
- `policy_name`
- `capacity_scenario`
- `capacity_per_hour`
- `feasible_selection_target`
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
- `predicted_is_departure_severe_delay`
- `actual_is_departure_severe_delay`
- `prediction_split`
- `is_eligible_candidate`
- `selected_for_review`
- `candidate_priority_rank`
- `selection_rank`
- `priority_score`
- `objective_contribution`
- `eligibility_reason`
- `solver_status`
- `scoring_model_name`
- `scoring_model_version`
- `optimization_policy_name`
- `optimization_policy_version`
- `selected_threshold`
- `optimized_at`

Rules:

- row grain stays one scored stop event
- `stop_event_key` stays unique
- `policy_name` must be exactly `gurobi_soft_station_penalty`
- `capacity_per_hour` must be exactly `3`
- `priority_score` must equal probability term actually optimized in this thread because service weights are uniform
- event-level output must not be used as source of truth for station-concentration totals or penalty attribution; those diagnostics live in horizon-level and comparison artifacts

### Primary horizon summary contract

`data/scoped/optimization/<mode>/horizon_summary.parquet` remains one row per `calendar_date + hour_of_day` horizon for frozen `gurobi_soft_station_penalty` at canonical capacity `3` and must include exactly these minimum fields:

- `optimization_run_id`
- `execution_mode`
- `policy_name`
- `calendar_date`
- `hour_of_day`
- `horizon_id`
- `capacity_scenario`
- `capacity_per_hour`
- `feasible_selection_target`
- `candidate_count`
- `eligible_candidate_count`
- `selected_event_count`
- `candidate_shortage_count`
- `unused_capacity`
- `selected_probability_score_sum`
- `actual_severe_selected_count`
- `actual_severe_candidate_count`
- `candidate_prevalence`
- `precision_at_capacity`
- `severe_delay_coverage`
- `lift_over_candidate_prevalence`
- `distinct_selected_stations`
- `max_selected_same_station_in_horizon`
- `station_concentration_excess_total`
- `penalty_active_in_horizon`
- `solver_status`
- `scoring_model_name`
- `scoring_model_version`
- `optimization_policy_name`
- `optimization_policy_version`
- `optimized_at`

Rules:

- `selected_event_count` must equal `feasible_selection_target` for every horizon
- `candidate_shortage_count = capacity_per_hour - feasible_selection_target`
- `unused_capacity` must equal `candidate_shortage_count` and must never represent policy-driven under-filling
- `station_concentration_excess_total` must be computed from selected set after optimization
- `policy_name` must be exactly `gurobi_soft_station_penalty`
- `capacity_per_hour` must be exactly `3`

### Horizon policy metrics contract

`data/scoped/optimization/<mode>/horizon_policy_metrics.parquet` must contain one row per:

- `policy_name`
- `capacity_per_hour`
- `horizon_id`

Required fields:

- `execution_mode`
- `policy_name`
- `capacity_scenario`
- `capacity_per_hour`
- `calendar_date`
- `hour_of_day`
- `horizon_id`
- `feasible_selection_target`
- `candidate_shortage_count`
- `selected_event_count`
- `selected_severe_event_count`
- `precision_at_capacity`
- `severe_delay_coverage`
- `distinct_selected_stations`
- `max_selected_same_station_in_horizon`
- `station_concentration_excess_total`
- `penalty_active_in_horizon`
- `selected_stop_event_key_hash`

Rules:

- every evaluated policy and capacity must produce one row per evaluated horizon
- `selected_stop_event_key_hash` must be deterministic and derived from selected set in that horizon so pairwise comparison metrics can be reproduced

### Policy comparison contract

`data/scoped/optimization/<mode>/policy_comparison.parquet` must contain one row per:

- `policy_name`
- `capacity_per_hour`

Required fields:

- `execution_mode`
- `policy_name`
- `capacity_scenario`
- `capacity_per_hour`
- `selected_event_count`
- `selected_severe_event_count`
- `precision_at_capacity`
- `severe_delay_coverage`
- `lift_vs_random`
- `expected_risk_score_captured`
- `distinct_stations_covered`
- `max_selected_same_station_in_horizon`
- `station_concentration_excess_total`
- `unused_capacity_total`
- `binding_horizon_count`
- `binding_horizon_rate`
- `candidate_shortage_horizon_count`
- `candidate_shortage_horizon_rate`
- `median_feasible_selection_target`
- `preferred_station_load_per_station_hour`
- `frozen_station_excess_penalty_lambda`

Rules:

- all policies must be evaluated on same candidate pool per execution mode and capacity
- `lift_vs_random` must use random policy at same `execution_mode` and `capacity_per_hour`
- `policy_name = 'random'` must use deterministic seeded sampling so repeated runs are identical and row-order invariant
- `selected_event_count` must be sum of `selected_event_count` across horizons for that policy and capacity
- `selected_severe_event_count` must be sum of `selected_severe_event_count` across horizons for that policy and capacity
- `precision_at_capacity = selected_severe_event_count / selected_event_count`, or `null` when `selected_event_count = 0`
- `severe_delay_coverage = selected_severe_event_count / total_actual_severe_candidate_count_for_same_mode`, or `null` when denominator is `0`
- `lift_vs_random = precision_at_capacity / random_precision_at_same_mode_and_capacity`, or `null` when random precision denominator is `0` or `null`
- `expected_risk_score_captured` must be sum of selected `predicted_severe_delay_probability`
- `distinct_stations_covered` must count distinct stations across all selected events for that policy and capacity
- `max_selected_same_station_in_horizon` must be maximum horizon-level `max_selected_same_station_in_horizon` for that policy and capacity
- `station_concentration_excess_total` must be sum of horizon-level `station_concentration_excess_total`
- `unused_capacity_total` must be sum of horizon-level `unused_capacity`
- `binding_horizon_count` must count horizons where `feasible_selection_target = capacity_per_hour`
- `binding_horizon_rate = binding_horizon_count / horizon_count`
- `candidate_shortage_horizon_count` must count horizons where `candidate_shortage_count > 0`
- `candidate_shortage_horizon_rate = candidate_shortage_horizon_count / horizon_count`
- `median_feasible_selection_target` must be median of horizon-level `feasible_selection_target`

### Development opportunity diagnostics contract

`data/scoped/optimization/development/opportunity_diagnostics.parquet` must contain one row per validation horizon with at minimum:

- `calendar_date`
- `hour_of_day`
- `horizon_id`
- `capacity_per_hour`
- `eligible_event_count`
- `distinct_eligible_journey_count`
- `distinct_eligible_station_count`
- `max_candidate_count_at_one_station`
- `feasible_selection_target`
- `station_excess_could_activate`
- `capacity_binds`

Rules:

- this artifact exists only for `development`
- it is descriptive evidence for whether optimization can differ meaningfully from ranking-only selection

### Development tuning search results contract

`data/scoped/optimization/development/tuning_search_results.parquet` must contain one row per tried parameter pair at canonical tuning capacity `3` with at minimum:

- `preferred_station_load_per_station_hour`
- `station_excess_penalty_lambda`
- `is_diagnostic_zero_penalty`
- `solver_status`
- `selected_severe_event_count`
- `total_actual_severe_candidate_count`
- `severe_delay_coverage`
- `station_concentration_excess_total`
- `distinct_stations_covered`
- `matching_horizon_count_vs_zero_penalty`
- `differing_horizon_count_vs_zero_penalty`

Rules:

- aggregated metrics must be computed over all validation horizons at canonical tuning capacity `3`
- `selected_severe_event_count` must be sum across horizons
- `total_actual_severe_candidate_count` must be count of actual severe eligible candidates across same validation horizons
- `severe_delay_coverage = selected_severe_event_count / total_actual_severe_candidate_count`, or `null` when denominator is `0`
- `station_concentration_excess_total` must be sum across horizons
- `distinct_stations_covered` must count distinct selected stations across all validation horizons for that parameter pair

### Evaluation summary contract

`data/scoped/optimization/<mode>/evaluation.json` must summarize at minimum:

- canonical frozen policy identity and parameters
- development tuning winner when `mode = development`
- path reference to `horizon_policy_metrics.parquet`
- path reference to `policy_comparison.parquet`
- path reference to `development/opportunity_diagnostics.parquet` when `mode = development`
- path reference to `development/tuning_search_results.parquet` when `mode = development`
- canonical-capacity (`3`) pairwise diagnostics for:
  - `gurobi_soft_station_penalty` vs `ml_first`
  - `gurobi_soft_station_penalty` vs `constrained_greedy`
- for each required pairwise comparison:
  - `matching_horizon_count`
  - `differing_horizon_count`
  - `selected_set_match_rate`
  - `mean_selected_set_jaccard`
  - `selected_event_disagreement_count`
  - `penalty_active_horizon_count`

Rules:

- `selected_set_match` against deterministic ranking is no longer primary success proof
- evaluation must record comparison values, not only yes/no claims

## Acceptance Criteria

- existing optimization redesign stays event-level and preserves current split discipline and current join keys
- frozen policy records preferred station load, positive frozen station excess penalty, baseline policy set, and fixed capacity scenario bundle
- `lambda = 0.00` is retained only as diagnostic benchmark and cannot become frozen final Gurobi policy
- Gurobi objective is no longer mathematically equivalent to unconstrained ML-first ranking under same candidate pool
- service-priority weighting is either absent or explicitly uniform in this thread
- hard constraints remain limited to exact feasible selection count, eligibility, one-per-journey-per-horizon, and binary selection
- policy-driven under-filling is impossible; any unused capacity is candidate shortage only
- constrained greedy baseline exists as distinct evaluated policy and uses same marginal objective inputs as Gurobi
- policy comparisons are produced for random, ML-first, constrained greedy, and Gurobi at capacities `1`, `3`, `5`, and `10`
- horizon-level policy metrics exist for every evaluated policy and capacity
- primary canonical output artifacts for frozen Gurobi at capacity `3` remain joinable to downstream Power BI work
- policy comparison artifact reports both predictive metrics and operational metrics, including binding and shortage diagnostics
- development evidence artifacts exist for opportunity diagnostics and tuning search results
- evaluation artifact records frozen-policy parameters and horizon-level pairwise comparison diagnostics at canonical capacity
- dashboard handoff manifest is updated so downstream wording is explicit that ML scores risk, Gurobi allocates limited review attention, and dashboard explains actions and trade-offs

## Non-Goals

- retrain or replace current ML baseline model
- add service-priority weighting without justified business weighting source
- add corridor minimums, network-flow constraints, or rolling-horizon live dispatch logic
- model intervention cost or intentionally unused capacity in this thread
- modify PBIP visuals, page layout, or semantic model directly
- migrate optimization or dashboard pipeline to BigQuery in this thread

## Risks and Mitigations

- risk: penalty weight may be too small to change selections materially
  - mitigation: evaluate bounded validation grid and record identical-versus-different policy outcomes explicitly

- risk: hard-to-explain business weights could reintroduce ranking-only logic under new name
  - mitigation: defer service weights entirely until there is justified business weighting source

- risk: constrained greedy may perform similarly to Gurobi, weakening optimization story
  - mitigation: treat that as honest evidence and use it to decide whether richer constraints are needed before BigQuery

- risk: random baseline may vary across runs and make lift unstable
  - mitigation: fix random seed and deterministic tie-break behavior and validate row-order invariance

- risk: high capacity scenarios may rarely bind and add little insight
  - mitigation: report binding and shortage diagnostics for every frozen capacity scenario

- risk: dashboard could overclaim operational benefit from small metric differences
  - mitigation: preserve descriptive wording and separate predictive metrics from operational trade-off metrics in output contracts

## Invariants

- optimization redesign must consume validated ML scored outputs as primary source
- development tuning must use validation rows only
- final evaluation must use test rows only and frozen policy only
- one `stop_event_key` must map to at most one row in canonical primary decision output
- selected row count per horizon must equal `feasible_selection_target` and must never exceed configured `capacity_per_hour`
- candidate shortage is only allowed source of `unused_capacity`
- no more than one candidate from same `journey_id` may be selected within same horizon
- random, ML-first, constrained greedy, and Gurobi must compare on same candidate pools for each mode and capacity
- constrained greedy and Gurobi must use same probability field, preferred station load, penalty parameter, feasible target rule, and hard constraints
- frozen final Gurobi policy must use `frozen_station_excess_penalty_lambda > 0`
- service weights must not silently influence this thread
- station concentration diagnostics must come from selected-set-derived horizon or comparison artifacts, not summed event-row penalty fields
- downstream outputs must remain descriptive only and must not claim avoided-delay or intervention-effect causality

## Validation Plan

- proof target: current redesign owns real optimization problem rather than pure ranking
  - method: inspection
  - evidence: implementation objective contains station-excess penalty term and output contracts record selected-set-derived station concentration metrics

- proof target: development tuning stays separated from held-out final evaluation
  - method: comparison
  - evidence: development artifacts contain only `prediction_split = 'validation'`; final artifacts contain only `prediction_split = 'test'` and final mode rejects policy overrides

- proof target: exact feasible selection count is enforced
  - method: run
  - evidence: every horizon in canonical `horizon_summary.parquet` satisfies `selected_event_count = feasible_selection_target` and `unused_capacity = candidate_shortage_count`

- proof target: `lambda = 0.00` remains diagnostic only
  - method: inspection and run
  - evidence: frozen policy records `diagnostic_station_excess_penalty_lambda = 0.00`, `frozen_station_excess_penalty_lambda > 0`, and development output still reports comparison against zero-penalty benchmark

- proof target: constrained greedy baseline exists and uses same marginal objective inputs as Gurobi
  - method: inspection and run
  - evidence: implementation computes `marginal_score = predicted_severe_delay_probability - lambda * delta_u` for constrained greedy and `policy_comparison.parquet` contains rows for `constrained_greedy` and `gurobi_soft_station_penalty` at each required capacity

- proof target: random baseline is reproducible and row-order invariant
  - method: run and comparison
  - evidence: repeated runs with reordered input rows produce identical random-policy metrics under fixed seed

- proof target: canonical frozen policy parameters are reproducible
  - method: comparison
  - evidence: repeated development runs with same inputs select same `(preferred_station_load_per_station_hour, frozen_station_excess_penalty_lambda)` winner and write same frozen policy contents except timestamp

- proof target: primary event output preserves row grain and joinability
  - method: comparison
  - evidence: one row per `stop_event_key` remains in canonical `event_decision.parquet`, and required join keys still match downstream semantic export requirements

- proof target: capacity-one invariance holds
  - method: run and comparison
  - evidence: when `capacity_per_hour = 1` and `preferred_station_load_per_station_hour >= 1`, Gurobi and ML-first produce identical horizon selections apart from deterministic tie handling

- proof target: scenario bundle is complete
  - method: inspection and run
  - evidence: `policy_comparison.parquet` and `horizon_policy_metrics.parquet` contain all four policies for capacities `1`, `3`, `5`, and `10`

- proof target: predictive and operational metrics are both present
  - method: inspection
  - evidence: `policy_comparison.parquet` includes precision, coverage, lift, binding, shortage, and concentration fields with formulas owned by this spec

- proof target: horizon-level pairwise diagnostics are visible
  - method: inspection and comparison
  - evidence: `evaluation.json` reports `matching_horizon_count`, `differing_horizon_count`, `selected_set_match_rate`, `mean_selected_set_jaccard`, `selected_event_disagreement_count`, and `penalty_active_horizon_count` for required policy pairs

- proof target: metric zero-denominator behavior is explicit
  - method: run and comparison
  - evidence: zero-selection or zero-severe cases return documented `null` metric values rather than silently coercing to zero

- proof target: development evidence artifacts are durable and reproducible
  - method: inspection and run
  - evidence: `development/opportunity_diagnostics.parquet` and `development/tuning_search_results.parquet` exist with documented fields and stable rerun outputs except timestamps

- proof target: dashboard handoff uses real downstream contract surface
  - method: inspection
  - evidence: `data/scoped/power_bi/dashboard_mvp_manifest.json` references current optimization semantics and canonical artifact meanings

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
