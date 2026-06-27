---
name: workflow-live-run-execution
description: Run the live run execution workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
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

# Live Run Execution Workflow

## Goal

Execute selected live-run scope and produce complete, traceable run evidence.

## Execution Flow

1. Execute the selected scenario pipeline or bounded stage scope.
2. Capture:
   - stage outputs
   - intermediate artifacts
   - logs/traces/metrics references
3. Record run status and failure/success boundary summary.
4. Route by outcome:
   - success signal -> verification
   - failure signal -> debugging

## Decision Gates

1. Scope gate:
   - execution must stay within selected run scope.
2. Evidence gate:
   - run is invalid if outputs/telemetry references are incomplete.
3. Outcome gate:
   - routing must follow observed run status only.

## Exit Criteria

- Success/failure signal is explicit.
- Evidence package is complete enough for verification or debugging.
