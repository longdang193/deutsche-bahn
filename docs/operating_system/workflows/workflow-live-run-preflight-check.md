---
name: workflow-live-run-preflight-check
description: Run the live run preflight check workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-planning-dispatch
- skill-executing-plans
tags:
- workflow
- execution
- change
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Live Run Preflight Check Workflow

## Goal

Validate live-run prerequisites before execution so evidence can be captured and
results are trustworthy.

## Execution Flow

1. Validate required artifacts exist for selected scenario.
2. Validate observability is enabled for required telemetry surfaces.
3. Validate traceability IDs are present/resolvable.
4. Validate environment and configuration match intended run target.
5. Confirm evidence capture paths for outputs and intermediate artifacts.
6. If session touched Python `@meta` headers, validate ownership classification and capability linkage against upstream contracts.
7. Produce pass/fail readiness decision with minimal unblock actions.

## Decision Gates

1. Artifact gate:
   - fail preflight if required artifacts are missing.
2. Observability gate:
   - fail preflight if required logs/traces/metrics cannot be captured.
3. Traceability gate:
   - fail preflight if run evidence cannot be linked to scope.
4. Environment gate:
   - fail preflight if environment is invalid for scenario intent.
5. Metadata linkage gate (conditional on Python metadata touch):
   - fail preflight if governed Python files omit `@meta.ownership`.
   - fail preflight if `ownership: feature` omits `@meta.capabilities`.
   - fail preflight if `@meta.capabilities` values are not grounded in upstream feature capability IDs.

## Exit Criteria

- Preflight pass with ready evidence paths, or
- Preflight fail with explicit minimal prerequisites to unblock.
