# Validation

## Refresh Validation

- Status: `pending`
- Reason: PBIP report artifact has not been authored yet in Power BI Desktop.
- Required app: `C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe`
- Power BI Desktop version observed on this machine: `2.145.1602.0 (25.07)+10647c9fa319b5e39936cdb21328038c371d1fe4`
- Required canonical entry file: `reports/power_bi/historical_evaluation/historical_evaluation.pbip`
- Required root parameter: `SemanticExportRoot`
- Required second-root refresh check: `pending`

## Artifact-Level Validation

### Frozen Input Fingerprint

- Validation timestamp: `2026-06-28T15:29:32.4122657+02:00`
- Report commit: `4f078ed281c97d5d115b1d852aecb0e70dc39354`
- Operating system: `Microsoft Windows NT 10.0.19045.0`
- Fingerprint algorithm: `SHA-256 over exact bytes of 8 source files in lexicographic relative-path order`
- Semantic export fingerprint: `24c05aa02e6ba420311e9e3984f9409d74c6794d087acf22cfdc61b869fe31eb`

| Path | SHA256 |
| --- | --- |
| `data/scoped/power_bi/dashboard_mvp_manifest.json` | `2AF3D7751BEA4C2E6B9AAF88F084B7BAAD59D7AEA1AC84628AE08EA53CEDF260` |
| `data/scoped/power_bi/dim_date_hour.parquet` | `26DBD788F96C6F1AEC82623E18F3C1C08B69EB7B87B6E86BF36EFDB2ADD34BFF` |
| `data/scoped/power_bi/dim_scenario.parquet` | `F1414727D470766F34E65795F42241C93BA2FDD356EE3BBC675A0215BE2526D7` |
| `data/scoped/power_bi/dim_station.parquet` | `A6A7F79A86A6339F93EEAEA93A61C271ECDE2DF29400AF4ED62BAF3F77B65382` |
| `data/scoped/power_bi/dim_train_service.parquet` | `6E328985E240E3B690881E8DA4A900DB7CDB3883A0F27A213877C19F08C49F98` |
| `data/scoped/power_bi/fact_event_decision.parquet` | `3A9F76BB36D91DAE92798C8EDC0CE7836447225A75A54028F2DA95A74BCDE1ED` |
| `data/scoped/power_bi/fact_horizon_summary.parquet` | `6D81DB8FD7AB34A8FB23D0C56F876B3054476B84A9C8F13076FF7CEC6BB5A949` |
| `data/scoped/power_bi/semantic_contract.json` | `6ADD369F71F0902A8D6148A1F1DD82539A930CDCBDCD154D6E794726036123D1` |

### Frozen Lineage Tuple

- `optimization_run_id = final-efd5c4df`
- `execution_mode = final`
- `prediction_split = test`
- `policy_version = 2026-06-28-v1`
- `model_version = 2026-06-28-v1`
- `scenario_key = 2026-06-28-v1`
- `optimized_at = 2026-06-28T10:26:53.766136+00:00`
- `scenario_display_name = Prototype hourly_capacity_3 | threshold 0.40 | policy 2026-06-28-v1`

### Source Completeness Snapshot

| Table | Row count |
| --- | ---: |
| `fact_event_decision` | 743 |
| `fact_horizon_summary` | 137 |
| `dim_date_hour` | 137 |
| `dim_station` | 41 |
| `dim_train_service` | 108 |
| `dim_scenario` | 1 |

### Pending PBIP Checks

| Check name | Expected behavior | Observed behavior | Result |
| --- | --- | --- | --- |
| Canonical `.pbip` exists | Exactly one `historical_evaluation.pbip` exists | Not authored yet | Pending |
| Runtime table count | Exactly 6 authored data tables | No PBIP model yet | Pending |
| Auto date/time disabled | No hidden auto date tables | No PBIP project yet | Pending |
| `SemanticExportRoot` parameter | One portable root parameter drives all parquet imports | No PBIP query layer yet | Pending |
| JSON import exclusion | JSON contracts are not imported as runtime tables | No PBIP model yet | Pending |
| Relationship topology | Active one-to-many single-direction joins on exported keys | No PBIP model yet | Pending |
| Field visibility | Hidden ratios and traceability fields stay hidden | No PBIP model yet | Pending |
| Type and sort rules | Match semantic export contract | No PBIP model yet | Pending |

## Rendered Report Validation

| Check name | Expected behavior | Observed behavior | Result |
| --- | --- | --- | --- |
| Original-root refresh | All 6 parquet tables refresh successfully from `SemanticExportRoot` | No PBIP report yet | Pending |
| Second-root refresh | Changing only `SemanticExportRoot` refreshes successfully | No PBIP report yet | Pending |
| Page count | Exactly 2 visible pages, no hidden tooltip/drillthrough pages | No PBIP report yet | Pending |
| Page 1 slicers | Only `calendar_date`, `hour_of_day`, `scenario_key` | No PBIP report yet | Pending |
| Page 2 slicers | `calendar_date`, `hour_of_day`, `scenario_key`, `station_id`, `train_service_key`, `eligibility_reason`, `selected_for_review` | No PBIP report yet | Pending |
| Slicer sync | Date/hour/scenario sync; station/train/eligibility/selection Page-2 only | No PBIP report yet | Pending |
| Page 1 immunity | Page 1 horizon visuals ignore Page-2-only slicers | No PBIP report yet | Pending |
| Descriptive wording | No causal or avoided-delay claims | No PBIP report yet | Pending |

## Reconciliation Checkpoints

| Checkpoint | Source value | Report value | Difference | Result |
| --- | ---: | ---: | ---: | --- |
| Full-period selected count | Pending from semantic export formula check | Pending | Pending | Pending |
| Full-period precision at capacity | Pending from semantic export formula check | Pending | Pending | Pending |
| One selected date horizon checkpoint | Pending | Pending | Pending | Pending |
| One selected date-hour horizon checkpoint | Pending | Pending | Pending | Pending |
| Full-period event count | 743 | Pending | Pending | Pending |
| One station event count | Pending | Pending | Pending | Pending |
| One train-service selected event count | Pending | Pending | Pending | Pending |
| One selected-vs-not-selected distribution checkpoint | Pending | Pending | Pending | Pending |

## Open Issues

- Blocking: PBIP report artifact has not been authored yet, so refresh, model, page, and interaction validations cannot run.
- Blocking: terminal-only session cannot perform Power BI Desktop UI authoring and save-to-PBIP workflow end-to-end.
- Non-blocking: static PBIP validator script is deferred until first working PBIP artifact exists.
