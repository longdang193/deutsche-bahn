---
name: spec-set-to-spec-authoring-map-prompt
description: Translate a spec set into an authoring map for detailed-spec creation.
type: prompt
stage: planning
entry_points:
- complete spec set exists and detailed-spec authoring order must be orchestrated
prerequisites:
- spec set inventory exists
next_steps:
- spec-prompt.md
- spec-set-execution-map-prompt.md
related_skills:
- skill-planning-dispatch
required_reads:
- docs/operating_system/prompt_templates/README.md
- docs/operating_system/workflows/workflow-spec-to-plan-to-execution.md
tags:
- prompt
- planning
distribution_tier: starter_kit
---

# Spec Set To Spec-Authoring Map Prompt

## Not For

plan execution or closeout
Use this when the complete spec set is known but the detailed specs have not
all been written yet.

```text
Create a spec-authoring map for this complete spec set.

Context:
- workstream or branch in scope:
- threads in scope:
- complete spec set in scope:
- known dependencies between specs:
- known shared design surfaces:
- whether the main risk is design sequencing, shared-surface design conflicts, or authoring parallelism:

Please:
1. identify which detailed specs should be authored first
2. identify dependencies across detailed-spec authoring
3. define safe parallel authoring lanes
4. call out shared-surface design risks
5. recommend the next detailed-spec authoring sequence
6. draft the spec-authoring map in docs/superpowers/execution_maps/
```

Expected output:
- one spec-authoring map artifact in `docs/superpowers/execution_maps/`
- dependency and sequencing guidance for detailed-spec authoring
- safe parallel authoring lanes
- recommended next detailed-spec sequence
