---
name: workflow-live-run-scenario-planning
description: Run the live run scenario planning workflow procedure.
required_reads:
- docs/operating_system/governance/repo-governance.md
related_skills:
- skill-planning-dispatch
- skill-brainstorming
tags:
- workflow
- planning
- execution
- change
allowed-tools: []
required_outputs:
- docs/superpowers/plans/
distribution_tier: starter_kit
---

# Live Run Scenario Planning Workflow

## Goal

Define reusable live-run scenarios and triggers that are traceable to current
workstream/thread/spec scope.

## Execution Flow

1. Identify target capability path and boundaries.
2. Define scenario set covering normal path, edge path, and high-risk path.
3. Define trigger conditions for when each scenario must run.
4. Map each scenario to:
   - workstream/thread scope
   - related spec(s)
   - expected observable evidence
5. Record scenario outputs needed for downstream preflight and execution.

## Decision Gates

1. Scope gate:
   - reject scenarios not linked to in-scope artifacts.
2. Trigger gate:
   - each scenario must have explicit run trigger.
3. Traceability gate:
   - each scenario must reference spec/workstream/thread linkage.

## Exit Criteria

- Scenario set is explicit and scoped.
- Triggers are defined.
- Traceability links are present.
- Expected evidence outputs are defined for preflight.
