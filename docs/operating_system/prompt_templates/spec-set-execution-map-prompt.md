---
name: spec-set-execution-map-prompt
description: Create an execution map that sequences multiple approved specs.
type: prompt
stage: planning
entry_points:
- approved detailed specs exist and implementation sequencing/waves are needed
prerequisites:
- approved detailed specs identified
next_steps:
- plan-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/workflows/workflow-spec-to-plan-to-execution.md
tags:
- prompt
- execution
distribution_tier: starter_kit
---

# Spec Set To Implementation Execution Map Prompt

## Not For

thread creation or roadmap closeout
Use this when the approved detailed specs already exist and you want a distinct
implementation execution map that decides ordering, waves, and parallel lanes.

```text
Create an implementation execution map for this approved detailed-spec set.

Context:
- workstream or branch in scope:
- threads in scope:
- approved detailed specs in scope:
- known dependencies:
- known shared docs/code surfaces:
- whether the main risk is sequencing, parallelism, or shared-surface coordination:

Please:
1. identify the dependency graph across the spec set
2. define execution waves
3. define safe parallel lanes
4. call out shared-surface coordination risks
5. recommend the bounded implementation-plan breakdown
6. draft the execution map in docs/superpowers/execution_maps/
7. include canonical execution-map metadata, including `artifact_type: execution_map`, `map_type: implementation_execution`, `layer`, `status`, `parent_workstream`, `threads`, and `name` as the preferred identity field
```

Expected output:
- one implementation execution map artifact in `docs/superpowers/execution_maps/`
- dependency graph
- execution waves
- parallel lanes
- recommended plan breakdown
