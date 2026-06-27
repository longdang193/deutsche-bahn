---
name: plan-prompt
description: Turn approved spec or patch context into an execution-ready implementation
  plan.
type: prompt
stage: planning
entry_points:
- approved work item context exists and an execution-ready implementation/patch plan
  is needed
prerequisites:
- approved spec or execution-map context
next_steps:
- execute-prompt.md
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

# Plan Prompt

## Not For

spec discovery or closeout verdicts
Use this when the work item context is already approved and you want an execution-ready
plan, including patching work.

If the workstream is still unclear, use `roadmap-to-workstream-prompt.md`
before this prompt.
If multiple approved detailed specs still need sequencing or parallel-lane
decisions, use `spec-set-execution-map-prompt.md` first.

```text
Turn this approved work item context (or approved spec/patch context) into an execution-ready plan (implementation or patch).

Spec:
- path:
- bounded change thread this plan follows (use the canonical thread identity from `docs/intent/workstreams/threads/`; keep legacy thread-id lookup only when needed to find an existing thread file, or use `none`):
- if `none`, why this is operating_system work:
- implementation execution map path, if this plan is part of a multi-spec execution wave:

Please:
1. review the spec and classify the bounded change
2. make lineage explicit in the plan metadata:
   - use `parent_thread` plus `parent_spec` for change-layer plans
   - use `parent_workstream: none` only when this is true operating_system work
   - do not re-enter derived workstream linkage when `parent_thread` is present
3. write a concrete execution plan in docs/superpowers/plans/
4. include canonical frontmatter fields needed by the schema, including `artifact_type`, `layer`, `status`, and `name` as the preferred identity field for new plans
5. name files to create or modify
6. include verification steps
7. keep the plan small, explicit, and execution-ready
8. if an implementation execution map exists, explain how this plan fits its wave or lane
```

Expected output:
- a plan in `docs/superpowers/plans/`
