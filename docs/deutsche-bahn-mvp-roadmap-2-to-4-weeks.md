# Deutsche Bahn MVP Roadmap (2-4 Weeks)

## MVP Objective

Deliver working decision dashboard that:

- uses scoped historical Deutsche Bahn operational data
- predicts short-horizon severe delay risk
- generates feasible connection-hold actions
- selects best hold actions with Gurobi
- presents results in Power BI

## MVP Scope

Include:

- scoped extraction step
- cleaned stop-event model
- station-hour serving table
- one ML model
- one candidate generator
- one optimization model
- one Power BI dashboard

Exclude for MVP:

- full-network real-time replanning
- multi-action optimization
- passenger-level demand modeling
- multi-model stack
- Part II core implementation

## Final MVP Use Case

Question:

- which outgoing train connections should be held for `0`, `2`, or `5` minutes to preserve value under limited holding capacity?

## Week 1: Scoped Data Foundation

### Goals

- define small reproducible project scope
- create Bronze and Silver layers locally in DuckDB
- define stable schema

### Tasks

1. Define `scope.yml` for months, stations, train types, and columns.
2. Extract scoped subset from source parquet.
3. Build `bronze.raw_stop_events`.
4. Build `bronze.raw_ingestion_manifest`.
5. Build `silver.dim_station`.
6. Build `silver.dim_train_service`.
7. Build `silver.dim_date` and `silver.dim_hour`.
8. Build `silver.fact_stop_event`.
9. Validate timestamps, nulls, duplicates, and cancellation flags.

### Outputs

- scoped Bronze dataset
- Silver fact and dimension tables
- ingestion manifest
- data quality notes

### Exit Criteria

- one scoped train-stop fact table ready for analytics
- delay and cancellation metrics match manual spot checks

## Week 2: Features + First ML Model

### Goals

- create prediction-ready features
- train first severe-delay model locally

### Tasks

1. Build `gold.feature_stop_event`.
2. Build `gold.fact_station_hour`.
3. Define label `severe_departure_delay_15plus`.
4. Split train/validation/test by time.
5. Train logistic regression baseline in Python.
6. Evaluate with precision, recall, ROC-AUC, and calibration.
7. Write `gold.fact_ml_prediction`.

### Outputs

- feature tables
- training script or notebook
- scored prediction table
- model evaluation summary

### Exit Criteria

- model predicts severe delay better than naive baseline
- prediction artifact includes model metadata

## Week 3: Candidate Generation + Gurobi + Power BI

### Goals

- convert predictions into feasible connection-hold alternatives
- build first optimization result
- build Power BI MVP

### Tasks

1. Define candidate rules for `depart_normally`, `hold_2_min`, `hold_5_min`.
2. Build `gold.fact_intervention_candidate`.
3. Estimate `expected_saved_minutes` and `expected_downstream_delay_penalty`.
4. Build first Gurobi model with hold-capacity constraints.
5. Save `gold.fact_optimization_result`.
6. Build Power BI model and relationships.
7. Create dashboard pages:
   - Network Health
   - Risk Forecast
   - Connection Hold Optimizer
8. Add what-if parameter for hold budget.

### Outputs

- candidate generation logic
- optimization model
- optimization results table
- Power BI MVP report

### Exit Criteria

- optimizer selects exactly one feasible action per decision context
- dashboard shows risk, recommendation, and expected impact

## Week 4: Parity + Hardening

### Goals

- improve trust
- test migration path to BigQuery
- prepare extension path

### Tasks

1. Run same scoped sample in DuckDB and BigQuery.
2. Compare row counts, keys, nulls, aggregates, prediction distributions, and candidate counts.
3. Improve model only if baseline weak.
4. Backtest optimizer on multiple historical windows.
5. Add explanation fields for dashboard.
6. Document local-to-cloud migration steps.
7. Capture later extension for Part II policy comparison.

### Outputs

- parity check summary
- improved scored dataset
- backtest summary
- demo-ready report

### Exit Criteria

- DuckDB and BigQuery outputs are close enough for same scoped sample
- ML and optimization outputs are reproducible

## 2-Week Compressed Version

If time is tight:

### Week 1

- scoped extraction
- Silver stop-event model
- station-hour table
- severe delay baseline model

### Week 2

- candidate generation
- simple Gurobi hold optimizer
- 3 Power BI pages

Skip for compressed MVP:

- BigQuery parity
- advanced model tuning
- Part II policy comparison

## Recommended Deliverables By End State

### Minimum

1. Scoped dataset
2. Silver schema
3. Severe delay prediction
4. Connection-hold candidate generator
5. Gurobi hold optimizer
6. Power BI dashboard

### Strong Version

1. All minimum deliverables
2. DuckDB to BigQuery parity check
3. What-if optimization page
4. Part II policy comparison plan

## Risks And Mitigations

### Risk: No true passenger transfer data

Mitigation:

- use proxy connection value first

### Risk: Historical data does not contain explicit operator actions

Mitigation:

- frame candidate generation as decision simulation, not historical truth replay

### Risk: Model is predictive but not actionable

Mitigation:

- force prediction output into explicit candidate table with action alternatives

### Risk: Optimization objective feels arbitrary

Mitigation:

- keep first action family narrow and explainable

## Recommended MVP Order

1. Scope first
2. Data quality first
3. One label first
4. One model first
5. One action family first
6. One optimization problem first
7. One dashboard story first

## Final Recommendation

Best 2-4 week MVP:

- scoped DuckDB pipeline
- severe delay risk model
- connection-hold candidate generation
- Gurobi selection of best hold action
- Power BI dashboard

Part II should be added after MVP as policy comparison layer, not as first implementation dependency.
