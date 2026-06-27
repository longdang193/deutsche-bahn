# Deutsche Bahn Decision Dashboard Project Architecture

## Goal

Build end-to-end decision system from historical Deutsche Bahn operational data to prediction, candidate generation, optimization, and Power BI reporting.

## Revised Logical Architecture

```text
Historical Deutsche Bahn dataset
-> Scope and extraction
-> Raw / Bronze
-> Clean / Silver operational model
-> Feature / Gold tables
-> ML prediction
-> Candidate generation
-> Gurobi optimization
-> Power BI serving tables
-> Power BI decision dashboard
```

## Layer 1: Historical Data Source

Primary source:

- `deutsche-bahn-data` processed parquet data derived from Deutsche Bahn APIs

Main business content:

- station metadata
- planned arrivals and departures
- changed arrivals and departures
- delay minutes
- cancellations
- train identifiers
- service dates and timestamps

## Layer 2: Scope And Extraction

Purpose:

- cut provider dataset to project-sized subset before landing Bronze
- keep extraction reproducible
- support DuckDB-first development

Recommended scope dimensions:

- selected months
- selected stations or hubs
- selected train types
- required columns only

Recommended artifact:

- `scope.yml`

Recommended manifest fields:

- `source_file`
- `source_version`
- `selected_month`
- `selected_stations`
- `selected_train_types`
- `extraction_timestamp`
- `extraction_query_version`
- `row_count`

Rule:

- preserve selected source records unchanged after scope cut

## Layer 3: Raw / Bronze

Purpose:

- keep scoped source records unchanged
- preserve replayability
- support reprocessing

Recommended objects:

- `bronze.raw_station_reference`
- `bronze.raw_stop_events`
- `bronze.raw_ingestion_manifest`

Recommended storage rules:

- partition by `service_date`
- keep source filename and ingestion timestamp
- no business logic here

## Layer 4: Clean / Silver Operational Model

Purpose:

- standardize schema
- enforce types
- remove duplicates
- create stable business keys

Core transformations:

- parse timestamps into `Europe/Berlin`
- normalize station identifiers
- normalize train type / line naming
- deduplicate repeated stop snapshots
- compute planned vs actual event timestamps

Core logical outputs:

- `fact_stop_event`
- `dim_station`
- `dim_train_service`
- `dim_date`
- `dim_hour`

Example physical names:

- `silver.fact_stop_event`
- `silver.dim_station`

## Layer 5: Feature / Gold Tables

Purpose:

- separate ML, optimization, and Power BI serving concerns

Feature groups:

- delay features
- congestion features
- propagation features
- station baseline features
- train service baseline features
- calendar features

Main outputs:

- `gold.feature_stop_event`
- `gold.fact_station_hour`
- `gold.fact_intervention_candidate`

Rule:

- do not use one large table for ML, optimization, and Power BI together

## Layer 6: ML Prediction

Purpose:

- estimate disruption risk before actions are generated

Recommended MVP model:

1. `severe_departure_delay_15plus`

Model input examples:

- current delay
- station
- train type
- hour of day
- weekday
- rolling station congestion
- station historical baseline

Recommended output:

- `fact_ml_prediction`

Required model metadata:

- `model_version`
- `feature_version`
- `training_period_start`
- `training_period_end`
- `evaluation_metrics`
- `prediction_timestamp`

## Layer 7: Candidate Generation

Purpose:

- convert predictions into feasible business actions before optimization

Flow:

```text
ML predicts risk
-> business rules create feasible actions
-> Gurobi chooses among those actions
```

Recommended MVP action family:

- `connection_holding`

Recommended candidate actions:

- `depart_normally`
- `hold_2_min`
- `hold_5_min`

Rule:

- Gurobi should not consume raw predictions directly

## Layer 8: Gurobi Optimization

Purpose:

- choose best feasible action per decision context under constraints

Recommended MVP optimization problem:

- select best connection-hold alternative per outgoing train

MVP constraints:

- one action per outgoing train
- maximum total held trains
- maximum total holding minutes
- maximum additional downstream delay
- connection feasibility

Objective:

- maximize expected saved delay or connection value
- minimize downstream delay penalty
- stay within holding limits

Output:

- `fact_optimization_result`

## Layer 9: Power BI Serving Tables

Purpose:

- expose curated serving facts and dimensions only

Recommended serving tables:

- `dim_station`
- `dim_train_service`
- `dim_date`
- `dim_hour`
- `fact_station_hour`
- `fact_ml_prediction`
- `fact_intervention_candidate`
- `fact_optimization_result`

Rule:

- do not load complete stop-event fact into Power BI initially

Use detailed stop events only for:

- drill-through
- validation
- scoped detailed extracts

## Layer 10: Power BI Dashboard

Recommended pages:

1. Network Health
2. Risk Forecast
3. Connection Hold Optimizer
4. What-If Analysis
5. Later: Policy Comparison

## Two Physical Implementations

### Phase 1: Local Prototype

```text
Monthly Parquet file
-> DuckDB
   -> bronze
   -> silver
   -> gold
-> Python ML
-> Local Gurobi
-> DuckDB result tables
-> Power BI Import
```

Purpose:

- develop cheaply
- debug transformations
- validate features
- test ML target
- validate Gurobi formulation
- build first dashboard story

### Phase 2: Cloud Implementation

```text
Selected monthly Parquet files
-> Google Cloud Storage
-> BigQuery
   -> bronze
   -> silver
   -> gold
-> BigQuery ML
-> Cloud Run + Gurobi
-> BigQuery serving tables
-> Power BI
```

Purpose:

- demonstrate scalable data engineering
- process more stations and months
- automate model scoring
- run optimization as cloud job
- serve stable Power BI tables

## DuckDB To BigQuery Validation Gate

Do not scale up immediately after local success.

First run same scoped sample through both engines:

```text
One month
One selected hub
Same columns
Same business rules
-> DuckDB outputs
<-> compare
-> BigQuery outputs
```

Compare:

- row counts
- key uniqueness
- null counts
- delay averages
- severe-delay counts
- cancellation counts
- station-hour aggregates
- ML feature distributions
- candidate counts
- Gurobi objective values

Only expand data after parity is good enough.

## Runtime Modes

### Local Development Runtime

```text
Manual pipeline run
-> rebuild selected sample
-> train model
-> generate candidates
-> run Gurobi
-> refresh Power BI
```

### Cloud Runtime

```text
Scheduled monthly ingestion
-> incremental Silver transformation
-> feature refresh
-> model scoring
-> candidate generation
-> Cloud Run Gurobi job
-> Power BI refresh
```

Rule:

- do not add daily scheduling until historical MVP is stable

## MVP Design Choice

Start with one decision loop:

- severe delay risk prediction
- connection-hold candidate generation
- limited connection-hold optimizer
- Power BI decision cockpit

Do not start with:

- full-network real-time replanning
- many action families
- RL-first implementation

## Target Deliverables

1. Reproducible scoped pipeline
2. Clean analytics schema
3. One risk model
4. One candidate generator
5. One Gurobi optimization model
6. One Power BI dashboard
7. Optional Part II policy comparison extension
