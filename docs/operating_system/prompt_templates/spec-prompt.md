---
name: spec-prompt
description: Author or update a detailed specification aligned to bounded change scope.
type: prompt
stage: planning
entry_points:
- a specific detailed spec must be drafted from an approved bounded work item context
prerequisites:
- bounded thread context known or explicit operating_system justification
next_steps:
- spec-set-execution-map-prompt.md
- plan-prompt.md
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

# Detailed Spec Prompt

## Not For

direct implementation without spec context
Use this when the complete spec set is known, a detailed-spec target is chosen,
and you want the actual design spec.

If the roadmap thread or workstream is still unclear, use
`roadmap-to-workstream-prompt.md` or `workstream-to-spec-prompt.md` first.
If the detailed-spec authoring order is still unclear across a multi-spec set,
use `spec-set-to-spec-authoring-map-prompt.md` first.

```text
Draft a spec for this work item.

Work item:
- problem:
- desired outcome:
- affected area:
- constraints:
- what should stay true:
- bounded change thread this follows (use a valid thread artifact from `docs/intent/workstreams/threads/`; prefer its canonical `name` and keep the legacy `thread_id` only when needed to locate the existing file; use `none` only for true operating_system work):
- if `none`, explain why this should not attach to a product workstream thread:

Please:
1. classify the work as intent, operating_system, workstream, or change
2. identify the owning docs and targets
3. state how this follows the chosen thread via `parent_thread`; if truly operating_system scoped, state why `parent_thread: none` is intentional
4. draft the detailed spec in docs/superpowers/specs/ using the canonical detailed specification template
5. include required frontmatter for the spec, including at minimum:
   - `artifact_type: spec`
   - `layer`
   - `status`
   - `name` as the preferred identity field for new specs
6. include required sections with exact names:
   - `## Goal`
   - `## Key Deliverables`
   - `## Design Decisions`
   - `## Invariants`
   - `## Validation Plan`
   - `## Completion Criteria`
7. ensure completion semantics in `## Completion Criteria` stay aligned with lifecycle rules
8. call out whether the next artifact should be another detailed spec or an implementation execution map
```

Expected output:
- a template-aligned spec in `docs/superpowers/specs/` with required frontmatter and required sections
